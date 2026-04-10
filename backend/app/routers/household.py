from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.household import HouseholdCreate, HouseholdJoin
from app.services import household_service

router = APIRouter(prefix="/household", tags=["household"])

DEFAULT_USER = "demo-user"


@router.get("")
async def get_household(user_id: str = Query(default=DEFAULT_USER)):
    """Get the current user's household."""
    household = await household_service.get_household(user_id)
    if household is None:
        return {"household": None, "message": "Not part of a household. Create or join one."}
    return household.model_dump()


@router.post("/create")
async def create_household(
    data: HouseholdCreate,
    user_id: str = Query(default=DEFAULT_USER),
):
    """Create a new household and get a shareable code."""
    household = await household_service.create_household(user_id, data.name)
    return {
        **household.model_dump(),
        "message": f"Household created! Share code '{household.code}' with family members.",
    }


@router.post("/join")
async def join_household(
    data: HouseholdJoin,
    user_id: str = Query(default=DEFAULT_USER),
):
    """Join an existing household using a code."""
    household = await household_service.join_household(user_id, data.code)
    if household is None:
        raise HTTPException(status_code=404, detail="Invalid household code")
    return {
        **household.model_dump(),
        "message": f"Joined household '{household.name}'!",
    }


@router.post("/leave")
async def leave_household(user_id: str = Query(default=DEFAULT_USER)):
    """Leave the current household."""
    left = await household_service.leave_household(user_id)
    if not left:
        raise HTTPException(status_code=404, detail="Not part of a household")
    return {"status": "left"}
