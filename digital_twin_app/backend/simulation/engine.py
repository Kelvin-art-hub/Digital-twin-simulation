"""Simulation engine that orchestrates the assembly line simulation."""

import random
from typing import Any, Callable, Dict, List, Optional

import simpy

from simulation.metrics import AggregatedMetrics, SimulationMetrics, aggregate_replications
from simulation.part import Part
from simulation.station import Station


class StationConfig:
    """Configuration for a single station."""

    def __init__(
        self,
        name: str,
        cycle_time_mean: float,
        cycle_time_std: float,
        buffer_capacity: int,
        operators: int,
        breakdown_probability: float = 0.02,
        repair_time_min: float = 30.0,
        repair_time_max: float = 90.0,
    ):
        self.name = name
        self.cycle_time_mean = cycle_time_mean
        self.cycle_time_std = cycle_time_std
        self.buffer_capacity = buffer_capacity
        self.operators = operators
        self.breakdown_probability = breakdown_probability
        self.repair_time_min = repair_time_min
        self.repair_time_max = repair_time_max


class SimulationEngine:
    """Orchestrates the discrete-event simulation of the assembly line."""

    def __init__(
        self,
        scenario_name: str,
        station_configs: List[StationConfig],
        shift_duration_hours: float,
        warmup_period_minutes: float,
        seed: int,
        replication_index: int = 0,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        self.scenario_name = scenario_name
        self.station_configs = station_configs
        self.shift_duration_hours = shift_duration_hours
        self.warmup_period_minutes = warmup_period_minutes
        self.seed = seed
        self.replication_index = replication_index
        self.event_callback = event_callback

        self._env: Optional[simpy.Environment] = None
        self._stations: Dict[str, Station] = {}
        self._all_parts: List[Part] = []
        self._part_counter = 0

    def run(self) -> SimulationMetrics:
        """Execute the simulation and return collected metrics."""
        random.seed(self.seed)

        shift_seconds = self.shift_duration_hours * 3600.0
        warmup_seconds = self.warmup_period_minutes * 60.0

        self._env = simpy.Environment()
        self._stations = {}
        self._all_parts = []
        self._part_counter = 0

        # Create stations
        for cfg in self.station_configs:
            station = Station(
                env=self._env,
                name=cfg.name,
                cycle_time_mean=cfg.cycle_time_mean,
                cycle_time_std=cfg.cycle_time_std,
                buffer_capacity=cfg.buffer_capacity,
                operators=cfg.operators,
                breakdown_probability=cfg.breakdown_probability,
                repair_time_min=cfg.repair_time_min,
                repair_time_max=cfg.repair_time_max,
                warmup_end_time=warmup_seconds,
                event_callback=self.event_callback,
            )
            self._stations[cfg.name] = station

        # Chain stations
        names = [cfg.name for cfg in self.station_configs]
        for i in range(len(names) - 1):
            self._stations[names[i]].next_station = self._stations[names[i + 1]]

        # Start part generation
        self._env.process(self._generate_parts(shift_seconds))

        # Run
        self._env.run(until=shift_seconds)

        # Finalize
        for station in self._stations.values():
            station.finalize_metrics(shift_seconds)

        completed_after_warmup = [
            p for p in self._all_parts
            if p.completion_time is not None and p.completion_time >= warmup_seconds
        ]

        metrics = SimulationMetrics(
            scenario_name=self.scenario_name,
            parts_produced=len(completed_after_warmup),
            shift_duration_seconds=shift_seconds,
            warmup_duration_seconds=warmup_seconds,
            replication_index=self.replication_index,
        )

        for name, station in self._stations.items():
            metrics.station_metrics[name] = station.metrics

        metrics.completed_parts_lead_times = [
            p.lead_time for p in completed_after_warmup if p.lead_time is not None
        ]

        return metrics

    def _generate_parts(self, shift_seconds: float):
        first_cfg = self.station_configs[0]
        first_station = self._stations[first_cfg.name]

        while self._env.now < shift_seconds:
            self._part_counter += 1
            part = Part(part_id=self._part_counter, creation_time=self._env.now)
            self._all_parts.append(part)

            yield self._env.process(first_station.receive_part(part))

            inter_arrival = max(0.1, random.gauss(first_cfg.cycle_time_mean, first_cfg.cycle_time_std))
            yield self._env.timeout(inter_arrival)


def run_scenario_replications(
    scenario_name: str,
    station_configs: List[StationConfig],
    shift_duration_hours: float,
    warmup_period_minutes: float,
    num_replications: int,
    seed_base: int = 42,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
) -> AggregatedMetrics:
    """Run a scenario across multiple replications and return aggregated metrics."""
    replications: List[SimulationMetrics] = []

    for i in range(num_replications):
        seed = seed_base + i * 100
        engine = SimulationEngine(
            scenario_name=scenario_name,
            station_configs=station_configs,
            shift_duration_hours=shift_duration_hours,
            warmup_period_minutes=warmup_period_minutes,
            seed=seed,
            replication_index=i,
            event_callback=event_callback,
        )
        result = engine.run()
        replications.append(result)

        if progress_callback:
            progress_callback(i + 1, num_replications)

    return aggregate_replications(replications)
