"""Report generation: terminal tables, CSV exports, and matplotlib charts."""

import csv
import os
import logging
from typing import List, Dict, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving files
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from config import STATION_ORDER
from simulation.metrics import AggregatedMetrics

logger = logging.getLogger(__name__)

RESULTS_DIR = "results"


def _ensure_results_dir() -> str:
    """Create the results directory if it does not exist.

    Returns:
        Absolute path to the results directory
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    return RESULTS_DIR


def print_comparison_table(scenarios: List[AggregatedMetrics], baseline: Optional[AggregatedMetrics] = None) -> None:
    """Print a formatted comparison table to the terminal.

    Args:
        scenarios: List of AggregatedMetrics for each scenario
        baseline: Optional baseline scenario for improvement calculations
    """
    if not scenarios:
        logger.warning("No scenarios to display")
        return

    col_width = 22
    name_width = 30

    # Header
    header = f"{'Metric':<{name_width}}" + "".join(
        f"{s.scenario_name:^{col_width}}" for s in scenarios
    )
    separator = "-" * (name_width + col_width * len(scenarios))

    print("\n" + "=" * len(separator))
    print("  DIGITAL TWIN SIMULATION — ASSEMBLY LINE COMPARISON REPORT")
    print("=" * len(separator))
    print(header)
    print(separator)

    def row(label: str, values: List[str]) -> str:
        return f"{label:<{name_width}}" + "".join(f"{v:^{col_width}}" for v in values)

    # Parts produced
    print(row(
        "Parts Produced (avg)",
        [f"{s.parts_produced:.1f}" for s in scenarios]
    ))

    # Throughput
    print(row(
        "Throughput (parts/hr)",
        [f"{s.throughput_per_hour:.2f}" for s in scenarios]
    ))

    # Average lead time
    print(row(
        "Avg Lead Time (min)",
        [f"{s.average_lead_time / 60:.2f}" for s in scenarios]
    ))

    print(separator)
    print(f"{'--- Station Utilization ---':<{name_width}}")

    for station in STATION_ORDER:
        print(row(
            f"  {station} Util (%)",
            [f"{s.station_utilizations.get(station, 0) * 100:.1f}%" for s in scenarios]
        ))

    print(separator)
    print(f"{'--- Avg Waiting Time (s) ---':<{name_width}}")

    for station in STATION_ORDER:
        print(row(
            f"  {station} Wait (s)",
            [f"{s.station_waiting_times.get(station, 0):.1f}" for s in scenarios]
        ))

    print(separator)
    print(f"{'--- Breakdowns ---':<{name_width}}")

    for station in STATION_ORDER:
        print(row(
            f"  {station} Breakdowns",
            [f"{s.station_breakdown_counts.get(station, 0):.1f}" for s in scenarios]
        ))
        print(row(
            f"  {station} Downtime (min)",
            [f"{s.station_downtimes.get(station, 0) / 60:.1f}" for s in scenarios]
        ))

    print(separator)
    print(row(
        "Bottleneck Station",
        [s.bottleneck_station for s in scenarios]
    ))

    # Improvement vs baseline
    if baseline:
        print(separator)
        print(f"{'--- vs Base Case ---':<{name_width}}")
        for s in scenarios:
            improvements = s.improvement_vs(baseline)
            tp_imp = improvements.get('throughput_improvement', 0.0)
            lt_imp = improvements.get('lead_time_improvement', 0.0)
            tp_str = f"{tp_imp:+.1f}%" if s.scenario_name != baseline.scenario_name else "baseline"
            lt_str = f"{lt_imp:+.1f}%" if s.scenario_name != baseline.scenario_name else "baseline"
            print(row(f"  Throughput Δ", [tp_str if s.scenario_name == s.scenario_name else ""]))
            break  # Print per-scenario below

        for s in scenarios:
            improvements = s.improvement_vs(baseline)
            tp_imp = improvements.get('throughput_improvement', 0.0)
            lt_imp = improvements.get('lead_time_improvement', 0.0)
            if s.scenario_name == baseline.scenario_name:
                tp_str = "baseline"
                lt_str = "baseline"
            else:
                tp_str = f"{tp_imp:+.1f}%"
                lt_str = f"{lt_imp:+.1f}%"

        # Print improvement rows properly
        tp_values = []
        lt_values = []
        for s in scenarios:
            improvements = s.improvement_vs(baseline)
            if s.scenario_name == baseline.scenario_name:
                tp_values.append("baseline")
                lt_values.append("baseline")
            else:
                tp_values.append(f"{improvements.get('throughput_improvement', 0):+.1f}%")
                lt_values.append(f"{improvements.get('lead_time_improvement', 0):+.1f}%")

        print(row("  Throughput Δ vs Base", tp_values))
        print(row("  Lead Time Δ vs Base", lt_values))

    print("=" * len(separator))
    print()


def export_scenario_csv(scenarios: List[AggregatedMetrics], filename: str = "scenario_metrics.csv") -> str:
    """Export per-scenario metrics to a CSV file.

    Args:
        scenarios: List of AggregatedMetrics for each scenario
        filename: Output filename (saved in results directory)

    Returns:
        Full path to the saved CSV file
    """
    results_dir = _ensure_results_dir()
    filepath = os.path.join(results_dir, filename)

    fieldnames = [
        'scenario', 'parts_produced', 'throughput_per_hour', 'avg_lead_time_s',
        'bottleneck_station', 'num_replications'
    ]
    for station in STATION_ORDER:
        fieldnames += [
            f'{station}_utilization_pct',
            f'{station}_avg_wait_s',
            f'{station}_breakdown_count',
            f'{station}_downtime_s'
        ]

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for s in scenarios:
            row_data: Dict = {
                'scenario': s.scenario_name,
                'parts_produced': f"{s.parts_produced:.2f}",
                'throughput_per_hour': f"{s.throughput_per_hour:.4f}",
                'avg_lead_time_s': f"{s.average_lead_time:.2f}",
                'bottleneck_station': s.bottleneck_station,
                'num_replications': s.num_replications
            }
            for station in STATION_ORDER:
                row_data[f'{station}_utilization_pct'] = f"{s.station_utilizations.get(station, 0) * 100:.2f}"
                row_data[f'{station}_avg_wait_s'] = f"{s.station_waiting_times.get(station, 0):.2f}"
                row_data[f'{station}_breakdown_count'] = f"{s.station_breakdown_counts.get(station, 0):.2f}"
                row_data[f'{station}_downtime_s'] = f"{s.station_downtimes.get(station, 0):.2f}"
            writer.writerow(row_data)

    logger.info("Scenario metrics CSV saved: %s", filepath)
    return filepath


def export_lead_times_csv(scenarios: List[AggregatedMetrics], filename: str = "lead_times.csv") -> str:
    """Export per-part lead time data to a CSV file.

    Args:
        scenarios: List of AggregatedMetrics for each scenario
        filename: Output filename (saved in results directory)

    Returns:
        Full path to the saved CSV file
    """
    results_dir = _ensure_results_dir()
    filepath = os.path.join(results_dir, filename)

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['scenario', 'part_index', 'lead_time_s', 'lead_time_min'])

        for s in scenarios:
            for idx, lt in enumerate(s.all_lead_times):
                writer.writerow([s.scenario_name, idx + 1, f"{lt:.2f}", f"{lt / 60:.4f}"])

    logger.info("Lead times CSV saved: %s", filepath)
    return filepath


def plot_station_utilization(scenarios: List[AggregatedMetrics], filename: str = "station_utilization.png") -> str:
    """Generate a grouped bar chart of station utilization per scenario.

    Args:
        scenarios: List of AggregatedMetrics for each scenario
        filename: Output filename (saved in results directory)

    Returns:
        Full path to the saved PNG file
    """
    results_dir = _ensure_results_dir()
    filepath = os.path.join(results_dir, filename)

    stations = STATION_ORDER
    n_stations = len(stations)
    n_scenarios = len(scenarios)

    x = np.arange(n_stations)
    bar_width = 0.25
    offsets = np.linspace(-(n_scenarios - 1) / 2, (n_scenarios - 1) / 2, n_scenarios) * bar_width

    colors = ['#2196F3', '#FF9800', '#4CAF50', '#E91E63', '#9C27B0']

    fig, ax = plt.subplots(figsize=(12, 6))

    for i, (scenario, offset) in enumerate(zip(scenarios, offsets)):
        utils = [scenario.station_utilizations.get(s, 0) * 100 for s in stations]
        bars = ax.bar(
            x + offset, utils,
            width=bar_width,
            label=scenario.scenario_name,
            color=colors[i % len(colors)],
            alpha=0.85,
            edgecolor='white',
            linewidth=0.5
        )
        # Add value labels on bars
        for bar, val in zip(bars, utils):
            if val > 2:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f"{val:.1f}%",
                    ha='center', va='bottom',
                    fontsize=7.5, fontweight='bold'
                )

    ax.set_xlabel('Station', fontsize=12)
    ax.set_ylabel('Utilization (%)', fontsize=12)
    ax.set_title('Station Utilization by Scenario', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(stations, fontsize=10)
    ax.set_ylim(0, 115)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)

    logger.info("Station utilization chart saved: %s", filepath)
    return filepath


def plot_throughput_comparison(scenarios: List[AggregatedMetrics], filename: str = "throughput_comparison.png") -> str:
    """Generate a bar chart comparing throughput across scenarios.

    Args:
        scenarios: List of AggregatedMetrics for each scenario
        filename: Output filename (saved in results directory)

    Returns:
        Full path to the saved PNG file
    """
    results_dir = _ensure_results_dir()
    filepath = os.path.join(results_dir, filename)

    names = [s.scenario_name for s in scenarios]
    throughputs = [s.throughput_per_hour for s in scenarios]
    colors = ['#2196F3', '#FF9800', '#4CAF50']

    fig, ax = plt.subplots(figsize=(9, 5))

    bars = ax.bar(
        names, throughputs,
        color=colors[:len(scenarios)],
        alpha=0.85,
        edgecolor='white',
        linewidth=0.8,
        width=0.5
    )

    # Add value labels
    for bar, val in zip(bars, throughputs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            f"{val:.2f}",
            ha='center', va='bottom',
            fontsize=11, fontweight='bold'
        )

    # Add improvement annotations vs first scenario (baseline)
    if len(scenarios) > 1:
        baseline_tp = throughputs[0]
        for i, (bar, val) in enumerate(zip(bars[1:], throughputs[1:]), start=1):
            if baseline_tp > 0:
                pct = (val - baseline_tp) / baseline_tp * 100
                sign = "+" if pct >= 0 else ""
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.35,
                    f"({sign}{pct:.1f}% vs base)",
                    ha='center', va='bottom',
                    fontsize=9, color='#555555', style='italic'
                )

    ax.set_ylabel('Throughput (parts/hour)', fontsize=12)
    ax.set_title('Throughput Comparison Across Scenarios', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylim(0, max(throughputs) * 1.25)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='x', labelsize=11)

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)

    logger.info("Throughput comparison chart saved: %s", filepath)
    return filepath
