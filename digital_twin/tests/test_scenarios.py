"""Integration tests for all three simulation scenarios."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import SimulationConfig
from simulation.metrics import AggregatedMetrics
from scenarios import base_case, extra_buffer, bottleneck_fix


# ─── Shared fast config ───────────────────────────────────────────────────────

@pytest.fixture
def fast_config():
    """Reduced simulation config for fast test execution."""
    return SimulationConfig(
        shift_duration_hours=1.0,
        warmup_period_minutes=5.0,
        cycle_time_std_dev_ratio=0.05,
        breakdown_repair_time_min=10.0,
        breakdown_repair_time_max=20.0,
        num_replications=2,
        random_seed_base=999
    )


# ─── Base case tests ──────────────────────────────────────────────────────────

class TestBaseCase:
    """Tests for the base case scenario."""

    def test_returns_aggregated_metrics(self, fast_config):
        """Base case returns an AggregatedMetrics object."""
        result = base_case.run_scenario(fast_config)
        assert isinstance(result, AggregatedMetrics)

    def test_scenario_name(self, fast_config):
        """Base case has correct scenario name."""
        result = base_case.run_scenario(fast_config)
        assert result.scenario_name == base_case.SCENARIO_NAME

    def test_parts_produced_positive(self, fast_config):
        """Base case produces a positive number of parts."""
        result = base_case.run_scenario(fast_config)
        assert result.parts_produced > 0

    def test_throughput_positive(self, fast_config):
        """Base case has positive throughput."""
        result = base_case.run_scenario(fast_config)
        assert result.throughput_per_hour > 0

    def test_all_stations_have_metrics(self, fast_config):
        """Base case records metrics for all 5 stations."""
        result = base_case.run_scenario(fast_config)
        expected_stations = {'Feeding', 'Drilling', 'Inspection', 'Assembly', 'Packing'}
        assert expected_stations.issubset(set(result.station_utilizations.keys()))

    def test_utilizations_bounded(self, fast_config):
        """All station utilizations are between 0 and 1."""
        result = base_case.run_scenario(fast_config)
        for station, util in result.station_utilizations.items():
            assert 0.0 <= util <= 1.0, f"{station} utilization {util} out of bounds"

    def test_bottleneck_identified(self, fast_config):
        """Base case identifies a bottleneck station."""
        result = base_case.run_scenario(fast_config)
        assert result.bottleneck_station != ''
        assert result.bottleneck_station in {'Feeding', 'Drilling', 'Inspection', 'Assembly', 'Packing'}

    def test_lead_times_collected(self, fast_config):
        """Base case collects lead time data."""
        result = base_case.run_scenario(fast_config)
        assert len(result.all_lead_times) > 0

    def test_lead_times_positive(self, fast_config):
        """All lead times are positive."""
        result = base_case.run_scenario(fast_config)
        for lt in result.all_lead_times:
            assert lt > 0, f"Non-positive lead time: {lt}"

    def test_num_replications(self, fast_config):
        """Correct number of replications is recorded."""
        result = base_case.run_scenario(fast_config)
        assert result.num_replications == fast_config.num_replications


# ─── Extra buffer tests ───────────────────────────────────────────────────────

class TestExtraBuffer:
    """Tests for the extra buffer scenario."""

    def test_returns_aggregated_metrics(self, fast_config):
        """Extra buffer returns an AggregatedMetrics object."""
        result = extra_buffer.run_scenario(fast_config)
        assert isinstance(result, AggregatedMetrics)

    def test_scenario_name(self, fast_config):
        """Extra buffer has correct scenario name."""
        result = extra_buffer.run_scenario(fast_config)
        assert result.scenario_name == extra_buffer.SCENARIO_NAME

    def test_parts_produced_positive(self, fast_config):
        """Extra buffer produces a positive number of parts."""
        result = extra_buffer.run_scenario(fast_config)
        assert result.parts_produced > 0

    def test_all_stations_have_metrics(self, fast_config):
        """Extra buffer records metrics for all 5 stations."""
        result = extra_buffer.run_scenario(fast_config)
        expected_stations = {'Feeding', 'Drilling', 'Inspection', 'Assembly', 'Packing'}
        assert expected_stations.issubset(set(result.station_utilizations.keys()))

    def test_drilling_buffer_size_modified(self):
        """Extra buffer scenario uses increased Drilling buffer size."""
        assert extra_buffer.DRILLING_BUFFER_SIZE == 10
        assert extra_buffer.DRILLING_BUFFER_SIZE > 5  # Greater than base case


# ─── Bottleneck fix tests ─────────────────────────────────────────────────────

class TestBottleneckFix:
    """Tests for the bottleneck fix scenario."""

    def test_returns_aggregated_metrics(self, fast_config):
        """Bottleneck fix returns an AggregatedMetrics object."""
        result = bottleneck_fix.run_scenario(fast_config)
        assert isinstance(result, AggregatedMetrics)

    def test_scenario_name(self, fast_config):
        """Bottleneck fix has correct scenario name."""
        result = bottleneck_fix.run_scenario(fast_config)
        assert result.scenario_name == bottleneck_fix.SCENARIO_NAME

    def test_parts_produced_positive(self, fast_config):
        """Bottleneck fix produces a positive number of parts."""
        result = bottleneck_fix.run_scenario(fast_config)
        assert result.parts_produced > 0

    def test_all_stations_have_metrics(self, fast_config):
        """Bottleneck fix records metrics for all 5 stations."""
        result = bottleneck_fix.run_scenario(fast_config)
        expected_stations = {'Feeding', 'Drilling', 'Inspection', 'Assembly', 'Packing'}
        assert expected_stations.issubset(set(result.station_utilizations.keys()))

    def test_drilling_parameters_modified(self):
        """Bottleneck fix uses correct Drilling parameters."""
        assert bottleneck_fix.DRILLING_OPERATORS == 2
        assert bottleneck_fix.DRILLING_CYCLE_TIME == 24.0

    def test_throughput_improvement_over_base(self, fast_config):
        """Bottleneck fix should generally improve throughput over base case."""
        base = base_case.run_scenario(fast_config)
        fixed = bottleneck_fix.run_scenario(fast_config)
        # With same seeds, bottleneck fix should produce more or equal parts
        # (allow small tolerance for stochastic variation with few replications)
        assert fixed.throughput_per_hour >= base.throughput_per_hour * 0.9


# ─── Cross-scenario comparison tests ─────────────────────────────────────────

class TestScenarioComparison:
    """Tests comparing scenarios against each other."""

    @pytest.fixture(autouse=True)
    def run_all(self, fast_config):
        """Run all scenarios once for comparison tests."""
        self.base = base_case.run_scenario(fast_config)
        self.buffer = extra_buffer.run_scenario(fast_config)
        self.fix = bottleneck_fix.run_scenario(fast_config)

    def test_all_scenarios_produce_parts(self):
        """All scenarios produce a positive number of parts."""
        assert self.base.parts_produced > 0
        assert self.buffer.parts_produced > 0
        assert self.fix.parts_produced > 0

    def test_improvement_calculation_works(self):
        """Improvement calculation runs without error."""
        improvements = self.fix.improvement_vs(self.base)
        assert 'throughput_improvement' in improvements
        assert 'lead_time_improvement' in improvements

    def test_different_scenario_names(self):
        """All scenarios have distinct names."""
        names = {self.base.scenario_name, self.buffer.scenario_name, self.fix.scenario_name}
        assert len(names) == 3

    def test_bottleneck_fix_reduces_drilling_utilization(self):
        """Bottleneck fix should reduce Drilling utilization."""
        base_drilling_util = self.base.station_utilizations.get('Drilling', 0)
        fix_drilling_util = self.fix.station_utilizations.get('Drilling', 0)
        # With 2 operators and faster cycle, Drilling utilization should drop
        # Allow tolerance for stochastic variation
        assert fix_drilling_util <= base_drilling_util * 1.1
