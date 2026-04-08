from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.profile import DietaryProfile
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])

DEFAULT_USER = "demo-user"


@router.get("/dietary", response_model=DietaryProfile)
async def get_dietary_profile(user_id: str = Query(default=DEFAULT_USER)):
    """Get the user's dietary preferences and restrictions."""
    return await profile_service.get_profile(user_id)


@router.put("/dietary", response_model=DietaryProfile)
async def update_dietary_profile(
    profile: DietaryProfile,
    user_id: str = Query(default=DEFAULT_USER),
):
    """Update dietary preferences. These are used when generating meal suggestions."""
    return await profile_service.update_profile(user_id, profile)
