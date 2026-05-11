"""Extra buffer scenario: increased buffer before Drilling station."""

import copy
import logging
from typing import List
from config import SimulationConfig, SIMULATION_CONFIG, BASE_STATIONS
from simulation.engine import SimulationEngine
from simulation.metrics import SimulationMetrics, AggregatedMetrics, aggregate_replications

logger = logging.getLogger(__name__)

SCENARIO_NAME = "Extra Buffer"

# Buffer size increase for Drilling station
DRILLING_BUFFER_SIZE = 10


def run_scenario(
    sim_config: SimulationConfig = SIMULATION_CONFIG
) -> AggregatedMetrics:
    """Run the extra buffer scenario across multiple replications.

    Identical to base case except the buffer before Drilling is
    increased from 5 to 10, allowing more parts to queue before
    the bottleneck station.

    Args:
        sim_config: Simulation configuration (defaults to global config)

    Returns:
        AggregatedMetrics averaged across all replications
    """
    logger.info("Running scenario: %s (%d replications)", SCENARIO_NAME, sim_config.num_replications)

    station_configs = copy.deepcopy(BASE_STATIONS)
    station_configs['Drilling'].buffer_size = DRILLING_BUFFER_SIZE

    logger.info(
        "  Modified: Drilling buffer_size = %d (was %d)",
        DRILLING_BUFFER_SIZE, BASE_STATIONS['Drilling'].buffer_size
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
