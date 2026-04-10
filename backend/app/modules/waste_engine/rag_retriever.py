"""
RAG (Retrieval-Augmented Generation) Retriever for Food Safety Knowledge

This module provides an interface to retrieve:
- Food safety guidelines (FDA/EFSA storage limits)
- Disposal protocols (Galway waste management)
- Donation/sharing resources
- Storage tips and best practices

Currently uses a mock in-memory retriever. Will integrate with:
- Pinecone/Supabase vector DB for semantic search
- Gemini for multi-modal reasoning over documents
"""

import json
from typing import Optional
from pathlib import Path


class RAGRetriever:
    """Base interface for RAG retrieval"""

    def get_category_safety_limit(self, category: str, storage: str) -> dict:
        """Retrieve max safe storage days for category + storage location"""
        raise NotImplementedError

    def get_safety_guidelines(self, category: str) -> str:
        """Get detailed safety guidelines for a food category"""
        raise NotImplementedError

    def get_storage_tips(self, category: str) -> str:
        """Get storage optimization tips"""
        raise NotImplementedError

    def get_donation_guidelines(self) -> str:
        """Get guidelines for donating food"""
        raise NotImplementedError

    def get_disposal_protocol(self, category: str) -> str:
        """Get Galway-specific waste disposal protocol"""
        raise NotImplementedError


