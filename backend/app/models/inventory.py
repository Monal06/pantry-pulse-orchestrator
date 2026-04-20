from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional
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


# ---------------------------------------------------------------------------
# USDA-Backed Freshness Decay Rates
# ---------------------------------------------------------------------------
# Each value = 100 / (max safe storage days) from USDA FoodKeeper & USDA
# Cold Storage Charts.  A higher number means faster decay.
#
# Sources:
#   • USDA FoodKeeper App Data (foodkeeper.fsis.usda.gov)
#   • USDA Cold Storage Chart (fsis.usda.gov/food-safety)
#   • FDA Refrigerator & Freezer Storage Chart
#
# Formula reminder:  freshness = 100 − (days_elapsed × decay_rate)
#   → item hits 0 % at exactly (100 / decay_rate) days.
#
# Category        | Storage   | USDA Max Days      | decay = 100/days
# ---------------------------------------------------------------------------
# Dairy (milk)    | fridge    | 7 d                 | 14.3
# Dairy           | freezer   | 90 d (hard cheese)  |  1.1
# Meat (ground)   | fridge    | 2 d                 | 50.0
# Meat (steaks)   | fridge    | 5 d                 | 20.0
# Meat (avg)      | fridge    | 3–5 d  → 4 d avg    | 25.0
# Meat            | freezer   | 4–12 mo → 240 d avg |  0.42
# Seafood (fresh) | fridge    | 1–2 d  → 2 d        | 50.0
# Seafood         | freezer   | 3–6 mo → 120 d      |  0.83
# Fruit (berries) | fridge    | 3–7 d  → 5 d avg    | 20.0
# Fruit (apples)  | fridge    | 21–28 d → 25 d      |  4.0
# Fruit (avg)     | fridge    | ~14 d               |  7.1
# Vegetable       | fridge    | 7–14 d → 10 d avg   | 10.0
# Bread           | counter   | 5–7 d  → 7 d        | 14.3
# Bread           | freezer   | 90 d                |  1.1
# Eggs            | fridge    | 21–35 d → 35 d      |  2.86
# Leftovers       | fridge    | 3–4 d  → 4 d        | 25.0
# Condiments      | fridge    | 60–180 d → 120 d    |  0.83
# Canned goods    | pantry    | 730 d  (2 yr)       |  0.14
# Dry goods       | pantry    | 365 d  (1 yr)       |  0.27
# Beverages       | fridge    | 7–14 d (opened)     |  7.1
# Frozen meals    | freezer   | 90–180 d → 120 d    |  0.83
# ---------------------------------------------------------------------------

FRESHNESS_DECAY_RATES: dict[str, dict[str, float]] = {
    # Dairy — USDA: milk 7 d fridge, hard cheese 6 mo freezer
    "dairy":     {"fridge": 14.3,  "freezer": 1.1,  "pantry": 50.0,  "counter": 50.0},

    # Meat — USDA: raw ground 2 d, steaks/chops 3-5 d, frozen 4-12 mo
    "meat":      {"fridge": 25.0,  "freezer": 0.42, "pantry": 100.0, "counter": 100.0},

    # Seafood — USDA: fresh fish 1-2 d fridge, 3-6 mo freezer
    "seafood":   {"fridge": 50.0,  "freezer": 0.83, "pantry": 100.0, "counter": 100.0},

    # Fruit — USDA: berries 3-7 d, citrus 2-3 wk, apples 4 wk; ~14 d weighted avg
    "fruit":     {"fridge": 7.1,   "freezer": 0.83, "pantry": 10.0,  "counter": 14.3},

    # Vegetable — USDA: leafy greens 3-7 d, carrots 3-4 wk; ~10 d avg
    "vegetable": {"fridge": 10.0,  "freezer": 0.83, "pantry": 14.3,  "counter": 20.0},

    # Bread — USDA: 5-7 d counter, 3 mo freezer
    "bread":     {"fridge": 7.1,   "freezer": 1.1,  "pantry": 14.3,  "counter": 14.3},

    # Eggs — USDA: 3-5 weeks in fridge (35 d), 12 mo freezer (beaten)
    "eggs":      {"fridge": 2.86,  "freezer": 0.27, "pantry": 20.0,  "counter": 20.0},

    # Leftovers — USDA: 3-4 days fridge, 2-3 mo freezer
    "leftover":  {"fridge": 25.0,  "freezer": 1.1,  "pantry": 100.0, "counter": 100.0},

    # Condiments — USDA: ketchup 6 mo, mustard 12 mo; ~4 mo avg opened
    "condiment": {"fridge": 0.83,  "freezer": 0.27, "pantry": 1.67,  "counter": 1.67},

    # Canned goods — USDA: 2-5 years unopened; using 2 yr (730 d)
    "canned":    {"fridge": 0.14,  "freezer": 0.14, "pantry": 0.14,  "counter": 0.14},

    # Dry goods — USDA: pasta/rice 1-2 yr, flour 6-8 mo; ~1 yr avg (365 d)
    "dry_goods": {"fridge": 0.14,  "freezer": 0.14, "pantry": 0.27,  "counter": 0.27},

    # Beverages — USDA: opened juice 7-10 d, opened soda ~7 d
    "beverage":  {"fridge": 7.1,   "freezer": 0.55, "pantry": 1.67,  "counter": 3.3},

    # Frozen meals — USDA: 3-4 months in freezer (avg 120 d)
    "frozen":    {"fridge": 25.0,  "freezer": 0.83, "pantry": 50.0,  "counter": 50.0},

    # Fallback — conservative 7-day fridge assumption
    "other":     {"fridge": 14.3,  "freezer": 0.55, "pantry": 5.0,   "counter": 7.1},
}


