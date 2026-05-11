"""Simulation service — runs scenarios in background tasks."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from db.crud import (
    create_simulation_result,
    get_simulation_run,
    update_run_progress,
    update_run_status,
)
from db.database import AsyncSessionLocal
from models.request_models import SimulationConfigRequest
from simulation.engine import StationConfig, run_scenario_replications
from simulation.metrics import AggregatedMetrics

logger = logging.getLogger(__name__)

# Registry of active simulation tasks: job_id -> asyncio.Task
_active_tasks: Dict[str, asyncio.Task] = {}

# WebSocket broadcast registry: job_id -> list of send callbacks
_ws_callbacks: Dict[str, List[Callable]] = {}


def get_active_count() -> int:
    """Return number of currently running simulations."""
    return sum(1 for t in _active_tasks.values() if not t.done())


def register_ws_callback(job_id: str, callback: Callable) -> None:
    """Register a WebSocket send callback for a job."""
    _ws_callbacks.setdefault(job_id, []).append(callback)


def unregister_ws_callback(job_id: str, callback: Callable) -> None:
    """Remove a WebSocket send callback."""
    if job_id in _ws_callbacks:
        _ws_callbacks[job_id] = [c for c in _ws_callbacks[job_id] if c != callback]


async def _broadcast(job_id: str, message: dict) -> None:
    """Send a message to all WebSocket clients watching this job."""
    callbacks = _ws_callbacks.get(job_id, [])
    dead = []
    for cb in callbacks:
        try:
            await cb(message)
        except Exception:
            dead.append(cb)
    for cb in dead:
        unregister_ws_callback(job_id, cb)


def _metrics_to_dict(m: AggregatedMetrics) -> dict:
    """Serialize AggregatedMetrics to a JSON-safe dict."""
    return {
        "scenario_name": m.scenario_name,
        "parts_produced": m.parts_produced,
        "throughput_per_hour": m.throughput_per_hour,
        "average_lead_time": m.average_lead_time,
        "bottleneck_station": m.bottleneck_station,
        "station_utilizations": m.station_utilizations,
        "station_waiting_times": m.station_waiting_times,
        "station_breakdown_counts": m.station_breakdown_counts,
        "station_downtimes": m.station_downtimes,
        "station_buffer_occupancies": m.station_buffer_occupancies,
        "all_lead_times": m.all_lead_times[:500],  # cap for storage
        "num_replications": m.num_replications,
        "throughput_variance": m.throughput_variance,
        "lead_time_variance": m.lead_time_variance,
        "parts_produced_variance": m.parts_produced_variance,
    }


async def run_simulation_background(job_id: str, config: SimulationConfigRequest) -> None:
    """Background task that runs the full simulation and stores results."""
    logger.info("Starting simulation job %s", job_id)

    async with AsyncSessionLocal() as db:
        await update_run_status(db, job_id, "running", progress=0)
        await db.commit()

    await _broadcast(job_id, {"type": "status", "status": "running", "progress": 0})

    try:
        station_configs = [
            StationConfig(
                name=s.name,
                cycle_time_mean=s.cycle_time_mean,
                cycle_time_std=s.cycle_time_std,
                buffer_capacity=s.buffer_capacity,
                operators=s.operators,
                breakdown_probability=s.breakdown_probability,
                repair_time_min=s.repair_time_min,
                repair_time_max=s.repair_time_max,
            )
            for s in config.stations
        ]

        total_replications = config.num_replications
        completed_replications = 0

        def sync_event_callback(event_type: str, data: Dict[str, Any]) -> None:
            """Sync callback — schedule async broadcast without blocking SimPy."""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.call_soon_threadsafe(
                        lambda: asyncio.ensure_future(
                            _broadcast(job_id, {"type": "sim_event", "event": event_type, **data})
                        )
                    )
            except Exception:
                pass

        def progress_callback(done: int, total: int) -> None:
            nonlocal completed_replications
            completed_replications = done
            pct = int(done / total * 100)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.call_soon_threadsafe(
                        lambda: asyncio.ensure_future(
                            _update_and_broadcast(job_id, pct)
                        )
                    )
            except Exception:
                pass

        # Run simulation in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        aggregated = await loop.run_in_executor(
            None,
            lambda: run_scenario_replications(
                scenario_name=config.name,
                station_configs=station_configs,
                shift_duration_hours=config.shift_duration_hours,
                warmup_period_minutes=config.warmup_period_minutes,
                num_replications=config.num_replications,
                seed_base=config.seed_base,
                progress_callback=progress_callback,
                event_callback=sync_event_callback,
            ),
        )

        metrics_dict = _metrics_to_dict(aggregated)

        async with AsyncSessionLocal() as db:
            await create_simulation_result(db, job_id, config.name, metrics_dict)
            await update_run_status(db, job_id, "complete", progress=100)
            await db.commit()

        await _broadcast(
            job_id,
            {
                "type": "complete",
                "status": "complete",
                "progress": 100,
                "metrics": metrics_dict,
            },
        )
        logger.info("Simulation job %s completed successfully", job_id)

    except Exception as exc:
        logger.exception("Simulation job %s failed: %s", job_id, exc)
        async with AsyncSessionLocal() as db:
            await update_run_status(db, job_id, "failed", error_message=str(exc))
            await db.commit()
        await _broadcast(job_id, {"type": "error", "status": "failed", "message": str(exc)})
    finally:
        _active_tasks.pop(job_id, None)


async def _update_and_broadcast(job_id: str, progress: int) -> None:
    async with AsyncSessionLocal() as db:
        await update_run_progress(db, job_id, progress)
        await db.commit()
    await _broadcast(job_id, {"type": "progress", "progress": progress})


def start_simulation_task(job_id: str, config: SimulationConfigRequest) -> asyncio.Task:
    """Create and register a background simulation task."""
    task = asyncio.create_task(run_simulation_background(job_id, config))
    _active_tasks[job_id] = task
    return task
