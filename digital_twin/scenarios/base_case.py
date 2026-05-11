"""Base case scenario: standard assembly line configuration."""

import copy
import logging
from typing import List
from config import SimulationConfig, SIMULATION_CONFIG, BASE_STATIONS, STATION_ORDER
from simulation.engine import SimulationEngine
from simulation.metrics import SimulationMetrics, AggregatedMetrics, aggregate_replications

logger = logging.getLogger(__name__)

SCENARIO_NAME = "Base Case"


def run_scenario(
    sim_config: SimulationConfig = SIMULATION_CONFIG
) -> AggregatedMetrics:
    """Run the base case scenario across multiple replications.

    Uses the standard station parameters:
    - Feeding: 18s cycle, buffer 5, 1 operator
    - Drilling: 42s cycle, buffer 5, 1 operator
    - Inspection: 22s cycle, buffer 5, 1 operator
    - Assembly: 30s cycle, buffer 5, 2 operators
    - Packing: 20s cycle, buffer 5, 1 operator

    Args:
        sim_config: Simulation configuration (defaults to global config)

    Returns:
        AggregatedMetrics averaged across all replications
    """
    logger.info("Running scenario: %s (%d replications)", SCENARIO_NAME, sim_config.num_replications)

    station_configs = copy.deepcopy(BASE_STATIONS)
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
