"""Report service — assembles scenario results for API responses."""

from typing import Any, Dict, List, Optional

from models.response_models import ScenarioResultResponse, StationMetricsResponse


def build_scenario_response(
    metrics_dict: Dict[str, Any],
    baseline_dict: Optional[Dict[str, Any]] = None,
) -> ScenarioResultResponse:
    """Build a ScenarioResultResponse from a stored metrics dict.

    Args:
        metrics_dict: Raw metrics dict from the database
        baseline_dict: Optional baseline metrics for improvement calculation

    Returns:
        ScenarioResultResponse
    """
    station_metrics: Dict[str, StationMetricsResponse] = {}
    station_names = list(metrics_dict.get("station_utilizations", {}).keys())

    for sname in station_names:
        station_metrics[sname] = StationMetricsResponse(
            station_name=sname,
            utilization=metrics_dict.get("station_utilizations", {}).get(sname, 0.0),
            average_waiting_time=metrics_dict.get("station_waiting_times", {}).get(sname, 0.0),
            breakdown_count=metrics_dict.get("station_breakdown_counts", {}).get(sname, 0.0),
            total_downtime=metrics_dict.get("station_downtimes", {}).get(sname, 0.0),
            average_buffer_occupancy=metrics_dict.get("station_buffer_occupancies", {}).get(sname, 0.0),
            parts_processed=metrics_dict.get("parts_produced", 0.0),
        )

    throughput_improvement = None
    lead_time_improvement = None

    if baseline_dict:
        base_tp = baseline_dict.get("throughput_per_hour", 0)
        base_lt = baseline_dict.get("average_lead_time", 0)
        curr_tp = metrics_dict.get("throughput_per_hour", 0)
        curr_lt = metrics_dict.get("average_lead_time", 0)

        if base_tp > 0:
            throughput_improvement = (curr_tp - base_tp) / base_tp * 100
        if base_lt > 0:
            lead_time_improvement = (base_lt - curr_lt) / base_lt * 100

    return ScenarioResultResponse(
        scenario_name=metrics_dict.get("scenario_name", ""),
        parts_produced=metrics_dict.get("parts_produced", 0.0),
        throughput_per_hour=metrics_dict.get("throughput_per_hour", 0.0),
        average_lead_time=metrics_dict.get("average_lead_time", 0.0),
        bottleneck_station=metrics_dict.get("bottleneck_station", ""),
        station_metrics=station_metrics,
        all_lead_times=metrics_dict.get("all_lead_times", []),
        num_replications=metrics_dict.get("num_replications", 0),
        throughput_variance=metrics_dict.get("throughput_variance", 0.0),
        lead_time_variance=metrics_dict.get("lead_time_variance", 0.0),
        parts_produced_variance=metrics_dict.get("parts_produced_variance", 0.0),
        throughput_improvement=throughput_improvement,
        lead_time_improvement=lead_time_improvement,
    )
