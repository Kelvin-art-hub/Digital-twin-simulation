"""Station class representing a processing station in the assembly line."""

import simpy
import random
import logging
from typing import Optional, List
from config import StationConfig, SimulationConfig
from simulation.part import Part
from simulation.metrics import StationMetrics

logger = logging.getLogger(__name__)


class Station:
    """Represents a single processing station in the assembly line.

    Handles part processing, buffer management, operator resources,
    random breakdowns, and metrics collection.

    Attributes:
        env: SimPy environment
        config: Station configuration
        sim_config: Global simulation configuration
        buffer: SimPy Store representing the input buffer
        operators: SimPy Resource representing available operators
        metrics: StationMetrics object for tracking performance
        next_station: Reference to the next station in the line
        warmup_end_time: Simulation time when warm-up period ends
        is_broken: Flag indicating if station is currently broken
    """

    def __init__(
        self,
        env: simpy.Environment,
        config: StationConfig,
        sim_config: SimulationConfig,
        warmup_end_time: float
    ):
        """Initialize a station.

        Args:
            env: SimPy environment
            config: Station configuration
            sim_config: Global simulation configuration
            warmup_end_time: Time when warm-up period ends
        """
        self.env = env
        self.config = config
        self.sim_config = sim_config
        self.buffer = simpy.Store(env, capacity=config.buffer_size)
        self.operators = simpy.Resource(env, capacity=config.operators)
        self.metrics = StationMetrics(station_name=config.name)
        self.next_station: Optional[Station] = None
        self.warmup_end_time = warmup_end_time
        self.is_broken = False

        # Start the processing loop
        self.env.process(self._process_parts())

        # Start breakdown monitoring
        self.env.process(self._monitor_breakdowns())

        # Start buffer occupancy monitoring
        self.env.process(self._monitor_buffer())

    def _process_parts(self):
        """Main processing loop for the station.

        Continuously retrieves parts from buffer, processes them,
        and forwards to the next station.
        """
        while True:
            # Get a part from the buffer
            part: Part = yield self.buffer.get()
            logger.debug(
                "[%.2f] %s: Part %d retrieved from buffer",
                self.env.now, self.config.name, part.part_id
            )

            # Request an operator
            with self.operators.request() as req:
                yield req

                # Record processing start
                part.record_start(self.config.name, self.env.now)
                logger.debug(
                    "[%.2f] %s: Part %d processing started",
                    self.env.now, self.config.name, part.part_id
                )

                # Calculate processing time with variability
                mean_time = self.config.cycle_time
                std_dev = mean_time * self.sim_config.cycle_time_std_dev_ratio
                process_time = max(0.1, random.gauss(mean_time, std_dev))

                # Wait for processing to complete
                start_time = self.env.now
                yield self.env.timeout(process_time)
                end_time = self.env.now

                # Record processing end
                part.record_exit(self.config.name, end_time)

                # Update metrics if past warm-up
                if start_time >= self.warmup_end_time:
                    actual_busy_time = end_time - start_time
                    self.metrics.total_busy_time += actual_busy_time
                    self.metrics.parts_processed += 1
                    waiting_time = part.waiting_time_at(self.config.name)
                    self.metrics.waiting_times.append(waiting_time)

                logger.debug(
                    "[%.2f] %s: Part %d processing completed (%.2fs)",
                    self.env.now, self.config.name, part.part_id, process_time
                )

            # Forward to next station or mark as complete
            if self.next_station:
                yield self.env.process(self.next_station.receive_part(part))
            else:
                # Last station - mark part as complete
                part.completion_time = self.env.now
                logger.debug(
                    "[%.2f] %s: Part %d completed (lead time: %.2fs)",
                    self.env.now, self.config.name, part.part_id,
                    part.lead_time or 0.0
                )

    def _monitor_breakdowns(self):
        """Monitor and simulate random station breakdowns."""
        while True:
            # Wait for a random interval before checking for breakdown
            yield self.env.timeout(self.config.cycle_time)

            # Check if breakdown occurs
            if random.random() < self.config.breakdown_probability:
                self.is_broken = True
                repair_time = random.uniform(
                    self.sim_config.breakdown_repair_time_min,
                    self.sim_config.breakdown_repair_time_max
                )

                logger.info(
                    "[%.2f] %s: BREAKDOWN occurred, repair time: %.2fs",
                    self.env.now, self.config.name, repair_time
                )

                # Record breakdown if past warm-up
                if self.env.now >= self.warmup_end_time:
                    self.metrics.breakdown_count += 1
                    self.metrics.total_downtime += repair_time

                # Wait for repair
                yield self.env.timeout(repair_time)
                self.is_broken = False

                logger.info(
                    "[%.2f] %s: Repair completed",
                    self.env.now, self.config.name
                )

    def _monitor_buffer(self):
        """Monitor buffer occupancy over time for metrics."""
        while True:
            if self.env.now >= self.warmup_end_time:
                occupancy = len(self.buffer.items)
                self.metrics.buffer_occupancy_samples.append(
                    (self.env.now, occupancy)
                )
            yield self.env.timeout(60.0)  # Sample every minute

    def receive_part(self, part: Part):
        """Receive a part from the previous station.

        Args:
            part: The part to receive

        Yields:
            SimPy event when part is placed in buffer
        """
        part.record_entry(self.config.name, self.env.now)
        logger.debug(
            "[%.2f] %s: Part %d entering buffer (occupancy: %d/%d)",
            self.env.now, self.config.name, part.part_id,
            len(self.buffer.items), self.config.buffer_size
        )
        yield self.buffer.put(part)

    def finalize_metrics(self, simulation_end_time: float):
        """Finalize metrics at the end of simulation.

        Args:
            simulation_end_time: Total simulation time
        """
        # Calculate total available time (post warm-up)
        self.metrics.total_available_time = max(
            0.0,
            (simulation_end_time - self.warmup_end_time) * self.config.operators
        )

        logger.info(
            "%s metrics: utilization=%.2f%%, parts=%d, breakdowns=%d, downtime=%.1fs",
            self.config.name,
            self.metrics.utilization * 100,
            self.metrics.parts_processed,
            self.metrics.breakdown_count,
            self.metrics.total_downtime
        )
