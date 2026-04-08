from __future__ import annotations

import random
import string
from uuid import uuid4

from app.models.household import Household

_households: dict[str, Household] = {}
_user_to_household: dict[str, str] = {}


def _generate_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


async def create_household(user_id: str, name: str) -> Household:
    household = Household(
        id=str(uuid4()),
        name=name,
        code=_generate_code(),
        members=[user_id],
    )
    _households[household.id] = household
    _user_to_household[user_id] = household.id
    return household


async def join_household(user_id: str, code: str) -> Household | None:
    for household in _households.values():
        if household.code == code:
            if user_id not in household.members:
                household.members.append(user_id)
            _user_to_household[user_id] = household.id
            return household
    return None


async def get_household(user_id: str) -> Household | None:
    hid = _user_to_household.get(user_id)
    if hid:
        return _households.get(hid)
    return None


async def get_household_members(user_id: str) -> list[str]:
    household = await get_household(user_id)
    if household:
        return household.members
    return [user_id]


async def leave_household(user_id: str) -> bool:
    hid = _user_to_household.pop(user_id, None)
    if hid and hid in _households:
        household = _households[hid]
        if user_id in household.members:
            household.members.remove(user_id)
        if not household.members:
            del _households[hid]
        return True
    return False
