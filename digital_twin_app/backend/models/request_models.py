"""Pydantic v2 request models."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class StationConfigRequest(BaseModel):
    """Configuration for a single station."""

    name: str = Field(..., min_length=1, max_length=100)
    cycle_time_mean: float = Field(..., gt=0, description="Mean cycle time in seconds")
    cycle_time_std: float = Field(..., ge=0, description="Std dev of cycle time in seconds")
    buffer_capacity: int = Field(..., ge=1, le=100)
    operators: int = Field(..., ge=1, le=10)
    breakdown_probability: float = Field(0.02, ge=0.0, le=1.0)
    repair_time_min: float = Field(30.0, gt=0)
    repair_time_max: float = Field(90.0, gt=0)

    @field_validator("repair_time_max")
    @classmethod
    def max_gte_min(cls, v: float, info) -> float:
        if "repair_time_min" in info.data and v < info.data["repair_time_min"]:
            raise ValueError("repair_time_max must be >= repair_time_min")
        return v

    @field_validator("cycle_time_std")
    @classmethod
    def std_reasonable(cls, v: float, info) -> float:
        if "cycle_time_mean" in info.data and v > info.data["cycle_time_mean"] * 2:
            raise ValueError("cycle_time_std should not exceed 2x the mean")
        return v


class SimulationConfigRequest(BaseModel):
    """Full simulation configuration for a run request."""

    name: str = Field("Unnamed Run", min_length=1, max_length=255)
    stations: List[StationConfigRequest] = Field(..., min_length=1, max_length=10)
    shift_duration_hours: float = Field(8.0, gt=0, le=24)
    warmup_period_minutes: float = Field(30.0, ge=0, le=120)
    num_replications: int = Field(10, ge=1, le=50)
    seed_base: int = Field(42, ge=0)

    @field_validator("stations")
    @classmethod
    def unique_station_names(cls, v: List[StationConfigRequest]) -> List[StationConfigRequest]:
        names = [s.name for s in v]
        if len(names) != len(set(names)):
            raise ValueError("Station names must be unique")
        return v


class SaveScenarioRequest(BaseModel):
    """Request to save a named scenario configuration."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field("", max_length=1000)
    config: SimulationConfigRequest
