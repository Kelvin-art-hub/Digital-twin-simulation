"""Bottleneck fix scenario: second operator and reduced cycle time at Drilling."""

import copy
import logging
from typing import List
from config import SimulationConfig, SIMULATION_CONFIG, BASE_STATIONS
from simulation.engine import SimulationEngine
from simulation.metrics import SimulationMetrics, AggregatedMetrics, aggregate_replications

logger = logging.getLogger(__name__)

SCENARIO_NAME = "Bottleneck Fix"

# Drilling station improvements
DRILLING_OPERATORS = 2
DRILLING_CYCLE_TIME = 24.0  # seconds


def run_scenario(
    sim_config: SimulationConfig = SIMULATION_CONFIG
) -> AggregatedMetrics:
    """Run the bottleneck fix scenario across multiple replications.

    Addresses the Drilling bottleneck by:
    - Adding a second operator (1 -> 2)
    - Reducing cycle time from 42s to 24s

    This models the effect of adding a second drill press or
    a more skilled/faster operator at the bottleneck station.

    Args:
        sim_config: Simulation configuration (defaults to global config)

    Returns:
        AggregatedMetrics averaged across all replications
    """
    logger.info("Running scenario: %s (%d replications)", SCENARIO_NAME, sim_config.num_replications)

    station_configs = copy.deepcopy(BASE_STATIONS)
    station_configs['Drilling'].operators = DRILLING_OPERATORS
    station_configs['Drilling'].cycle_time = DRILLING_CYCLE_TIME

    logger.info(
        "  Modified: Drilling operators = %d (was %d), cycle_time = %.1fs (was %.1fs)",
        DRILLING_OPERATORS, BASE_STATIONS['Drilling'].operators,
        DRILLING_CYCLE_TIME, BASE_STATIONS['Drilling'].cycle_time
    )

    replications: List[SimulationMetrics] = []

    for i in range(sim_config.num_replications):
        seed = sim_config.random_seed_base + i * 100
        engine = SimulationEngine(
            scenario_name=SCENARIO_NAME,
            station_configs=station_configs,
            sim_config=sim_config,
            seed=seed,
            replication_index=i
        )
        result = engine.run()
        replications.append(result)
        logger.info(
            "  Replication %d/%d: parts=%d, throughput=%.2f/hr",
            i + 1, sim_config.num_replications,
            result.parts_produced, result.throughput_per_hour
        )

    aggregated = aggregate_replications(replications)
    logger.info(
        "Scenario '%s' complete: avg_parts=%.1f, avg_throughput=%.2f/hr, "
        "bottleneck=%s",
        SCENARIO_NAME, aggregated.parts_produced,
        aggregated.throughput_per_hour, aggregated.bottleneck_station
    )
    return aggregated
