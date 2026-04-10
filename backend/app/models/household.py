from __future__ import annotations

from pydantic import BaseModel


class Household(BaseModel):
    id: str
    name: str
    code: str
    members: list[str] = []


class HouseholdCreate(BaseModel):
    name: str


class HouseholdJoin(BaseModel):
    code: str