def get_decay_rate(category: str, storage: str, item_name: Optional[str] = None) -> float:
    """
    Return freshness decay rate (points per day).

    Priority:
      1. USDA FoodKeeper item-specific rate (if item_name provided and matched)
      2. Generic category-based rate from FRESHNESS_DECAY_RATES
    """
    # Try item-specific USDA FoodKeeper lookup first
    if item_name:
        try:
            from app.services.foodkeeper_service import get_foodkeeper_decay_rate
            fk_rate = get_foodkeeper_decay_rate(item_name, storage)
            if fk_rate is not None:
                return fk_rate
        except Exception:
            pass  # FoodKeeper unavailable — fall through to category rates

    rates = FRESHNESS_DECAY_RATES.get(category, FRESHNESS_DECAY_RATES["other"])
    return rates.get(storage, 3.0)


def compute_freshness(
    added_date: date,
    category: str,
    storage: str,
    purchase_date: Optional[date] = None,
    item_name: Optional[str] = None,
) -> float:
    """
    Compute freshness score (0-100) for a food item.

    When *item_name* is provided the function first tries a USDA FoodKeeper
    lookup for a precise per-product decay rate before falling back to the
    generic category rate.
    """
    # Use actual purchase date if known, otherwise use added_date
    # This handles case where user buys Monday but adds to system Friday
    age_reference = purchase_date if purchase_date else added_date
    days_elapsed = (date.today() - age_reference).days
    decay = get_decay_rate(category, storage, item_name)
    freshness = max(0.0, 100.0 - days_elapsed * decay)
    return round(freshness, 1)


def compute_expiry(
    category: str,
    storage: str,
    purchase_date: Optional[date] = None,
    added_date: Optional[date] = None,
    item_name: Optional[str] = None,
) -> tuple[Optional[date], Optional[int]]:
    """
    Compute the estimated expiry date and days remaining for a food item.

    Uses the decay rate to determine when freshness reaches 0 (inedible).
    Returns (expires_on_date, days_remaining) or (None, None) for non-decaying items.
    """
    decay = get_decay_rate(category, storage, item_name)
    if decay <= 0:
        return None, None  # non-perishable / negligible decay

    age_reference = purchase_date if purchase_date else (added_date if added_date else date.today())

    # Total shelf life in days: freshness goes from 100 → 0 at `decay` points/day
    total_shelf_life_days = 100.0 / decay
    expires_on = age_reference + timedelta(days=total_shelf_life_days)

    days_remaining = (expires_on - date.today()).days
    days_remaining = max(0, days_remaining)

    return expires_on, days_remaining


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
    barcode: Optional[str] = None
    notes: Optional[str] = None
    price: Optional[float] = None
    visual_hazard: bool = False
    visual_verified: bool = False  # True if analyzed from photo/receipt, False if manually entered
    ai_freshness_score: Optional[float] = None


class PantryItemCreate(PantryItemBase):
    added_date: date = Field(default_factory=date.today)
    purchase_date: Optional[date] = None


class PantryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    storage: Optional[StorageLocation] = None
    is_perishable: Optional[bool] = None
    notes: Optional[str] = None
    price: Optional[float] = None
    visual_hazard: Optional[bool] = None
    visual_verified: Optional[bool] = None
    ai_freshness_score: Optional[float] = None


class PantryItem(PantryItemBase):
    id: str
    user_id: str
    added_date: date
    purchase_date: Optional[date] = None
    freshness_score: float = 100.0
    freshness_status: FreshnessCategory = FreshnessCategory.GOOD
    visual_hazard: bool = False
    visual_verified: bool = False
    expires_on: Optional[date] = None
    days_remaining: Optional[int] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: dict) -> PantryItem:
        storage = row.get("storage", "fridge")
        category = row.get("category", "other")
        item_name = row.get("name", "")
        added = row.get("added_date", str(date.today()))
        if isinstance(added, str):
            added = date.fromisoformat(added)

        # Parse purchase_date if provided
        purchase = row.get("purchase_date")
        if purchase and isinstance(purchase, str):
            purchase = date.fromisoformat(purchase)

        is_perishable = row.get("is_perishable", True)

        # Use AI freshness score if available, otherwise compute standard decay
        if row.get("ai_freshness_score") is not None:
            score = float(row["ai_freshness_score"])
        else:
            score = compute_freshness(added, category, storage, purchase, item_name) if is_perishable else 100.0

        visual_hazard = row.get("visual_hazard", False)
        
        # Hard cap freshness to zero for chemically/visually hazardous ingredients
        if visual_hazard:
            score = 0.0

        # Compute expiry date (also using FoodKeeper-aware decay)
        exp_date, days_left = compute_expiry(category, storage, purchase, added, item_name) if is_perishable else (None, None)

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
            purchase_date=purchase,
            visual_hazard=visual_hazard,
            visual_verified=row.get("visual_verified", False),
            ai_freshness_score=row.get("ai_freshness_score"),
            freshness_score=score,
            freshness_status=freshness_category(score),
            expires_on=exp_date,
            days_remaining=days_left,
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