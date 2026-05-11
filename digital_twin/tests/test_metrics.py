"""Unit tests for metrics calculation and aggregation."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulation.metrics import (
    StationMetrics,
    SimulationMetrics,
    AggregatedMetrics,
    aggregate_replications
)


# ─── StationMetrics tests ─────────────────────────────────────────────────────

class TestStationMetrics:
    """Tests for StationMetrics calculations."""

    def test_utilization_zero_when_no_available_time(self):
        """Utilization is 0 when no available time is recorded."""
        m = StationMetrics(station_name='S1')
        assert m.utilization == 0.0

    def test_utilization_calculation(self):
        """Utilization is correctly calculated as busy/available."""
        m = StationMetrics(station_name='S1')
        m.total_busy_time = 3600.0
        m.total_available_time = 7200.0
        assert m.utilization == pytest.approx(0.5)

    def test_utilization_capped_at_one(self):
        """Utilization is capped at 1.0 even if busy > available."""
        m = StationMetrics(station_name='S1')
        m.total_busy_time = 8000.0
        m.total_available_time = 7200.0
        assert m.utilization == pytest.approx(1.0)

    def test_average_waiting_time_empty(self):
        """Average waiting time is 0 when no parts recorded."""
        m = StationMetrics(station_name='S1')
        assert m.average_waiting_time == 0.0

    def test_average_waiting_time(self):
        """Average waiting time is correctly calculated."""
        m = StationMetrics(station_name='S1')
        m.waiting_times = [10.0, 20.0, 30.0]
        assert m.average_waiting_time == pytest.approx(20.0)

    def test_average_buffer_occupancy_empty(self):
        """Buffer occupancy is 0 when no samples."""
        m = StationMetrics(station_name='S1')
        assert m.average_buffer_occupancy == 0.0

    def test_average_buffer_occupancy_single_sample(self):
        """Buffer occupancy is 0 with only one sample (no time interval)."""
        m = StationMetrics(station_name='S1')
        m.buffer_occupancy_samples = [(0.0, 3)]
        assert m.average_buffer_occupancy == 0.0

    def test_average_buffer_occupancy_calculation(self):
        """Buffer occupancy is time-weighted average."""
        m = StationMetrics(station_name='S1')
        # 2 parts for 100s, then 4 parts for 100s → average = 3
        m.buffer_occupancy_samples = [(0.0, 2), (100.0, 4), (200.0, 4)]
        assert m.average_buffer_occupancy == pytest.approx(3.0)


# ─── SimulationMetrics tests ──────────────────────────────────────────────────

class TestSimulationMetrics:
    """Tests for SimulationMetrics calculations."""

    def test_effective_duration(self):
        """Effective duration is shift minus warm-up."""
        m = SimulationMetrics(
            scenario_name='Test',
            shift_duration_seconds=28800.0,
            warmup_duration_seconds=1800.0
        )
        assert m.effective_duration_seconds == pytest.approx(27000.0)

    def test_throughput_per_hour(self):
        """Throughput is correctly calculated in parts/hour."""
        m = SimulationMetrics(
            scenario_name='Test',
            parts_produced=100,
            shift_duration_seconds=28800.0,
            warmup_duration_seconds=1800.0
        )
        # 100 parts / 7.5 hours = 13.33 parts/hr
        assert m.throughput_per_hour == pytest.approx(100 / 7.5, rel=1e-3)

    def test_throughput_zero_when_no_duration(self):
        """Throughput is 0 when effective duration is 0."""
        m = SimulationMetrics(
            scenario_name='Test',
            parts_produced=50,
            shift_duration_seconds=1800.0,
            warmup_duration_seconds=1800.0
        )
        assert m.throughput_per_hour == 0.0

    def test_average_lead_time_empty(self):
        """Average lead time is 0 when no parts."""
        m = SimulationMetrics(scenario_name='Test')
        assert m.average_lead_time == 0.0

    def test_average_lead_time(self):
        """Average lead time is correctly calculated."""
        m = SimulationMetrics(scenario_name='Test')
        m.completed_parts_lead_times = [100.0, 200.0, 300.0]
        assert m.average_lead_time == pytest.approx(200.0)

    def test_bottleneck_station_none_when_empty(self):
        """Bottleneck is None when no station metrics."""
        m = SimulationMetrics(scenario_name='Test')
        assert m.bottleneck_station is None

    def test_bottleneck_station_identified(self):
        """Bottleneck is the station with highest utilization."""
        m = SimulationMetrics(scenario_name='Test')
        s1 = StationMetrics(station_name='S1')
        s1.total_busy_time = 1000.0
        s1.total_available_time = 2000.0

        s2 = StationMetrics(station_name='S2')
        s2.total_busy_time = 1800.0
        s2.total_available_time = 2000.0

        m.station_metrics = {'S1': s1, 'S2': s2}
        assert m.bottleneck_station == 'S2'


# ─── AggregatedMetrics tests ──────────────────────────────────────────────────

class TestAggregatedMetrics:
    """Tests for AggregatedMetrics improvement calculations."""

    def test_improvement_vs_baseline_throughput(self):
        """Throughput improvement is correctly calculated."""
        baseline = AggregatedMetrics(
            scenario_name='Base',
            throughput_per_hour=10.0,
            average_lead_time=200.0
        )
        improved = AggregatedMetrics(
            scenario_name='Improved',
            throughput_per_hour=12.0,
            average_lead_time=180.0
        )
        improvements = improved.improvement_vs(baseline)
        assert improvements['throughput_improvement'] == pytest.approx(20.0)

    def test_improvement_vs_baseline_lead_time(self):
        """Lead time improvement is correctly calculated (lower is better)."""
        baseline = AggregatedMetrics(
            scenario_name='Base',
            throughput_per_hour=10.0,
            average_lead_time=200.0
        )
        improved = AggregatedMetrics(
            scenario_name='Improved',
            throughput_per_hour=12.0,
            average_lead_time=150.0
        )
        improvements = improved.improvement_vs(baseline)
        assert improvements['lead_time_improvement'] == pytest.approx(25.0)

    def test_improvement_vs_zero_baseline(self):
        """Improvement is 0 when baseline values are 0."""
        baseline = AggregatedMetrics(
            scenario_name='Base',
            throughput_per_hour=0.0,
            average_lead_time=0.0
        )
        improved = AggregatedMetrics(
            scenario_name='Improved',
            throughput_per_hour=10.0,
            average_lead_time=100.0
        )
        improvements = improved.improvement_vs(baseline)
        assert improvements['throughput_improvement'] == 0.0
        assert improvements['lead_time_improvement'] == 0.0

    def test_negative_improvement(self):
        """Negative improvement is correctly reported."""
        baseline = AggregatedMetrics(
            scenario_name='Base',
            throughput_per_hour=12.0,
            average_lead_time=150.0
        )
        worse = AggregatedMetrics(
            scenario_name='Worse',
            throughput_per_hour=10.0,
            average_lead_time=200.0
        )
        improvements = worse.improvement_vs(baseline)
        assert improvements['throughput_improvement'] < 0
        assert improvements['lead_time_improvement'] < 0


# ─── aggregate_replications tests ─────────────────────────────────────────────

class TestAggregateReplications:
    """Tests for the aggregate_replications function."""

    def _make_replication(self, scenario_name: str, parts: int, throughput: float,
                          lead_times: list, station_name: str = 'S1') -> SimulationMetrics:
        """Helper to create a SimulationMetrics object."""
        m = SimulationMetrics(
            scenario_name=scenario_name,
            parts_produced=parts,
            shift_duration_seconds=28800.0,
            warmup_duration_seconds=1800.0
        )
        m.completed_parts_lead_times = lead_times

        sm = StationMetrics(station_name=station_name)
        sm.total_busy_time = 1000.0
        sm.total_available_time = 2000.0
        sm.waiting_times = [10.0, 20.0]
        sm.breakdown_count = 1
        sm.total_downtime = 60.0
        m.station_metrics[station_name] = sm
        return m

    def test_aggregate_empty_raises(self):
        """Aggregating empty list raises ValueError."""
        with pytest.raises(ValueError):
            aggregate_replications([])

    def test_aggregate_single_replication(self):
        """Aggregating a single replication returns its values."""
        rep = self._make_replication('Test', 100, 13.33, [200.0, 300.0])
        result = aggregate_replications([rep])
        assert result.parts_produced == pytest.approx(100.0)
        assert result.num_replications == 1

    def test_aggregate_averages_parts(self):
        """Parts produced is averaged across replications."""
        reps = [
            self._make_replication('Test', 100, 13.0, [200.0]),
            self._make_replication('Test', 120, 16.0, [180.0]),
        ]
        result = aggregate_replications(reps)
        assert result.parts_produced == pytest.approx(110.0)

    def test_aggregate_averages_station_utilization(self):
        """Station utilization is averaged across replications."""
        reps = [
            self._make_replication('Test', 100, 13.0, [200.0]),
            self._make_replication('Test', 100, 13.0, [200.0]),
        ]
        result = aggregate_replications(reps)
        # Both have 1000/2000 = 0.5 utilization
        assert result.station_utilizations.get('S1', 0) == pytest.approx(0.5)

    def test_aggregate_collects_all_lead_times(self):
        """All lead times from all replications are collected."""
        reps = [
            self._make_replication('Test', 2, 13.0, [100.0, 200.0]),
            self._make_replication('Test', 2, 13.0, [150.0, 250.0]),
        ]
        result = aggregate_replications(reps)
        assert len(result.all_lead_times) == 4

    def test_aggregate_identifies_bottleneck(self):
        """Bottleneck is the most common across replications."""
        rep1 = self._make_replication('Test', 100, 13.0, [], 'Drilling')
        rep2 = self._make_replication('Test', 100, 13.0, [], 'Drilling')
        rep3 = self._make_replication('Test', 100, 13.0, [], 'Assembly')

        # Manually set utilizations to make Drilling the bottleneck
        for rep in [rep1, rep2]:
            rep.station_metrics['Drilling'].total_busy_time = 1900.0
            rep.station_metrics['Drilling'].total_available_time = 2000.0
        rep3.station_metrics['Assembly'] = StationMetrics(station_name='Assembly')
        rep3.station_metrics['Assembly'].total_busy_time = 1900.0
        rep3.station_metrics['Assembly'].total_available_time = 2000.0

        result = aggregate_replications([rep1, rep2, rep3])
        assert result.bottleneck_station == 'Drilling'
