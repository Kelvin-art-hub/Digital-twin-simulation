"""Station class representing a processing station in the assembly line."""

import random
from typing import Any, Callable, Dict, Optional

import simpy

from simulation.part import Part
from simulation.metrics import StationMetrics


class Station:
    """Represents a single processing station in the assembly line."""

    def __init__(
        self,
        env: simpy.Environment,
        name: str,
        cycle_time_mean: float,
        cycle_time_std: float,
        buffer_capacity: int,
        operators: int,
        breakdown_probability: float,
        repair_time_min: float,
        repair_time_max: float,
        warmup_end_time: float,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        self.env = env
        self.name = name
        self.cycle_time_mean = cycle_time_mean
        self.cycle_time_std = cycle_time_std
        self.buffer = simpy.Store(env, capacity=buffer_capacity)
        self.operators = simpy.Resource(env, capacity=operators)
        self.breakdown_probability = breakdown_probability
        self.repair_time_min = repair_time_min
        self.repair_time_max = repair_time_max
        self.warmup_end_time = warmup_end_time
        self.event_callback = event_callback

        self.metrics = StationMetrics(station_name=name)
        self.next_station: Optional[Station] = None
        self.is_broken = False

        self.env.process(self._process_parts())
        self.env.process(self._monitor_breakdowns())
        self.env.process(self._monitor_buffer())

    def _emit_event(self, event_type: str, data: dict) -> None:
        """Emit an event to the callback if provided."""
        if self.event_callback:
            self.event_callback(event_type, {**data, "station": self.name, "time": self.env.now})

    def _process_parts(self):
        while True:
            part: Part = yield self.buffer.get()
            self._emit_event("part_retrieved", {"part_id": part.part_id})

            with self.operators.request() as req:
                yield req
                part.record_start(self.name, self.env.now)
                self._emit_event("processing_start", {"part_id": part.part_id})

                process_time = max(0.1, random.gauss(self.cycle_time_mean, self.cycle_time_std))
                start_time = self.env.now
                yield self.env.timeout(process_time)
                end_time = self.env.now

                part.record_exit(self.name, end_time)

                if start_time >= self.warmup_end_time:
                    self.metrics.total_busy_time += end_time - start_time
                    self.metrics.parts_processed += 1
                    self.metrics.waiting_times.append(part.waiting_time_at(self.name))

                self._emit_event("processing_complete", {"part_id": part.part_id, "duration": process_time})

            if self.next_station:
                yield self.env.process(self.next_station.receive_part(part))
            else:
                part.completion_time = self.env.now
                self._emit_event("part_complete", {"part_id": part.part_id, "lead_time": part.lead_time})

    def _monitor_breakdowns(self):
        while True:
            yield self.env.timeout(self.cycle_time_mean)
            if random.random() < self.breakdown_probability:
                self.is_broken = True
                repair_time = random.uniform(self.repair_time_min, self.repair_time_max)
                self._emit_event("breakdown", {"repair_time": repair_time})

                if self.env.now >= self.warmup_end_time:
                    self.metrics.breakdown_count += 1
                    self.metrics.total_downtime += repair_time

                yield self.env.timeout(repair_time)
                self.is_broken = False
                self._emit_event("repair_complete", {})

    def _monitor_buffer(self):
        while True:
            if self.env.now >= self.warmup_end_time:
                occupancy = len(self.buffer.items)
                self.metrics.buffer_occupancy_samples.append((self.env.now, occupancy))
                self._emit_event("buffer_update", {"occupancy": occupancy, "capacity": self.buffer.capacity})
            yield self.env.timeout(60.0)

    def receive_part(self, part: Part):
        part.record_entry(self.name, self.env.now)
        self._emit_event("part_enter", {"part_id": part.part_id, "buffer_level": len(self.buffer.items)})
        yield self.buffer.put(part)

    def finalize_metrics(self, simulation_end_time: float):
        self.metrics.total_available_time = max(
            0.0, (simulation_end_time - self.warmup_end_time) * self.operators.capacity
        )
