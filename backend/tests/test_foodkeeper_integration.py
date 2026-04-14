"""
Tests for USDA FoodKeeper integration.

Verifies that:
  1. FoodKeeper data loads successfully
  2. Product matching works for common food items
  3. Shelf-life values are reasonable per USDA guidelines
  4. Decay rates integrate correctly into compute_freshness / compute_expiry
  5. Backward compatibility: omitting item_name produces identical results
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta

from app.models.inventory import (
    compute_freshness,
    compute_expiry,
    get_decay_rate,
    FRESHNESS_DECAY_RATES,
    PantryItem,
)
from app.services.foodkeeper_service import (
    find_product,
    get_foodkeeper_shelf_life,
    get_foodkeeper_decay_rate,
    get_foodkeeper_info,
)


# ---------------------------------------------------------------------------
# 1. Data loading
# ---------------------------------------------------------------------------
def test_foodkeeper_data_loads():
    """FoodKeeper dataset loads and contains products."""
    product = find_product("butter")
    assert product is not None
    assert product["name"].strip().lower() == "butter"


# ---------------------------------------------------------------------------
# 2. Product matching
# ---------------------------------------------------------------------------
class TestProductMatching:
    def test_exact_match(self):
        p = find_product("Butter")
        assert p is not None and p["name"].strip() == "Butter"

    def test_case_insensitive(self):
        p = find_product("YOGURT")
        assert p is not None and "yogurt" in p["name"].lower()

    def test_depluralization(self):
        """'apple' should match 'Apples'."""
        p = find_product("apple")
        assert p is not None and "apple" in p["name"].lower()

    def test_multi_word(self):
        """'ground beef' should match 'Beef (ground)'."""
        p = find_product("ground beef")
        assert p is not None and "beef" in p["name"].lower()

    def test_keyword_match(self):
        """'salmon' should match 'Fatty fish' via keywords."""
        p = find_product("salmon")
        assert p is not None
        assert "fish" in p["name"].lower() or "salmon" in (p.get("keywords") or "").lower()

    def test_no_false_positive_for_garbage(self):
        """Completely unrelated strings should return None."""
        p = find_product("xyz_not_a_food_12345")
        assert p is None

    def test_milk_matches_dairy(self):
        """'milk' should match the Dairy Products entry, not Shelf Stable."""
        p = find_product("milk")
        assert p is not None
        assert p["category_name"] == "Dairy Products & Eggs"


# ---------------------------------------------------------------------------
# 3. Shelf-life reasonableness
# ---------------------------------------------------------------------------
class TestShelfLife:
    def test_butter_fridge(self):
        days = get_foodkeeper_shelf_life("butter", "fridge")
        assert days is not None
        assert 30 <= days <= 90  # USDA: 1-2 months

    def test_eggs_fridge(self):
        days = get_foodkeeper_shelf_life("eggs", "fridge")
        assert days is not None
        assert 21 <= days <= 42  # USDA: 3-5 weeks

    def test_chicken_fridge(self):
        days = get_foodkeeper_shelf_life("chicken", "fridge")
        assert days is not None
        assert 1 <= days <= 3  # USDA: 1-2 days

    def test_ground_beef_freezer(self):
        days = get_foodkeeper_shelf_life("ground beef", "freezer")
        assert days is not None
        assert 90 <= days <= 150  # USDA: 3-4 months

    def test_pasta_pantry(self):
        days = get_foodkeeper_shelf_life("pasta", "pantry")
        assert days is not None
        assert 365 <= days <= 730  # USDA: 1-2 years

    def test_no_data_returns_none(self):
        """Unknown item returns None, not an error."""
        days = get_foodkeeper_shelf_life("unknown_xyz_item", "fridge")
        assert days is None


# ---------------------------------------------------------------------------
# 4. Decay rate integration
# ---------------------------------------------------------------------------
class TestDecayRateIntegration:
    def test_foodkeeper_rate_differs_from_category(self):
        """FoodKeeper should produce a different rate for specific items."""
        fk_rate = get_decay_rate("dairy", "fridge", "butter")
        cat_rate = get_decay_rate("dairy", "fridge")
        # Butter specifically has a longer shelf life than generic dairy
        assert fk_rate != cat_rate
        assert fk_rate < cat_rate  # butter lasts longer than "average dairy"

    def test_unknown_item_falls_back_to_category(self):
        """When FoodKeeper has no match, category rate is used."""
        fk_rate = get_decay_rate("meat", "fridge", "unknown_xyz_meat")
        cat_rate = get_decay_rate("meat", "fridge")
        assert fk_rate == cat_rate

    def test_compute_freshness_with_item_name(self):
        """compute_freshness should use FoodKeeper rate when item_name is given."""
        d = date.today() - timedelta(days=5)
        score_fk = compute_freshness(d, "dairy", "fridge", item_name="butter")
        score_cat = compute_freshness(d, "dairy", "fridge")
        # Butter (FoodKeeper: ~60 day shelf life) decays much slower than generic dairy (7 days)
        assert score_fk > score_cat

    def test_compute_expiry_with_item_name(self):
        """compute_expiry should use FoodKeeper rate when item_name is given."""
        d = date.today()
        exp_fk, days_fk = compute_expiry("dairy", "fridge", d, item_name="butter")
        exp_cat, days_cat = compute_expiry("dairy", "fridge", d)
        assert exp_fk is not None and exp_cat is not None
        assert days_fk > days_cat  # butter expires much later than generic dairy


# ---------------------------------------------------------------------------
# 5. Backward compatibility
# ---------------------------------------------------------------------------
class TestBackwardCompatibility:
    def test_get_decay_rate_no_item_name(self):
        """get_decay_rate without item_name returns the original category rate."""
        rate = get_decay_rate("dairy", "fridge")
        expected = FRESHNESS_DECAY_RATES["dairy"]["fridge"]
        assert rate == expected

    def test_compute_freshness_no_item_name(self):
        """compute_freshness without item_name is unchanged."""
        d = date.today() - timedelta(days=3)
        score = compute_freshness(d, "dairy", "fridge")
        expected = max(0.0, 100.0 - 3 * FRESHNESS_DECAY_RATES["dairy"]["fridge"])
        assert abs(score - round(expected, 1)) < 0.1

    def test_pantry_item_from_db_row(self):
        """PantryItem.from_db_row still works with the name field."""
        row = {
            "id": "test-123",
            "user_id": "user-1",
            "name": "Butter",
            "category": "dairy",
            "storage": "fridge",
            "added_date": str(date.today() - timedelta(days=7)),
            "quantity": 1,
        }
        item = PantryItem.from_db_row(row)
        assert item.freshness_score > 0
        assert item.freshness_score <= 100
        assert item.expires_on is not None


# ---------------------------------------------------------------------------
# 6. FoodKeeper info API
# ---------------------------------------------------------------------------
class TestFoodKeeperInfo:
    def test_info_returns_data(self):
        info = get_foodkeeper_info("butter")
        assert info is not None
        assert info["matched_product"] == "Butter"
        assert "fridge" in info["shelf_life"] or "freezer" in info["shelf_life"]

    def test_info_returns_none_for_unknown(self):
        info = get_foodkeeper_info("xyz_unknown")
        assert info is None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
