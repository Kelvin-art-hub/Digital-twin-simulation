"""Pydantic v2 response models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class StationMetricsResponse(BaseModel):
    """Metrics for a single station."""

    station_name: str
    utilization: float
    average_waiting_time: float
    breakdown_count: float
    total_downtime: float
    average_buffer_occupancy: float
    parts_processed: float


class ScenarioResultResponse(BaseModel):
    """Results for a single scenario."""

    scenario_name: str
    parts_produced: float
    throughput_per_hour: float
    average_lead_time: float
    bottleneck_station: str
    station_metrics: Dict[str, StationMetricsResponse]
    all_lead_times: List[float]
    num_replications: int
    throughput_variance: float
    lead_time_variance: float
    parts_produced_variance: float
    throughput_improvement: Optional[float] = None
    lead_time_improvement: Optional[float] = None


class SimulationRunResponse(BaseModel):
    """Response for a simulation run (status + summary)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    progress: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SimulationResultsResponse(BaseModel):
    """Full results for a completed simulation run."""

    job_id: str
    name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    scenarios: List[ScenarioResultResponse]


class JobCreatedResponse(BaseModel):
    """Response when a simulation job is created."""

    job_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    """Status response for a simulation job."""

    job_id: str
    status: str
    progress: int
    message: str


class SavedScenarioResponse(BaseModel):
    """Response for a saved scenario."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    config: Dict[str, Any]
    created_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str
    active_simulations: int
