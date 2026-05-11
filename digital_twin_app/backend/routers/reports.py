"""Reports router — CSV and PDF export."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import get_simulation_run
from db.database import get_db
from services.export_service import generate_csv, generate_lead_times_csv, generate_pdf_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{job_id}/csv")
async def download_csv(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download full metrics as CSV."""
    run = await get_simulation_run(db, job_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Simulation job '{job_id}' not found")

    if run.status != "complete":
        raise HTTPException(status_code=400, detail="Simulation is not complete yet")

    if not run.results:
        raise HTTPException(status_code=404, detail="No results found for this simulation run")

    scenarios = [r.metrics for r in run.results]
    csv_bytes = generate_csv(run.name, scenarios)

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{run.name}_metrics.csv"'},
    )


@router.get("/{job_id}/csv/lead_times")
async def download_lead_times_csv(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download per-part lead times as CSV."""
    run = await get_simulation_run(db, job_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Simulation job '{job_id}' not found")

    if run.status != "complete":
        raise HTTPException(status_code=400, detail="Simulation is not complete yet")

    if not run.results:
        raise HTTPException(status_code=404, detail="No results found for this simulation run")

    scenarios = [r.metrics for r in run.results]
    csv_bytes = generate_lead_times_csv(scenarios)

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{run.name}_lead_times.csv"'},
    )


@router.get("/{job_id}/pdf")
async def download_pdf(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Generate and download a formatted PDF report."""
    run = await get_simulation_run(db, job_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Simulation job '{job_id}' not found")

    if run.status != "complete":
        raise HTTPException(status_code=400, detail="Simulation is not complete yet")

    if not run.results:
        raise HTTPException(status_code=404, detail="No results found for this simulation run")

    scenarios = [r.metrics for r in run.results]

    try:
        pdf_bytes = generate_pdf_report(
            run_name=run.name,
            run_date=run.created_at,
            config=run.config,
            scenarios=scenarios,
        )
    except Exception as exc:
        logger.exception("Failed to generate PDF: %s", exc)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{run.name}_report.pdf"'},
    )
