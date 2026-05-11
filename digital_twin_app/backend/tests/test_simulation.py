"""Tests for the simulation engine."""

import pytest

from simulation.engine import SimulationEngine, StationConfig, run_scenario_replications
from simulation.metrics import aggregate_replications
from simulation.part import Part


def _make_station(name="S1", cycle=10.0, std=0.0, buf=5, ops=1):
    return StationConfig(
        name=name,
        cycle_time_mean=cycle,
        cycle_time_std=std,
        buffer_capacity=buf,
        operators=ops,
        breakdown_probability=0.0,
        repair_time_min=30.0,
        repair_time_max=30.0,
    )


def _make_engine(stations=None, shift_hours=0.25, warmup_min=2.0, seed=42):
    if stations is None:
        stations = [_make_station("Feed", 10.0), _make_station("Pack", 8.0)]
    return SimulationEngine(
        scenario_name="Test",
        station_configs=stations,
        shift_duration_hours=shift_hours,
        warmup_period_minutes=warmup_min,
        seed=seed,
    )


class TestSimulationEngine:
    def test_run_returns_metrics(self):
        engine = _make_engine()
        metrics = engine.run()
        assert metrics is not None
        assert metrics.scenario_name == "Test"

    def test_parts_produced_positive(self):
        engine = _make_engine()
        metrics = engine.run()
        assert metrics.parts_produced > 0

    def test_throughput_positive(self):
        engine = _make_engine()
        metrics = engine.run()
        assert metrics.throughput_per_hour > 0

    def test_all_stations_have_metrics(self):
        engine = _make_engine()
        metrics = engine.run()
        assert "Feed" in metrics.station_metrics
        assert "Pack" in metrics.station_metrics

    def test_lead_times_collected(self):
        engine = _make_engine()
        metrics = engine.run()
        assert len(metrics.completed_parts_lead_times) > 0

    def test_lead_times_positive(self):
        engine = _make_engine()
        metrics = engine.run()
        for lt in metrics.completed_parts_lead_times:
            assert lt > 0

    def test_utilization_bounded(self):
        engine = _make_engine()
        metrics = engine.run()
        for sname, sm in metrics.station_metrics.items():
            assert 0.0 <= sm.utilization <= 1.0, f"{sname} utilization out of bounds"

    def test_bottleneck_identified(self):
        engine = _make_engine()
        metrics = engine.run()
        assert metrics.bottleneck_station in ("Feed", "Pack")

    def test_different_seeds_give_different_results(self):
        """Different seeds with variability should produce different lead times."""
        stations = [
            StationConfig("Feed", 10.0, 2.0, 5, 1, 0.0, 30.0, 30.0),
            StationConfig("Pack", 8.0, 2.0, 5, 1, 0.0, 30.0, 30.0),
        ]
        lead_time_sets = []
        for seed in [1, 100, 999]:
            engine = SimulationEngine(
                scenario_name="Test",
                station_configs=stations,
                shift_duration_hours=0.5,
                warmup_period_minutes=2.0,
                seed=seed,
            )
            m = engine.run()
            lead_time_sets.append(round(m.average_lead_time, 1))
        # With different seeds and variability, at least 2 of 3 should differ
        assert len(set(lead_time_sets)) > 1

    def test_event_callback_called(self):
        events = []

        def callback(event_type, data):
            events.append(event_type)

        engine = SimulationEngine(
            scenario_name="Test",
            station_configs=[_make_station()],
            shift_duration_hours=0.1,
            warmup_period_minutes=1.0,
            seed=42,
            event_callback=callback,
        )
        engine.run()
        assert len(events) > 0

    def test_single_station_line(self):
        engine = SimulationEngine(
            scenario_name="Single",
            station_configs=[_make_station("Only", 5.0)],
            shift_duration_hours=0.1,
            warmup_period_minutes=1.0,
            seed=42,
        )
        metrics = engine.run()
        assert metrics.parts_produced >= 0


class TestRunScenarioReplications:
    def test_returns_aggregated_metrics(self):
        stations = [_make_station("Feed", 10.0), _make_station("Pack", 8.0)]
        result = run_scenario_replications(
            scenario_name="Test",
            station_configs=stations,
            shift_duration_hours=0.2,
            warmup_period_minutes=2.0,
            num_replications=3,
            seed_base=42,
        )
        assert result.scenario_name == "Test"
        assert result.num_replications == 3

    def test_progress_callback_called(self):
        progress_calls = []

        def cb(done, total):
            progress_calls.append((done, total))

        stations = [_make_station()]
        run_scenario_replications(
            scenario_name="Test",
            station_configs=stations,
            shift_duration_hours=0.1,
            warmup_period_minutes=1.0,
            num_replications=3,
            seed_base=42,
            progress_callback=cb,
        )
        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)


class TestPart:
    def test_lead_time_calculation(self):
        part = Part(part_id=1, creation_time=100.0)
        part.completion_time = 700.0
        assert part.lead_time == pytest.approx(600.0)

    def test_waiting_time(self):
        part = Part(part_id=1, creation_time=0.0)
        part.record_entry("S1", 10.0)
        part.record_start("S1", 25.0)
        assert part.waiting_time_at("S1") == pytest.approx(15.0)

    def test_waiting_time_missing(self):
        part = Part(part_id=1, creation_time=0.0)
        assert part.waiting_time_at("S1") == 0.0
