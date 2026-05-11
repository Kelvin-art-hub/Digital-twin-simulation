"""Metrics collection and aggregation for the simulation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class StationMetrics:
    """Metrics for a single station.

    Attributes:
        station_name: Name of the station
        total_busy_time: Total time operators were busy processing parts
        total_available_time: Total time the station was available (post warm-up)
        total_downtime: Total time lost to breakdowns
        breakdown_count: Number of breakdowns that occurred
        waiting_times: List of waiting times for each part
        buffer_occupancy_samples: List of (time, occupancy) tuples
        parts_processed: Number of parts processed at this station
    """
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
        """Station utilization as a fraction (0-1).

        Returns:
            Utilization ratio, or 0.0 if no available time recorded
        """
        if self.total_available_time <= 0:
            return 0.0
        return min(1.0, self.total_busy_time / self.total_available_time)

    @property
    def average_waiting_time(self) -> float:
        """Average waiting time in buffer across all parts.

        Returns:
            Average waiting time in seconds, or 0.0 if no parts
        """
        if not self.waiting_times:
            return 0.0
        return sum(self.waiting_times) / len(self.waiting_times)

    @property
    def average_buffer_occupancy(self) -> float:
        """Time-weighted average buffer occupancy.

        Returns:
            Average number of parts in buffer, or 0.0 if no samples
        """
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
        if total_time <= 0:
            return 0.0
        return total_weighted / total_time


@dataclass
class SimulationMetrics:
    """Aggregated metrics for a complete simulation run.

    Attributes:
        scenario_name: Name of the scenario
        parts_produced: Total parts completed after warm-up
        shift_duration_seconds: Effective shift duration in seconds
        warmup_duration_seconds: Warm-up period in seconds
        station_metrics: Dict mapping station name to StationMetrics
        completed_parts_lead_times: Lead times for all completed parts
        replication_index: Which replication this is (0-indexed)
    """
    scenario_name: str
    parts_produced: int = 0
    shift_duration_seconds: float = 0.0
    warmup_duration_seconds: float = 0.0
    station_metrics: Dict[str, StationMetrics] = field(default_factory=dict)
    completed_parts_lead_times: List[float] = field(default_factory=list)
    replication_index: int = 0

    @property
    def effective_duration_seconds(self) -> float:
        """Effective measurement window (shift minus warm-up).

        Returns:
            Duration in seconds
        """
        return self.shift_duration_seconds - self.warmup_duration_seconds

    @property
    def throughput_per_hour(self) -> float:
        """Parts produced per hour during the measurement window.

        Returns:
            Throughput in parts/hour
        """
        hours = self.effective_duration_seconds / 3600.0
        if hours <= 0:
            return 0.0
        return self.parts_produced / hours

    @property
    def average_lead_time(self) -> float:
        """Average end-to-end lead time across all completed parts.

        Returns:
            Average lead time in seconds, or 0.0 if no parts
        """
        if not self.completed_parts_lead_times:
            return 0.0
        return sum(self.completed_parts_lead_times) / len(self.completed_parts_lead_times)

    @property
    def bottleneck_station(self) -> Optional[str]:
        """Identify the bottleneck station by highest utilization.

        Returns:
            Name of the station with highest utilization, or None
        """
        if not self.station_metrics:
            return None
        return max(self.station_metrics, key=lambda s: self.station_metrics[s].utilization)


@dataclass
class AggregatedMetrics:
    """Metrics averaged across multiple replications.

    Attributes:
        scenario_name: Name of the scenario
        parts_produced: Average parts produced per replication
        throughput_per_hour: Average throughput per hour
        average_lead_time: Average end-to-end lead time in seconds
        station_utilizations: Dict mapping station name to average utilization
        station_waiting_times: Dict mapping station name to average waiting time
        station_breakdown_counts: Dict mapping station name to average breakdown count
        station_downtimes: Dict mapping station name to average downtime
        bottleneck_station: Most frequently identified bottleneck
        all_lead_times: All individual part lead times across replications
        num_replications: Number of replications averaged
    """
    scenario_name: str
    parts_produced: float = 0.0
    throughput_per_hour: float = 0.0
    average_lead_time: float = 0.0
    station_utilizations: Dict[str, float] = field(default_factory=dict)
    station_waiting_times: Dict[str, float] = field(default_factory=dict)
    station_breakdown_counts: Dict[str, float] = field(default_factory=dict)
    station_downtimes: Dict[str, float] = field(default_factory=dict)
    bottleneck_station: str = ''
    all_lead_times: List[float] = field(default_factory=list)
    num_replications: int = 0

    def improvement_vs(self, baseline: 'AggregatedMetrics') -> Dict[str, float]:
        """Calculate improvement percentages versus a baseline scenario.

        Args:
            baseline: The baseline AggregatedMetrics to compare against

        Returns:
            Dict with 'throughput_improvement' and 'lead_time_improvement' as percentages
        """
        result = {}
        if baseline.throughput_per_hour > 0:
            result['throughput_improvement'] = (
                (self.throughput_per_hour - baseline.throughput_per_hour)
                / baseline.throughput_per_hour * 100.0
            )
        else:
            result['throughput_improvement'] = 0.0

        if baseline.average_lead_time > 0:
            result['lead_time_improvement'] = (
                (baseline.average_lead_time - self.average_lead_time)
                / baseline.average_lead_time * 100.0
            )
        else:
            result['lead_time_improvement'] = 0.0

        return result


def aggregate_replications(replications: List[SimulationMetrics]) -> AggregatedMetrics:
    """Aggregate metrics across multiple simulation replications.

    Args:
        replications: List of SimulationMetrics from individual runs

    Returns:
        AggregatedMetrics with averaged values
    """
    if not replications:
        raise ValueError("Cannot aggregate empty list of replications")

    scenario_name = replications[0].scenario_name
    n = len(replications)

    avg_parts = sum(r.parts_produced for r in replications) / n
    avg_throughput = sum(r.throughput_per_hour for r in replications) / n
    avg_lead_time = sum(r.average_lead_time for r in replications) / n

    # Collect all station names
    station_names = set()
    for r in replications:
        station_names.update(r.station_metrics.keys())

    station_utilizations: Dict[str, float] = {}
    station_waiting_times: Dict[str, float] = {}
    station_breakdown_counts: Dict[str, float] = {}
    station_downtimes: Dict[str, float] = {}

    for sname in station_names:
        utils = [r.station_metrics[sname].utilization
                 for r in replications if sname in r.station_metrics]
        waits = [r.station_metrics[sname].average_waiting_time
                 for r in replications if sname in r.station_metrics]
        bdowns = [r.station_metrics[sname].breakdown_count
                  for r in replications if sname in r.station_metrics]
        dtimes = [r.station_metrics[sname].total_downtime
                  for r in replications if sname in r.station_metrics]

        station_utilizations[sname] = sum(utils) / len(utils) if utils else 0.0
        station_waiting_times[sname] = sum(waits) / len(waits) if waits else 0.0
        station_breakdown_counts[sname] = sum(bdowns) / len(bdowns) if bdowns else 0.0
        station_downtimes[sname] = sum(dtimes) / len(dtimes) if dtimes else 0.0

    # Bottleneck: most common across replications
    bottlenecks = [r.bottleneck_station for r in replications if r.bottleneck_station]
    bottleneck = max(set(bottlenecks), key=bottlenecks.count) if bottlenecks else ''

    all_lead_times = []
    for r in replications:
        all_lead_times.extend(r.completed_parts_lead_times)

    logger.info(
        "Aggregated %d replications for scenario '%s': "
        "avg_parts=%.1f, avg_throughput=%.2f/hr, avg_lead_time=%.1fs",
        n, scenario_name, avg_parts, avg_throughput, avg_lead_time
    )

    return AggregatedMetrics(
        scenario_name=scenario_name,
        parts_produced=avg_parts,
        throughput_per_hour=avg_throughput,
        average_lead_time=avg_lead_time,
        station_utilizations=station_utilizations,
        station_waiting_times=station_waiting_times,
        station_breakdown_counts=station_breakdown_counts,
        station_downtimes=station_downtimes,
        bottleneck_station=bottleneck,
        all_lead_times=all_lead_times,
        num_replications=n
    )
