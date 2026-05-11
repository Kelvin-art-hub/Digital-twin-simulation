"""Scenarios router — save, list, delete saved scenarios."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import (
    create_saved_scenario,
    delete_saved_scenario,
    get_saved_scenario,
    list_saved_scenarios,
)
from db.database import get_db
from models.request_models import SaveScenarioRequest
from models.response_models import SavedScenarioResponse

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.post("", response_model=SavedScenarioResponse, status_code=201)
async def save_scenario(
    request: SaveScenarioRequest,
    db: AsyncSession = Depends(get_db),
) -> SavedScenarioResponse:
    """Save a named scenario configuration to the database."""
    scenario = await create_saved_scenario(
        db,
        name=request.name,
        description=request.description,
        config=request.config.model_dump(),
    )
    await db.commit()
    return SavedScenarioResponse.model_validate(scenario)


@router.get("", response_model=List[SavedScenarioResponse])
async def list_scenarios(
    db: AsyncSession = Depends(get_db),
) -> List[SavedScenarioResponse]:
    """List all saved scenarios."""
    scenarios = await list_saved_scenarios(db)
    return [SavedScenarioResponse.model_validate(s) for s in scenarios]


@router.get("/{scenario_id}", response_model=SavedScenarioResponse)
async def get_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
) -> SavedScenarioResponse:
    """Get a single saved scenario by ID."""
    scenario = await get_saved_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return SavedScenarioResponse.model_validate(scenario)


@router.delete("/{scenario_id}", status_code=204)
async def delete_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a saved scenario."""
    deleted = await delete_saved_scenario(db, scenario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    await db.commit()
