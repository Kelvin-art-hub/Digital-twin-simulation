"""Simulation engine that orchestrates the assembly line simulation."""

import simpy
import random
import logging
from typing import Dict, List, Optional
from config import SimulationConfig, StationConfig, STATION_ORDER
from simulation.part import Part
from simulation.station import Station
from simulation.metrics import SimulationMetrics, StationMetrics

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Orchestrates the discrete-event simulation of the assembly line.

    Creates stations, connects them in sequence, generates parts,
    and collects metrics across the simulation run.

    Attributes:
        scenario_name: Name of the scenario being simulated
        station_configs: Dict mapping station name to StationConfig
        sim_config: Global simulation configuration
        seed: Random seed for this replication
        replication_index: Index of this replication
    """

    def __init__(
        self,
        scenario_name: str,
        station_configs: Dict[str, StationConfig],
        sim_config: SimulationConfig,
        seed: int,
        replication_index: int = 0
    ):
        """Initialize the simulation engine.

        Args:
            scenario_name: Name of the scenario
            station_configs: Dict mapping station name to StationConfig
            sim_config: Global simulation configuration
            seed: Random seed for reproducibility
            replication_index: Index of this replication run
        """
        self.scenario_name = scenario_name
        self.station_configs = station_configs
        self.sim_config = sim_config
        self.seed = seed
        self.replication_index = replication_index

        self._env: Optional[simpy.Environment] = None
        self._stations: Dict[str, Station] = {}
        self._completed_parts: List[Part] = []
        self._all_parts: List[Part] = []
        self._part_counter = 0

    def run(self) -> SimulationMetrics:
        """Execute the simulation and return collected metrics.

        Returns:
            SimulationMetrics with all collected data
        """
        random.seed(self.seed)

        shift_seconds = self.sim_config.shift_duration_hours * 3600.0
        warmup_seconds = self.sim_config.warmup_period_minutes * 60.0

        logger.info(
            "Starting simulation: scenario='%s', seed=%d, replication=%d",
            self.scenario_name, self.seed, self.replication_index
        )

        self._env = simpy.Environment()
        self._stations = {}
        self._completed_parts = []
        self._all_parts = []
        self._part_counter = 0

        # Create stations
        for name in STATION_ORDER:
            if name not in self.station_configs:
                raise ValueError(f"Station '{name}' not found in station_configs")
            cfg = self.station_configs[name]
            station = Station(
                env=self._env,
                config=cfg,
                sim_config=self.sim_config,
                warmup_end_time=warmup_seconds
            )
            self._stations[name] = station

        # Chain stations together
        for i in range(len(STATION_ORDER) - 1):
            current_name = STATION_ORDER[i]
            next_name = STATION_ORDER[i + 1]
            self._stations[current_name].next_station = self._stations[next_name]

        # The last station needs a completion callback
        last_station = self._stations[STATION_ORDER[-1]]
        last_station.next_station = None  # Explicitly no next station

        # Start part generation process
        self._env.process(self._generate_parts(shift_seconds, warmup_seconds))

        # Run simulation
        self._env.run(until=shift_seconds)

        # Finalize station metrics
        for station in self._stations.values():
            station.finalize_metrics(shift_seconds)

        # Collect completed parts (only those completed after warm-up)
        completed_after_warmup = [
            p for p in self._all_parts
            if p.completion_time is not None and p.completion_time >= warmup_seconds
        ]

        # Build metrics object
        metrics = SimulationMetrics(
            scenario_name=self.scenario_name,
            parts_produced=len(completed_after_warmup),
            shift_duration_seconds=shift_seconds,
            warmup_duration_seconds=warmup_seconds,
            replication_index=self.replication_index
        )

        for name, station in self._stations.items():
            metrics.station_metrics[name] = station.metrics

        metrics.completed_parts_lead_times = [
            p.lead_time for p in completed_after_warmup
            if p.lead_time is not None
        ]

        logger.info(
            "Simulation complete: scenario='%s', seed=%d, parts_produced=%d, "
            "throughput=%.2f/hr, avg_lead_time=%.1fs",
            self.scenario_name, self.seed, metrics.parts_produced,
            metrics.throughput_per_hour, metrics.average_lead_time
        )

        return metrics

    def _generate_parts(self, shift_seconds: float, warmup_seconds: float):
        """Generate parts and feed them into the first station.

        Parts are generated continuously until the shift ends.
        The feeding station's cycle time governs the inter-arrival rate.

        Args:
            shift_seconds: Total shift duration in seconds
            warmup_seconds: Warm-up period in seconds

        Yields:
            SimPy timeout events
        """
        first_station = self._stations[STATION_ORDER[0]]
        feeding_config = self.station_configs[STATION_ORDER[0]]

        while self._env.now < shift_seconds:
            # Create a new part
            self._part_counter += 1
            part = Part(
                part_id=self._part_counter,
                creation_time=self._env.now
            )
            self._all_parts.append(part)

            logger.debug(
                "[%.2f] Generator: Created Part %d",
                self._env.now, part.part_id
            )

            # Feed into first station buffer (non-blocking if buffer has space)
            # If buffer is full, wait until space is available
            yield self._env.process(first_station.receive_part(part))

            # Inter-arrival time based on feeding station cycle time
            mean_time = feeding_config.cycle_time
            std_dev = mean_time * self.sim_config.cycle_time_std_dev_ratio
            inter_arrival = max(0.1, random.gauss(mean_time, std_dev))
            yield self._env.timeout(inter_arrival)