class MockRAGRetriever(RAGRetriever):
    """
    Mock in-memory RAG retriever for development/testing.
    Uses hardcoded data from EFSA/FDA guidelines and Galway waste management.
    """

    # Food Safety Limits (EFSA/FDA guidelines)
    SAFETY_LIMITS = {
        "seafood": {"fridge": 2, "freezer": 180, "pantry": 0, "counter": 1},
        "meat": {"fridge": 4, "freezer": 180, "pantry": 0, "counter": 1},
        "poultry": {"fridge": 3, "freezer": 180, "pantry": 0, "counter": 1},
        "dairy": {"fridge": 7, "freezer": 90, "pantry": 0, "counter": 0},
        "eggs": {"fridge": 28, "freezer": 180, "pantry": 0, "counter": 0},
        "fruit": {"fridge": 7, "freezer": 180, "pantry": 30, "counter": 3},
        "vegetable": {"fridge": 10, "freezer": 180, "pantry": 30, "counter": 3},
        "bread": {"fridge": 7, "freezer": 180, "pantry": 5, "counter": 2},
        "leftover": {"fridge": 4, "freezer": 180, "pantry": 0, "counter": 0},
        "condiment": {"fridge": 180, "freezer": 365, "pantry": 365, "counter": 0},
        "canned": {"fridge": 0, "freezer": 0, "pantry": 730, "counter": 0},
        "dry_goods": {"fridge": 0, "freezer": 0, "pantry": 365, "counter": 0},
        "beverage": {"fridge": 14, "freezer": 365, "pantry": 365, "counter": 0},
        "frozen": {"fridge": 0, "freezer": 180, "pantry": 0, "counter": 0},
        "other": {"fridge": 7, "freezer": 180, "pantry": 30, "counter": 3},  # Default fallback
    }

    SAFETY_GUIDELINES = {
        "seafood": (
            "Seafood is highly perishable. Store at 0-4°C (32-40°F). Consume within 2 days "
            "of purchase. Watch for: strong fishy odor, slimy texture, discoloration. "
            "Freezing extends shelf life to 6 months."
        ),
        "meat": (
            "Raw meat lasts 4 days in the fridge, 6-9 months in freezer. Store on lowest shelf "
            "to prevent cross-contamination. Signs of spoilage: brown/gray color, slimy texture, "
            "sour smell. Ground meat spoils faster (1-2 days)."
        ),
        "poultry": (
            "Store at 0-4°C. Raw poultry lasts 1-2 days, cooked 3-4 days. Frozen lasts 6 months. "
            "Always thaw in fridge, never at room temperature. Check for greenish hue or off smell."
        ),
        "dairy": (
            "Most dairy lasts 7-10 days past purchase date if unopened. After opening, consume within "
            "3-5 days. Watch for sour smell, lumps, or mold. Cheese can last 2+ weeks if stored properly. "
            "Freezing extends life 3 months."
        ),
        "fruit": (
            "Store at room temperature until ripe, then refrigerate. Citrus lasts 2-4 weeks in fridge. "
            "Berries last 5-7 days. Bananas ripen at room temp, brown spots = perfect for baking. "
            "Mold on soft fruits = discard. Frozen fruit lasts 6 months."
        ),
        "vegetable": (
            "Most vegetables last 7-10 days in fridge crisper. Store in breathable bags. "
            "Leafy greens: 3-5 days. Root veggies: 2-3 weeks. Signs: wilting, sliminess, mold. "
            "Frozen vegetables last 8-12 months."
        ),
        "bread": (
            "Store at room temp 2-3 days, fridge 7+ days, freezer 6 months. Cut ends first to slow mold. "
            "Fresh bread goes moldy faster than packaged. Freezing preserves freshness. Signs: visible mold, "
            "hard/stale texture."
        ),
        "leftover": (
            "Store in airtight containers at 0-4°C. Consume within 3-4 days. Reheat to 74°C (165°F) "
            "for safety. When in doubt, throw it out. Frozen leftovers last 3-6 months."
        ),
    }

    STORAGE_TIPS = {
        "seafood": "Use ice packs or coldest part of fridge. Consider vacuum sealing for longer storage.",
        "meat": "Store on lowest shelf to prevent dripping on other foods. Use within 2-3 days or freeze immediately.",
        "dairy": "Store in coldest part of fridge (back, not door). Keep unopened until ready to use.",
        "fruit": "Ripen at room temp, move to fridge when ripe. Store away from ethylene-producing items (avocado, tomato).",
        "vegetable": "Store in crisper drawer with high humidity. Keep ethylene-sensitive items (carrots, broccoli) away from fruits.",
        "bread": "Store in cool, dry place. Freezing is best long-term. Thaw at room temp before eating.",
    }

    DISPOSAL_PROTOCOLS = {
        "seafood": (
            "Galway Waste Protocol: Raw seafood waste → BROWN BIN (food waste). "
            "Shells/bones if small → brown bin. Large shells → request special collection. "
            "Frozen seafood → thaw first, then brown bin."
        ),
        "meat": (
            "Galway Waste Protocol: Raw/cooked meat → BROWN BIN (food waste). "
            "Bones → can go in brown bin if small/crushed. Packaging (foam trays) → BLACK BIN (general waste). "
            "Large bones → request bulky waste collection."
        ),
        "dairy": (
            "Galway Waste Protocol: Spoiled milk/yogurt → Pour down drain (dilute), container → BLUE BIN (recycling). "
            "Cheese waste → BROWN BIN. Butter/cream → BROWN BIN. Milk cartons → rinse well, BLUE BIN."
        ),
        "fruit": (
            "Galway Waste Protocol: All fruit waste (fresh/rotten) → BROWN BIN (compostable). "
            "Peels, cores, seeds → brown bin. Packaging (labels, stickers) → remove before placing in bin. "
            "Moldy fruit → still safe for brown bin."
        ),
        "vegetable": (
            "Galway Waste Protocol: All vegetable waste → BROWN BIN (compostable). "
            "Peels, stems, leaves, roots → all brown bin. Plastic bags → BLUE BIN. "
            "Soil still attached → rinse gently before binning."
        ),
        "bread": (
            "Galway Waste Protocol: Stale/moldy bread → BROWN BIN (compostable). "
            "Bread bags (plastic) → BLUE BIN (recycling). Ties (metal/plastic) → BLACK BIN. "
            "Large quantities → contact Galway waste management for bulk collection."
        ),
        "leftover": (
            "Galway Waste Protocol: Any leftover food → BROWN BIN. Oil/grease → paper towel in BLACK BIN, "
            "NOT down drain (clogs pipes). Containers: plastic → BLUE BIN, glass → BLUE BIN, foil → BLACK BIN."
        ),
    }

    DONATION_GUIDELINES = (
        "Food Donation Guidelines (Galway):\n\n"
        "✓ SAFE TO DONATE:\n"
        "- Non-perishables: canned goods, dry goods, unopened packaged items\n"
        "- Fresh produce: if no visible mold/damage\n"
        "- Dairy: only if unopened and within expiration\n"
        "- Bread/baked goods: if fresh (no mold)\n\n"
        "✗ DO NOT DONATE:\n"
        "- Open/partially used items\n"
        "- Items past expiration date\n"
        "- Visibly moldy or spoiled items\n"
        "- Items in damaged packaging\n\n"
        "Local Galway Charities:\n"
        "- Galway Food Bank (supporting low-income families)\n"
        "- St. Vincent de Paul (community outreach)\n"
        "- Local community fridges (pop-up donation points)"
    )

    def get_category_safety_limit(self, category: str, storage: str) -> dict:
        """Get max safe storage days from EFSA/FDA guidelines"""
        category = category.lower()
        storage = storage.lower()

        limits = self.SAFETY_LIMITS.get(category, self.SAFETY_LIMITS["other"])
        max_days = limits.get(storage, 7)  # Conservative default

        return {
            "category": category,
            "storage": storage,
            "max_days": max_days,
            "source": "EFSA/FDA",
        }

    def get_safety_guidelines(self, category: str) -> str:
        """Get detailed safety info for category"""
        return self.SAFETY_GUIDELINES.get(
            category.lower(),
            f"General food safety: Store perishables at 0-4°C. Check for visible signs of spoilage before consuming.",
        )

    def get_storage_tips(self, category: str) -> str:
        """Get storage optimization tips"""
        return self.STORAGE_TIPS.get(
            category.lower(),
            "Store in a cool, dry place. Keep away from direct sunlight.",
        )

    def get_donation_guidelines(self) -> str:
        """Get food donation guidelines"""
        return self.DONATION_GUIDELINES

    def get_disposal_protocol(self, category: str) -> str:
        """Get Galway-specific waste management protocol"""
        return self.DISPOSAL_PROTOCOLS.get(
            category.lower(),
            f"Galway Waste Protocol: Most food waste → BROWN BIN (compostable). "
            f"Packaging → BLUE BIN (recyclable) or BLACK BIN (general waste). "
            f"Contact Galway waste management for special items.",
        )
