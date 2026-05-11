"""CRUD operations for all database models."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import SavedScenario, SimulationResult, SimulationRun


# ─── SimulationRun ────────────────────────────────────────────────────────────

async def create_simulation_run(db: AsyncSession, name: str, config: dict) -> SimulationRun:
    run = SimulationRun(name=name, config=config, status="queued", progress=0)
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


async def get_simulation_run(db: AsyncSession, run_id: str) -> Optional[SimulationRun]:
    result = await db.execute(
        select(SimulationRun)
        .options(selectinload(SimulationRun.results))
        .where(SimulationRun.id == run_id)
    )
    return result.scalar_one_or_none()


async def list_simulation_runs(db: AsyncSession, limit: int = 50) -> List[SimulationRun]:
    result = await db.execute(
        select(SimulationRun)
        .options(selectinload(SimulationRun.results))
        .order_by(SimulationRun.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_run_status(
    db: AsyncSession,
    run_id: str,
    status: str,
    progress: int = 0,
    error_message: Optional[str] = None,
) -> Optional[SimulationRun]:
    run = await get_simulation_run(db, run_id)
    if not run:
        return None
    run.status = status
    run.progress = progress
    if error_message:
        run.error_message = error_message
    if status in ("complete", "failed"):
        run.completed_at = datetime.now(timezone.utc)
    await db.flush()
    return run


async def update_run_progress(db: AsyncSession, run_id: str, progress: int) -> None:
    run = await get_simulation_run(db, run_id)
    if run:
        run.progress = progress
        await db.flush()


# ─── SimulationResult ─────────────────────────────────────────────────────────

async def create_simulation_result(
    db: AsyncSession, run_id: str, scenario_name: str, metrics: dict
) -> SimulationResult:
    result = SimulationResult(run_id=run_id, scenario_name=scenario_name, metrics=metrics)
    db.add(result)
    await db.flush()
    return result


async def get_results_for_run(db: AsyncSession, run_id: str) -> List[SimulationResult]:
    result = await db.execute(
        select(SimulationResult).where(SimulationResult.run_id == run_id)
    )
    return list(result.scalars().all())


# ─── SavedScenario ────────────────────────────────────────────────────────────

async def create_saved_scenario(
    db: AsyncSession, name: str, description: str, config: dict
) -> SavedScenario:
    scenario = SavedScenario(name=name, description=description, config=config)
    db.add(scenario)
    await db.flush()
    await db.refresh(scenario)
    return scenario


async def list_saved_scenarios(db: AsyncSession) -> List[SavedScenario]:
    result = await db.execute(select(SavedScenario).order_by(SavedScenario.created_at.desc()))
    return list(result.scalars().all())


async def get_saved_scenario(db: AsyncSession, scenario_id: str) -> Optional[SavedScenario]:
    result = await db.execute(select(SavedScenario).where(SavedScenario.id == scenario_id))
    return result.scalar_one_or_none()


async def delete_saved_scenario(db: AsyncSession, scenario_id: str) -> bool:
    scenario = await get_saved_scenario(db, scenario_id)
    if not scenario:
        return False
    await db.delete(scenario)
    await db.flush()
    return True
