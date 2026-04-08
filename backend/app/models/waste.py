from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel


class WasteEventType(str, Enum):
    SAVED = "saved"     # Item was used before expiring
    WASTED = "wasted"   # Item was thrown away
    FROZEN = "frozen"   # Item was frozen to extend life
    DONATED = "donated" # Item was given away


AVG_PRICE_PER_CATEGORY = {
    "dairy": 4.50,
    "meat": 8.00,
    "seafood": 12.00,
    "fruit": 3.00,
    "vegetable": 2.50,
    "bread": 3.50,
    "eggs": 4.00,
    "leftover": 5.00,
    "condiment": 3.00,
    "canned": 2.00,
    "dry_goods": 3.00,
    "beverage": 3.50,
    "frozen": 5.00,
    "other": 3.00,
}

CO2_KG_PER_FOOD_ITEM = 2.5


class WasteEvent(BaseModel):
    id: str
    user_id: str
    item_name: str
    category: str
    event_type: WasteEventType
    quantity: float = 1.0
    estimated_value: float = 0.0
    co2_saved_kg: float = 0.0
    date: date
    created_at: datetime | None = None


class WasteStats(BaseModel):
    total_items_saved: int = 0
    total_items_wasted: int = 0
    total_items_frozen: int = 0
    total_money_saved: float = 0.0
    total_money_wasted: float = 0.0
    total_co2_saved_kg: float = 0.0
    meals_enabled: int = 0
    save_rate_percent: float = 0.0
    weekly_trend: list[dict] = []
    category_breakdown: dict[str, dict] = {}
