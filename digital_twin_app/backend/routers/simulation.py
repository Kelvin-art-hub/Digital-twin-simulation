"""Simulation router — run, status, results, history."""

import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db.crud import (
    create_simulation_run,
    get_simulation_run,
    list_simulation_runs,
)
from db.database import get_db
from models.request_models import SimulationConfigRequest
from models.response_models import (
    JobCreatedResponse,
    SimulationResultsResponse,
    SimulationRunResponse,
    StatusResponse,
)
from services.report_service import build_scenario_response
from services.simulation_service import (
    get_active_count,
    register_ws_callback,
    start_simulation_task,
    unregister_ws_callback,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/simulations", tags=["simulations"])


@router.post("/run", response_model=JobCreatedResponse, status_code=202)
async def run_simulation(
    config: SimulationConfigRequest,
    db: AsyncSession = Depends(get_db),
) -> JobCreatedResponse:
    """Start a simulation run in the background.

    Returns a job ID immediately. Poll /status or connect via WebSocket
    to track progress.
    """
    settings = get_settings()
    if get_active_count() >= settings.max_concurrent_simulations:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum concurrent simulations ({settings.max_concurrent_simulations}) reached. Try again later.",
        )

    run = await create_simulation_run(db, config.name, config.model_dump())
    await db.commit()

    start_simulation_task(run.id, config)

    logger.info("Simulation job %s queued for config '%s'", run.id, config.name)
    return JobCreatedResponse(
        job_id=run.id,
        status="queued",
        message=f"Simulation '{config.name}' queued. Use job_id to track progress.",
    )


@router.get("/{job_id}/status", response_model=StatusResponse)
async def get_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> StatusResponse:
    """Get the current status and progress of a simulation job."""
    run = await get_simulation_run(db, job_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Simulation job '{job_id}' not found")

    messages = {
        "queued": "Simulation is queued and waiting to start.",
        "running": f"Simulation is running ({run.progress}% complete).",
        "complete": "Simulation completed successfully.",
        "failed": f"Simulation failed: {run.error_message or 'Unknown error'}",
    }

    return StatusResponse(
        job_id=run.id,
        status=run.status,
        progress=run.progress,
        message=messages.get(run.status, "Unknown status"),
    )


@router.get("/{job_id}/results", response_model=SimulationResultsResponse)
async def get_results(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> SimulationResultsResponse:
    """Get full results for a completed simulation run."""
    run = await get_simulation_run(db, job_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Simulation job '{job_id}' not found")

    if run.status == "running" or run.status == "queued":
        raise HTTPException(status_code=202, detail="Simulation is still running. Check back later.")

    if run.status == "failed":
        raise HTTPException(status_code=500, detail=f"Simulation failed: {run.error_message}")

    if not run.results:
        raise HTTPException(status_code=404, detail="No results found for this simulation run.")

    # Build scenario responses — first result is treated as baseline
    scenario_responses = []
    baseline_dict = run.results[0].metrics if run.results else None

    for i, result in enumerate(run.results):
        baseline = baseline_dict if i > 0 else None
        scenario_responses.append(build_scenario_response(result.metrics, baseline))

    return SimulationResultsResponse(
        job_id=run.id,
        name=run.name,
        status=run.status,
        created_at=run.created_at,
        completed_at=run.completed_at,
        scenarios=scenario_responses,
    )


@router.get("/history", response_model=List[SimulationRunResponse])
async def get_history(
    db: AsyncSession = Depends(get_db),
) -> List[SimulationRunResponse]:
    """Return list of all past simulation runs."""
    runs = await list_simulation_runs(db)
    return [SimulationRunResponse.model_validate(r) for r in runs]


@router.websocket("/ws/{job_id}")
async def websocket_simulation(websocket: WebSocket, job_id: str) -> None:
    """WebSocket endpoint for real-time simulation progress.

    Streams status updates, progress, and live simulation events.
    """
    await websocket.accept()
    logger.info("WebSocket connected for job %s", job_id)

    async def send_callback(message: dict) -> None:
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            pass

    register_ws_callback(job_id, send_callback)

    try:
        # Send initial status
        async with __import__("db.database", fromlist=["AsyncSessionLocal"]).AsyncSessionLocal() as db:
            from db.crud import get_simulation_run as _get_run
            run = await _get_run(db, job_id)
            if run:
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "status": run.status,
                    "progress": run.progress,
                }))

        # Keep connection alive until client disconnects
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        unregister_ws_callback(job_id, send_callback)
        logger.info("WebSocket disconnected for job %s", job_id)
