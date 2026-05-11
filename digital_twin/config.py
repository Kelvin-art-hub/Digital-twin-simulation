"""Configuration module for the digital twin simulation.

All simulation parameters and station configurations are defined here.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class StationConfig:
    """Configuration for a single station.
    
    Attributes:
        name: Station name
        cycle_time: Mean cycle time in seconds
        buffer_size: Maximum buffer capacity before this station
        operators: Number of operators at this station
        breakdown_probability: Probability of breakdown per cycle (0-1)
    """
    name: str
    cycle_time: float
    buffer_size: int
    operators: int
    breakdown_probability: float = 0.02


@dataclass
class SimulationConfig:
    """Global simulation configuration.
    
    Attributes:
        shift_duration_hours: Total simulation time in hours
        warmup_period_minutes: Warm-up period to exclude from metrics
        cycle_time_std_dev_ratio: Standard deviation as ratio of mean cycle time
        breakdown_repair_time_min: Minimum repair time in seconds
        breakdown_repair_time_max: Maximum repair time in seconds
        num_replications: Number of simulation runs per scenario
        random_seed_base: Base seed for random number generation
    """
    shift_duration_hours: float = 8.0
    warmup_period_minutes: float = 30.0
    cycle_time_std_dev_ratio: float = 0.1
    breakdown_repair_time_min: float = 30.0
    breakdown_repair_time_max: float = 90.0
    num_replications: int = 10
    random_seed_base: int = 42


# Base case station configurations
BASE_STATIONS: Dict[str, StationConfig] = {
    'Feeding': StationConfig(
        name='Feeding',
        cycle_time=18.0,
        buffer_size=5,
        operators=1
    ),
    'Drilling': StationConfig(
        name='Drilling',
        cycle_time=42.0,
        buffer_size=5,
        operators=1
    ),
    'Inspection': StationConfig(
        name='Inspection',
        cycle_time=22.0,
        buffer_size=5,
        operators=1
    ),
    'Assembly': StationConfig(
        name='Assembly',
        cycle_time=30.0,
        buffer_size=5,
        operators=2
    ),
    'Packing': StationConfig(
        name='Packing',
        cycle_time=20.0,
        buffer_size=5,
        operators=1
    )
}

# Station processing order
STATION_ORDER = ['Feeding', 'Drilling', 'Inspection', 'Assembly', 'Packing']

# Global simulation configuration
SIMULATION_CONFIG = SimulationConfig()
