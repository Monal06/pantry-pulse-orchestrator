from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field


class StorageLocation(str, Enum):
    FRIDGE = "fridge"
    FREEZER = "freezer"
    PANTRY = "pantry"
    COUNTER = "counter"


class FreshnessCategory(str, Enum):
    GOOD = "good"              # 70-100
    USE_SOON = "use_soon"      # 50-70
    CRITICAL = "critical"      # 0-50


FRESHNESS_DECAY_RATES: dict[str, dict[str, float]] = {
    "dairy": {"fridge": 5.0, "freezer": 0.5, "pantry": 15.0, "counter": 15.0},
    "meat": {"fridge": 8.0, "freezer": 0.3, "pantry": 25.0, "counter": 25.0},
    "seafood": {"fridge": 10.0, "freezer": 0.3, "pantry": 30.0, "counter": 30.0},
    "fruit": {"fridge": 3.5, "freezer": 0.5, "pantry": 5.0, "counter": 6.0},
    "vegetable": {"fridge": 3.0, "freezer": 0.4, "pantry": 5.0, "counter": 6.0},
    "bread": {"fridge": 4.0, "freezer": 0.3, "pantry": 7.0, "counter": 7.0},
    "eggs": {"fridge": 2.0, "freezer": 0.5, "pantry": 8.0, "counter": 8.0},
    "leftover": {"fridge": 10.0, "freezer": 0.5, "pantry": 25.0, "counter": 25.0},
    "condiment": {"fridge": 0.5, "freezer": 0.2, "pantry": 0.5, "counter": 0.5},
    "canned": {"fridge": 0.1, "freezer": 0.1, "pantry": 0.1, "counter": 0.1},
    "dry_goods": {"fridge": 0.1, "freezer": 0.1, "pantry": 0.2, "counter": 0.2},
    "beverage": {"fridge": 1.0, "freezer": 0.3, "pantry": 0.5, "counter": 1.0},
    "frozen": {"fridge": 8.0, "freezer": 0.2, "pantry": 20.0, "counter": 20.0},
    "other": {"fridge": 2.0, "freezer": 0.3, "pantry": 3.0, "counter": 4.0},
}


def get_decay_rate(category: str, storage: str) -> float:
    rates = FRESHNESS_DECAY_RATES.get(category, FRESHNESS_DECAY_RATES["other"])
    return rates.get(storage, 3.0)


def compute_freshness(added_date: date, category: str, storage: str) -> float:
    days_elapsed = (date.today() - added_date).days
    decay = get_decay_rate(category, storage)
    freshness = max(0.0, 100.0 - days_elapsed * decay)
    return round(freshness, 1)


def freshness_category(score: float) -> FreshnessCategory:
    if score >= 70:
        return FreshnessCategory.GOOD
    if score >= 50:
        return FreshnessCategory.USE_SOON
    return FreshnessCategory.CRITICAL


class PantryItemBase(BaseModel):
    name: str
    category: str = "other"
    quantity: float = 1.0
    unit: str = "item"
    storage: StorageLocation = StorageLocation.FRIDGE
    is_perishable: bool = True
    barcode: str | None = None
    notes: str | None = None
    price: float | None = None


class PantryItemCreate(PantryItemBase):
    added_date: date = Field(default_factory=date.today)


class PantryItemUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    quantity: float | None = None
    unit: str | None = None
    storage: StorageLocation | None = None
    is_perishable: bool | None = None
    notes: str | None = None
    price: float | None = None


class PantryItem(PantryItemBase):
    id: str
    user_id: str
    added_date: date
    freshness_score: float = 100.0
    freshness_status: FreshnessCategory = FreshnessCategory.GOOD
    created_at: datetime | None = None

    @classmethod
    def from_db_row(cls, row: dict) -> PantryItem:
        storage = row.get("storage", "fridge")
        category = row.get("category", "other")
        added = row.get("added_date", str(date.today()))
        if isinstance(added, str):
            added = date.fromisoformat(added)

        is_perishable = row.get("is_perishable", True)
        score = compute_freshness(added, category, storage) if is_perishable else 100.0

        return cls(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            category=category,
            quantity=row.get("quantity", 1),
            unit=row.get("unit", "item"),
            storage=StorageLocation(storage),
            is_perishable=is_perishable,
            barcode=row.get("barcode"),
            notes=row.get("notes"),
            price=row.get("price"),
            added_date=added,
            freshness_score=score,
            freshness_status=freshness_category(score),
            created_at=row.get("created_at"),
        )


class SpoilageReport(BaseModel):
    item_name: str
    spoilage_detected: bool
    signs: list[str] = []
    confidence: float = 0.0
    recommendation: str = ""


class AnalysisResult(BaseModel):
    items: list[PantryItemCreate]
    spoilage_reports: list[SpoilageReport] = []
    raw_description: str = ""


class ShoppingListItem(BaseModel):
    name: str
    category: str = "other"
    reason: str = ""
    urgency: str = "normal"  # normal, soon, urgent


class MealSuggestion(BaseModel):
    name: str
    description: str
    ingredients_used: list[str]
    instructions: list[str]
    freshness_priority: str
    prep_time_minutes: int = 30
