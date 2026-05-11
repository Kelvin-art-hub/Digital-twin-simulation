"""Export service — CSV and PDF generation."""

import csv
import io
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _get_station_order(scenarios: List[Dict[str, Any]]) -> List[str]:
    """Extract station names from the first scenario's metrics."""
    if not scenarios:
        return []
    first = scenarios[0]
    return list(first.get("station_utilizations", {}).keys())


def generate_csv(run_name: str, scenarios: List[Dict[str, Any]]) -> bytes:
    """Generate a CSV file with per-scenario metrics.

    Args:
        run_name: Name of the simulation run
        scenarios: List of scenario metrics dicts

    Returns:
        CSV content as bytes
    """
    output = io.StringIO()
    station_names = _get_station_order(scenarios)

    fieldnames = [
        "scenario",
        "parts_produced",
        "throughput_per_hour",
        "avg_lead_time_s",
        "bottleneck_station",
        "num_replications",
        "throughput_variance",
        "lead_time_variance",
    ]
    for sname in station_names:
        fieldnames += [
            f"{sname}_utilization_pct",
            f"{sname}_avg_wait_s",
            f"{sname}_breakdown_count",
            f"{sname}_downtime_s",
            f"{sname}_buffer_occupancy",
        ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for s in scenarios:
        row: Dict[str, Any] = {
            "scenario": s.get("scenario_name", ""),
            "parts_produced": f"{s.get('parts_produced', 0):.2f}",
            "throughput_per_hour": f"{s.get('throughput_per_hour', 0):.4f}",
            "avg_lead_time_s": f"{s.get('average_lead_time', 0):.2f}",
            "bottleneck_station": s.get("bottleneck_station", ""),
            "num_replications": s.get("num_replications", 0),
            "throughput_variance": f"{s.get('throughput_variance', 0):.4f}",
            "lead_time_variance": f"{s.get('lead_time_variance', 0):.4f}",
        }
        utils = s.get("station_utilizations", {})
        waits = s.get("station_waiting_times", {})
        bdowns = s.get("station_breakdown_counts", {})
        dtimes = s.get("station_downtimes", {})
        buffs = s.get("station_buffer_occupancies", {})

        for sname in station_names:
            row[f"{sname}_utilization_pct"] = f"{utils.get(sname, 0) * 100:.2f}"
            row[f"{sname}_avg_wait_s"] = f"{waits.get(sname, 0):.2f}"
            row[f"{sname}_breakdown_count"] = f"{bdowns.get(sname, 0):.2f}"
            row[f"{sname}_downtime_s"] = f"{dtimes.get(sname, 0):.2f}"
            row[f"{sname}_buffer_occupancy"] = f"{buffs.get(sname, 0):.2f}"

        writer.writerow(row)

    return output.getvalue().encode("utf-8")


def generate_lead_times_csv(scenarios: List[Dict[str, Any]]) -> bytes:
    """Generate a CSV with per-part lead time data."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["scenario", "part_index", "lead_time_s", "lead_time_min"])

    for s in scenarios:
        name = s.get("scenario_name", "")
        for idx, lt in enumerate(s.get("all_lead_times", [])):
            writer.writerow([name, idx + 1, f"{lt:.2f}", f"{lt / 60:.4f}"])

    return output.getvalue().encode("utf-8")


def generate_pdf_report(
    run_name: str,
    run_date: datetime,
    config: Dict[str, Any],
    scenarios: List[Dict[str, Any]],
) -> bytes:
    """Generate a formatted PDF report using ReportLab.

    Args:
        run_name: Name of the simulation run
        run_date: When the simulation was run
        config: Simulation configuration dict
        scenarios: List of scenario metrics dicts

    Returns:
        PDF content as bytes
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            HRFlowable,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        raise RuntimeError("reportlab is required for PDF generation. Install it with: pip install reportlab")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=24,
        spaceAfter=12,
        textColor=colors.HexColor("#1e3a5f"),
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.HexColor("#1e3a5f"),
    )
    body_style = styles["BodyText"]
    body_style.fontSize = 10

    story = []

    # ── Title Page ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Digital Twin Simulation Report", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e3a5f")))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"<b>Run Name:</b> {run_name}", body_style))
    story.append(Paragraph(f"<b>Date:</b> {run_date.strftime('%Y-%m-%d %H:%M UTC')}", body_style))
    story.append(Paragraph(f"<b>Scenarios:</b> {len(scenarios)}", body_style))
    story.append(PageBreak())

    # ── Configuration Summary ────────────────────────────────────────────────
    story.append(Paragraph("Simulation Configuration", heading_style))
    story.append(Paragraph(
        f"Shift Duration: {config.get('shift_duration_hours', 8)} hours | "
        f"Warm-up: {config.get('warmup_period_minutes', 30)} minutes | "
        f"Replications: {config.get('num_replications', 10)}",
        body_style,
    ))
    story.append(Spacer(1, 0.5 * cm))

    stations = config.get("stations", [])
    if stations:
        station_data = [["Station", "Cycle Time (s)", "Std Dev", "Buffer", "Operators", "Breakdown %"]]
        for st in stations:
            station_data.append([
                st.get("name", ""),
                f"{st.get('cycle_time_mean', 0):.1f}",
                f"{st.get('cycle_time_std', 0):.1f}",
                str(st.get("buffer_capacity", 0)),
                str(st.get("operators", 0)),
                f"{st.get('breakdown_probability', 0) * 100:.1f}%",
            ])
        t = Table(station_data, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)

    story.append(PageBreak())

    # ── Scenario Comparison Table ────────────────────────────────────────────
    story.append(Paragraph("Scenario Comparison", heading_style))

    if scenarios:
        baseline = scenarios[0]
        headers = ["Metric"] + [s.get("scenario_name", f"Scenario {i+1}") for i, s in enumerate(scenarios)]
        rows = [headers]

        def fmt_row(label, values):
            return [label] + values

        rows.append(fmt_row("Parts Produced", [f"{s.get('parts_produced', 0):.1f}" for s in scenarios]))
        rows.append(fmt_row("Throughput (parts/hr)", [f"{s.get('throughput_per_hour', 0):.2f}" for s in scenarios]))
        rows.append(fmt_row("Avg Lead Time (min)", [f"{s.get('average_lead_time', 0) / 60:.2f}" for s in scenarios]))
        rows.append(fmt_row("Bottleneck Station", [s.get("bottleneck_station", "") for s in scenarios]))

        station_names = list(scenarios[0].get("station_utilizations", {}).keys())
        for sname in station_names:
            utils = [s.get("station_utilizations", {}).get(sname, 0) for s in scenarios]
            rows.append(fmt_row(f"{sname} Utilization", [f"{u * 100:.1f}%" for u in utils]))

        # Improvement row
        base_tp = baseline.get("throughput_per_hour", 1)
        improvements = []
        for s in scenarios:
            if s.get("scenario_name") == baseline.get("scenario_name"):
                improvements.append("baseline")
            else:
                pct = (s.get("throughput_per_hour", 0) - base_tp) / base_tp * 100 if base_tp else 0
                improvements.append(f"{pct:+.1f}%")
        rows.append(fmt_row("Throughput vs Base", improvements))

        col_widths = [4 * cm] + [3.5 * cm] * len(scenarios)
        t = Table(rows, colWidths=col_widths, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)

    story.append(PageBreak())

    # ── Bottleneck Analysis ──────────────────────────────────────────────────
    story.append(Paragraph("Bottleneck Analysis", heading_style))
    for s in scenarios:
        bottleneck = s.get("bottleneck_station", "N/A")
        util = s.get("station_utilizations", {}).get(bottleneck, 0)
        story.append(Paragraph(
            f"<b>{s.get('scenario_name', '')}:</b> Bottleneck is <b>{bottleneck}</b> "
            f"at {util * 100:.1f}% utilization.",
            body_style,
        ))
    story.append(Spacer(1, 0.5 * cm))

    # ── Key Findings ─────────────────────────────────────────────────────────
    story.append(Paragraph("Key Findings", heading_style))
    if len(scenarios) >= 1:
        base = scenarios[0]
        findings = []
        findings.append(
            f"The base scenario '{base.get('scenario_name', '')}' achieved "
            f"{base.get('throughput_per_hour', 0):.2f} parts/hour with an average "
            f"lead time of {base.get('average_lead_time', 0) / 60:.1f} minutes."
        )
        if len(scenarios) > 1:
            best = max(scenarios[1:], key=lambda s: s.get("throughput_per_hour", 0))
            base_tp = base.get("throughput_per_hour", 1)
            best_tp = best.get("throughput_per_hour", 0)
            pct = (best_tp - base_tp) / base_tp * 100 if base_tp else 0
            findings.append(
                f"The best performing alternative scenario '{best.get('scenario_name', '')}' "
                f"improved throughput by {pct:+.1f}% over the base case."
            )
        for finding in findings:
            story.append(Paragraph(f"• {finding}", body_style))

    doc.build(story)
    return buffer.getvalue()
