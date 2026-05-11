"""Metrics collection and aggregation for the simulation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class StationMetrics:
    """Metrics for a single station."""

    station_name: str
    total_busy_time: float = 0.0
    total_available_time: float = 0.0
    total_downtime: float = 0.0
    breakdown_count: int = 0
    waiting_times: List[float] = field(default_factory=list)
    buffer_occupancy_samples: List[Tuple[float, int]] = field(default_factory=list)
    parts_processed: int = 0

    @property
    def utilization(self) -> float:
        if self.total_available_time <= 0:
            return 0.0
        return min(1.0, self.total_busy_time / self.total_available_time)

    @property
    def average_waiting_time(self) -> float:
        if not self.waiting_times:
            return 0.0
        return sum(self.waiting_times) / len(self.waiting_times)

    @property
    def average_buffer_occupancy(self) -> float:
        if len(self.buffer_occupancy_samples) < 2:
            return 0.0
        total_weighted = 0.0
        total_time = 0.0
        for i in range(len(self.buffer_occupancy_samples) - 1):
            t0, occ = self.buffer_occupancy_samples[i]
            t1, _ = self.buffer_occupancy_samples[i + 1]
            dt = t1 - t0
            total_weighted += occ * dt
            total_time += dt
        return total_weighted / total_time if total_time > 0 else 0.0


@dataclass
class SimulationMetrics:
    """Aggregated metrics for a complete simulation run."""

    scenario_name: str
    parts_produced: int = 0
    shift_duration_seconds: float = 0.0
    warmup_duration_seconds: float = 0.0
    station_metrics: Dict[str, StationMetrics] = field(default_factory=dict)
    completed_parts_lead_times: List[float] = field(default_factory=list)
    replication_index: int = 0

    @property
    def effective_duration_seconds(self) -> float:
        return self.shift_duration_seconds - self.warmup_duration_seconds

    @property
    def throughput_per_hour(self) -> float:
        hours = self.effective_duration_seconds / 3600.0
        return self.parts_produced / hours if hours > 0 else 0.0

    @property
    def average_lead_time(self) -> float:
        if not self.completed_parts_lead_times:
            return 0.0
        return sum(self.completed_parts_lead_times) / len(self.completed_parts_lead_times)

    @property
    def bottleneck_station(self) -> Optional[str]:
        if not self.station_metrics:
            return None
        return max(self.station_metrics, key=lambda s: self.station_metrics[s].utilization)


@dataclass
class AggregatedMetrics:
    """Metrics averaged across multiple replications."""

    scenario_name: str
    parts_produced: float = 0.0
    throughput_per_hour: float = 0.0
    average_lead_time: float = 0.0
    station_utilizations: Dict[str, float] = field(default_factory=dict)
    station_waiting_times: Dict[str, float] = field(default_factory=dict)
    station_breakdown_counts: Dict[str, float] = field(default_factory=dict)
    station_downtimes: Dict[str, float] = field(default_factory=dict)
    station_buffer_occupancies: Dict[str, float] = field(default_factory=dict)
    bottleneck_station: str = ""
    all_lead_times: List[float] = field(default_factory=list)
    num_replications: int = 0
    # Variance metrics
    throughput_variance: float = 0.0
    lead_time_variance: float = 0.0
    parts_produced_variance: float = 0.0

    def improvement_vs(self, baseline: "AggregatedMetrics") -> Dict[str, float]:
        result = {}
        if baseline.throughput_per_hour > 0:
            result["throughput_improvement"] = (
                (self.throughput_per_hour - baseline.throughput_per_hour)
                / baseline.throughput_per_hour
                * 100.0
            )
        else:
            result["throughput_improvement"] = 0.0
        if baseline.average_lead_time > 0:
            result["lead_time_improvement"] = (
                (baseline.average_lead_time - self.average_lead_time)
                / baseline.average_lead_time
                * 100.0
            )
        else:
            result["lead_time_improvement"] = 0.0
        return result


def aggregate_replications(replications: List[SimulationMetrics]) -> AggregatedMetrics:
    """Aggregate metrics across multiple simulation replications."""
    if not replications:
        raise ValueError("Cannot aggregate empty list of replications")

    scenario_name = replications[0].scenario_name
    n = len(replications)

    throughputs = [r.throughput_per_hour for r in replications]
    lead_times = [r.average_lead_time for r in replications]
    parts = [r.parts_produced for r in replications]

    avg_throughput = sum(throughputs) / n
    avg_lead_time = sum(lead_times) / n
    avg_parts = sum(parts) / n

    # Variance
    tp_var = sum((t - avg_throughput) ** 2 for t in throughputs) / n
    lt_var = sum((t - avg_lead_time) ** 2 for t in lead_times) / n
    p_var = sum((t - avg_parts) ** 2 for t in parts) / n

    station_names = set()
    for r in replications:
        station_names.update(r.station_metrics.keys())

    station_utilizations: Dict[str, float] = {}
    station_waiting_times: Dict[str, float] = {}
    station_breakdown_counts: Dict[str, float] = {}
    station_downtimes: Dict[str, float] = {}
    station_buffer_occupancies: Dict[str, float] = {}

    for sname in station_names:
        utils = [r.station_metrics[sname].utilization for r in replications if sname in r.station_metrics]
        waits = [r.station_metrics[sname].average_waiting_time for r in replications if sname in r.station_metrics]
        bdowns = [r.station_metrics[sname].breakdown_count for r in replications if sname in r.station_metrics]
        dtimes = [r.station_metrics[sname].total_downtime for r in replications if sname in r.station_metrics]
        buffs = [r.station_metrics[sname].average_buffer_occupancy for r in replications if sname in r.station_metrics]

        station_utilizations[sname] = sum(utils) / len(utils) if utils else 0.0
        station_waiting_times[sname] = sum(waits) / len(waits) if waits else 0.0
        station_breakdown_counts[sname] = sum(bdowns) / len(bdowns) if bdowns else 0.0
        station_downtimes[sname] = sum(dtimes) / len(dtimes) if dtimes else 0.0
        station_buffer_occupancies[sname] = sum(buffs) / len(buffs) if buffs else 0.0

    bottlenecks = [r.bottleneck_station for r in replications if r.bottleneck_station]
    bottleneck = max(set(bottlenecks), key=bottlenecks.count) if bottlenecks else ""

    all_lead_times: List[float] = []
    for r in replications:
        all_lead_times.extend(r.completed_parts_lead_times)

    return AggregatedMetrics(
        scenario_name=scenario_name,
        parts_produced=avg_parts,
        throughput_per_hour=avg_throughput,
        average_lead_time=avg_lead_time,
        station_utilizations=station_utilizations,
        station_waiting_times=station_waiting_times,
        station_breakdown_counts=station_breakdown_counts,
        station_downtimes=station_downtimes,
        station_buffer_occupancies=station_buffer_occupancies,
        bottleneck_station=bottleneck,
        all_lead_times=all_lead_times,
        num_replications=n,
        throughput_variance=tp_var,
        lead_time_variance=lt_var,
        parts_produced_variance=p_var,
    )
