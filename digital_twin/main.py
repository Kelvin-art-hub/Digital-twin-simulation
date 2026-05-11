"""Main entry point for the digital twin assembly line simulation.

Run with:
    python main.py

This will execute all three scenarios, print a comparison table,
save CSV reports, and save charts to the results/ directory.
"""

import logging
import sys
import os
import time

# Ensure the package root is on the path when running directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SIMULATION_CONFIG
from scenarios import base_case, extra_buffer, bottleneck_fix
from reports.report_generator import (
    print_comparison_table,
    export_scenario_csv,
    export_lead_times_csv,
    plot_station_utilization,
    plot_throughput_comparison
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Execute all scenarios, generate reports, and save outputs."""
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("Digital Twin Simulation — Assembly Line")
    logger.info("Shift: %.1f hours | Warm-up: %.0f min | Replications: %d",
                SIMULATION_CONFIG.shift_duration_hours,
                SIMULATION_CONFIG.warmup_period_minutes,
                SIMULATION_CONFIG.num_replications)
    logger.info("=" * 60)

    # Run all three scenarios
    logger.info("Running Base Case scenario...")
    base_metrics = base_case.run_scenario(SIMULATION_CONFIG)

    logger.info("Running Extra Buffer scenario...")
    buffer_metrics = extra_buffer.run_scenario(SIMULATION_CONFIG)

    logger.info("Running Bottleneck Fix scenario...")
    fix_metrics = bottleneck_fix.run_scenario(SIMULATION_CONFIG)

    all_scenarios = [base_metrics, buffer_metrics, fix_metrics]

    # Print comparison table
    print_comparison_table(all_scenarios, baseline=base_metrics)

    # Export CSVs
    csv_path = export_scenario_csv(all_scenarios)
    lt_csv_path = export_lead_times_csv(all_scenarios)

    # Generate charts
    util_chart = plot_station_utilization(all_scenarios)
    tp_chart = plot_throughput_comparison(all_scenarios)

    elapsed = time.time() - start_time

    logger.info("=" * 60)
    logger.info("All outputs saved:")
    logger.info("  Scenario metrics CSV : %s", csv_path)
    logger.info("  Lead times CSV       : %s", lt_csv_path)
    logger.info("  Utilization chart    : %s", util_chart)
    logger.info("  Throughput chart     : %s", tp_chart)
    logger.info("Total runtime: %.1f seconds", elapsed)
    logger.info("=" * 60)

    print(f"\nOutputs saved to '{os.path.abspath('results')}/'")
    print(f"  {os.path.basename(csv_path)}")
    print(f"  {os.path.basename(lt_csv_path)}")
    print(f"  {os.path.basename(util_chart)}")
    print(f"  {os.path.basename(tp_chart)}")
    print(f"\nTotal runtime: {elapsed:.1f}s\n")


if __name__ == '__main__':
    main()
