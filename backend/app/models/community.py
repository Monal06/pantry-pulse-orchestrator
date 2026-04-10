from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ListingStatus(str, Enum):
    AVAILABLE = "available"
    CLAIMED = "claimed"
    EXPIRED = "expired"


class CommunityListing(BaseModel):
    id: str
    user_id: str
    item_name: str
    category: str = "other"
    quantity: float = 1.0
    unit: str = "item"
    description: str = ""
    pickup_location: str = ""
    status: ListingStatus = ListingStatus.AVAILABLE
    claimed_by: str | None = None
    created_at: str = ""
    expires_at: str = ""


class CommunityListingCreate(BaseModel):
    item_name: str
    category: str = "other"
    quantity: float = 1.0
    unit: str = "item"
    description: str = ""
    pickup_location: str = ""
    hours_available: int = Field(default=24, ge=1, le=72)
