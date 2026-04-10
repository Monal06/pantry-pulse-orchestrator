from __future__ import annotations

from app.models.profile import DietaryProfile

_profiles: dict[str, DietaryProfile] = {}


async def get_profile(user_id: str) -> DietaryProfile:
    return _profiles.get(user_id, DietaryProfile())


async def update_profile(user_id: str, profile: DietaryProfile) -> DietaryProfile:
    _profiles[user_id] = profile
    return profile
