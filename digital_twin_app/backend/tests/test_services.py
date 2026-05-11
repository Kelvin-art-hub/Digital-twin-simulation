"""Tests for services."""

import pytest

from services.export_service import generate_csv, generate_lead_times_csv
from services.report_service import build_scenario_response


SAMPLE_METRICS = {
    "scenario_name": "Test Scenario",
    "parts_produced": 100.0,
    "throughput_per_hour": 13.33,
    "average_lead_time": 600.0,
    "bottleneck_station": "Drilling",
    "station_utilizations": {"Feeding": 0.5, "Drilling": 0.99},
    "station_waiting_times": {"Feeding": 10.0, "Drilling": 200.0},
    "station_breakdown_counts": {"Feeding": 2.0, "Drilling": 1.0},
    "station_downtimes": {"Feeding": 120.0, "Drilling": 60.0},
    "station_buffer_occupancies": {"Feeding": 1.0, "Drilling": 3.5},
    "all_lead_times": [500.0, 600.0, 700.0],
    "num_replications": 5,
    "throughput_variance": 0.5,
    "lead_time_variance": 100.0,
    "parts_produced_variance": 4.0,
}


class TestExportService:
    def test_generate_csv_returns_bytes(self):
        csv_bytes = generate_csv("Test Run", [SAMPLE_METRICS])
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0

    def test_generate_csv_contains_scenario_name(self):
        csv_bytes = generate_csv("Test Run", [SAMPLE_METRICS])
        assert b"Test Scenario" in csv_bytes

    def test_generate_csv_contains_headers(self):
        csv_bytes = generate_csv("Test Run", [SAMPLE_METRICS])
        content = csv_bytes.decode("utf-8")
        assert "scenario" in content
        assert "throughput_per_hour" in content
        assert "parts_produced" in content

    def test_generate_csv_multiple_scenarios(self):
        s2 = dict(SAMPLE_METRICS)
        s2["scenario_name"] = "Scenario 2"
        csv_bytes = generate_csv("Test Run", [SAMPLE_METRICS, s2])
        content = csv_bytes.decode("utf-8")
        assert "Test Scenario" in content
        assert "Scenario 2" in content

    def test_generate_lead_times_csv(self):
        csv_bytes = generate_lead_times_csv([SAMPLE_METRICS])
        assert isinstance(csv_bytes, bytes)
        content = csv_bytes.decode("utf-8")
        assert "lead_time_s" in content
        assert "Test Scenario" in content

    def test_generate_lead_times_csv_correct_count(self):
        csv_bytes = generate_lead_times_csv([SAMPLE_METRICS])
        lines = csv_bytes.decode("utf-8").strip().split("\n")
        # 1 header + 3 lead times
        assert len(lines) == 4

    def test_generate_csv_empty_scenarios(self):
        csv_bytes = generate_csv("Empty", [])
        assert isinstance(csv_bytes, bytes)


class TestReportService:
    def test_build_scenario_response(self):
        response = build_scenario_response(SAMPLE_METRICS)
        assert response.scenario_name == "Test Scenario"
        assert response.parts_produced == 100.0
        assert response.throughput_per_hour == pytest.approx(13.33)
        assert response.bottleneck_station == "Drilling"

    def test_build_scenario_response_station_metrics(self):
        response = build_scenario_response(SAMPLE_METRICS)
        assert "Feeding" in response.station_metrics
        assert "Drilling" in response.station_metrics
        assert response.station_metrics["Drilling"].utilization == pytest.approx(0.99)

    def test_build_scenario_response_with_baseline(self):
        baseline = dict(SAMPLE_METRICS)
        baseline["throughput_per_hour"] = 10.0
        baseline["average_lead_time"] = 800.0

        improved = dict(SAMPLE_METRICS)
        improved["throughput_per_hour"] = 12.0
        improved["average_lead_time"] = 600.0

        response = build_scenario_response(improved, baseline)
        assert response.throughput_improvement == pytest.approx(20.0)
        assert response.lead_time_improvement == pytest.approx(25.0)

    def test_build_scenario_response_no_baseline(self):
        response = build_scenario_response(SAMPLE_METRICS)
        assert response.throughput_improvement is None
        assert response.lead_time_improvement is None
