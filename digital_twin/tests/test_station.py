"""Unit tests for the Station class and Part dataclass."""

import sys
import os
import pytest
import simpy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import StationConfig, SimulationConfig
from simulation.part import Part
from simulation.station import Station


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sim_config():
    """Minimal simulation config for testing."""
    return SimulationConfig(
        shift_duration_hours=1.0,
        warmup_period_minutes=0.0,
        cycle_time_std_dev_ratio=0.0,   # No variability for deterministic tests
        breakdown_repair_time_min=30.0,
        breakdown_repair_time_max=30.0,
        num_replications=1,
        random_seed_base=0
    )


@pytest.fixture
def station_config():
    """Standard station config for testing."""
    return StationConfig(
        name='TestStation',
        cycle_time=10.0,
        buffer_size=5,
        operators=1,
        breakdown_probability=0.0   # No breakdowns for deterministic tests
    )


# ─── Part tests ───────────────────────────────────────────────────────────────

class TestPart:
    """Tests for the Part dataclass."""

    def test_creation(self):
        """Part is created with correct id and creation time."""
        part = Part(part_id=1, creation_time=0.0)
        assert part.part_id == 1
        assert part.creation_time == 0.0
        assert part.completion_time is None
        assert part.lead_time is None

    def test_record_entry(self):
        """Entry time is recorded correctly."""
        part = Part(part_id=1, creation_time=0.0)
        part.record_entry('Station1', 5.0)
        assert part.entry_times['Station1'] == 5.0

    def test_record_start(self):
        """Start time is recorded correctly."""
        part = Part(part_id=1, creation_time=0.0)
        part.record_start('Station1', 10.0)
        assert part.start_times['Station1'] == 10.0

    def test_record_exit(self):
        """Exit time is recorded correctly."""
        part = Part(part_id=1, creation_time=0.0)
        part.record_exit('Station1', 20.0)
        assert part.exit_times['Station1'] == 20.0

    def test_waiting_time(self):
        """Waiting time is correctly calculated as start - entry."""
        part = Part(part_id=1, creation_time=0.0)
        part.record_entry('S1', 5.0)
        part.record_start('S1', 12.0)
        assert part.waiting_time_at('S1') == pytest.approx(7.0)

    def test_waiting_time_zero_when_no_wait(self):
        """Waiting time is 0 when part starts immediately."""
        part = Part(part_id=1, creation_time=0.0)
        part.record_entry('S1', 5.0)
        part.record_start('S1', 5.0)
        assert part.waiting_time_at('S1') == pytest.approx(0.0)

    def test_waiting_time_missing_timestamps(self):
        """Waiting time returns 0 when timestamps are missing."""
        part = Part(part_id=1, creation_time=0.0)
        assert part.waiting_time_at('S1') == 0.0

    def test_processing_time(self):
        """Processing time is correctly calculated as exit - start."""
        part = Part(part_id=1, creation_time=0.0)
        part.record_start('S1', 10.0)
        part.record_exit('S1', 25.0)
        assert part.processing_time_at('S1') == pytest.approx(15.0)

    def test_lead_time(self):
        """Lead time is correctly calculated as completion - creation."""
        part = Part(part_id=1, creation_time=100.0)
        part.completion_time = 250.0
        assert part.lead_time == pytest.approx(150.0)

    def test_lead_time_none_before_completion(self):
        """Lead time is None before part is completed."""
        part = Part(part_id=1, creation_time=0.0)
        assert part.lead_time is None


# ─── Station tests ────────────────────────────────────────────────────────────

class TestStation:
    """Tests for the Station class."""

    def test_station_processes_part(self, station_config, sim_config):
        """Station processes a part and records timestamps."""
        env = simpy.Environment()
        station = Station(env=env, config=station_config, sim_config=sim_config, warmup_end_time=0.0)

        completed_parts = []

        def inject_and_collect():
            part = Part(part_id=1, creation_time=0.0)
            yield env.process(station.receive_part(part))
            # Wait for processing to complete
            yield env.timeout(station_config.cycle_time + 1.0)
            completed_parts.append(part)

        env.process(inject_and_collect())
        env.run(until=station_config.cycle_time * 3)

        assert len(completed_parts) == 1
        part = completed_parts[0]
        assert station_config.name in part.start_times
        assert station_config.name in part.exit_times

    def test_station_buffer_capacity(self, station_config, sim_config):
        """Station buffer respects capacity limit."""
        env = simpy.Environment()
        station = Station(env=env, config=station_config, sim_config=sim_config, warmup_end_time=0.0)

        # Buffer capacity should match config
        assert station.buffer.capacity == station_config.buffer_size

    def test_station_operator_count(self, station_config, sim_config):
        """Station creates correct number of operators."""
        env = simpy.Environment()
        station = Station(env=env, config=station_config, sim_config=sim_config, warmup_end_time=0.0)
        assert station.operators.capacity == station_config.operators

    def test_station_metrics_updated(self, station_config, sim_config):
        """Station metrics are updated after processing."""
        env = simpy.Environment()
        station = Station(env=env, config=station_config, sim_config=sim_config, warmup_end_time=0.0)

        def inject():
            part = Part(part_id=1, creation_time=0.0)
            yield env.process(station.receive_part(part))

        env.process(inject())
        env.run(until=station_config.cycle_time * 5)

        station.finalize_metrics(station_config.cycle_time * 5)
        assert station.metrics.parts_processed >= 1
        assert station.metrics.total_busy_time > 0

    def test_station_utilization_bounded(self, station_config, sim_config):
        """Station utilization is between 0 and 1."""
        env = simpy.Environment()
        station = Station(env=env, config=station_config, sim_config=sim_config, warmup_end_time=0.0)

        def inject():
            for i in range(3):
                part = Part(part_id=i, creation_time=env.now)
                yield env.process(station.receive_part(part))

        env.process(inject())
        env.run(until=station_config.cycle_time * 10)
        station.finalize_metrics(station_config.cycle_time * 10)

        assert 0.0 <= station.metrics.utilization <= 1.0

    def test_multi_operator_station(self, sim_config):
        """Station with multiple operators can process parts in parallel."""
        config = StationConfig(
            name='MultiOp',
            cycle_time=10.0,
            buffer_size=10,
            operators=2,
            breakdown_probability=0.0
        )
        env = simpy.Environment()
        station = Station(env=env, config=config, sim_config=sim_config, warmup_end_time=0.0)
        assert station.operators.capacity == 2

    def test_station_chaining(self, station_config, sim_config):
        """Parts flow from one station to the next."""
        env = simpy.Environment()

        config2 = StationConfig(
            name='Station2',
            cycle_time=5.0,
            buffer_size=5,
            operators=1,
            breakdown_probability=0.0
        )

        station1 = Station(env=env, config=station_config, sim_config=sim_config, warmup_end_time=0.0)
        station2 = Station(env=env, config=config2, sim_config=sim_config, warmup_end_time=0.0)
        station1.next_station = station2

        completed = []

        def inject():
            part = Part(part_id=1, creation_time=0.0)
            yield env.process(station1.receive_part(part))
            yield env.timeout(100)
            completed.append(part)

        env.process(inject())
        env.run(until=200)

        assert len(completed) == 1
        part = completed[0]
        # Part should have been processed at both stations
        assert station_config.name in part.exit_times
        assert config2.name in part.exit_times
