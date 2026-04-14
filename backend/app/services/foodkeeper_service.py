"""
USDA FoodKeeper Lookup Service
===============================
Provides item-specific shelf-life data from the USDA FoodKeeper dataset
(661 products).  This replaces generic category-based decay rates with
precise per-product shelf-life windows backed by federal food-safety data.

Lookup strategy (in order of specificity):
  1. **Exact name match** — item name matches a FoodKeeper product name
  2. **Keyword match** — any token in the item name appears in a product's
     keyword list (scored by overlap ratio)
  3. **Fuzzy match** — Levenshtein-like similarity on product names (≥ 0.6)
  4. **Fallback** — return None → caller uses the legacy category-based rate

The service converts FoodKeeper's metric (Days / Weeks / Months / Years)
and min/max range into a single **shelf-life in days** using the *maximum*
value (optimistic but still USDA-safe).

Storage mapping
---------------
  FoodKeeper field prefix  → app StorageLocation
  Refrigerate_*            → fridge
  Freeze_*                 → freezer
  Pantry_*                 → pantry   (also used for counter)

DOP = "Date of Purchase" variants — preferred when available since they
align with how Pantry Pulse tracks items (from purchase date, not
manufacture date).
"""

from __future__ import annotations

import json
import logging
import os
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Text normalisation helpers (needed by both _load_data and matching)
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Lower-case, strip punctuation, collapse whitespace."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _depluralize(word: str) -> str:
    """Cheap English depluralization for food matching."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"       # berries -> berry
    if word.endswith("ves") and len(word) > 4:
        return word[:-3] + "f"       # loaves -> loaf
    if word.endswith("es") and len(word) > 3:
        return word[:-2]             # tomatoes -> tomato
    if word.endswith("s") and len(word) > 2 and not word.endswith("ss"):
        return word[:-1]             # apples -> apple
    return word


def _token_variants(word: str) -> set[str]:
    """Return a word and its depluralized form."""
    variants = {word}
    dep = _depluralize(word)
    if dep != word:
        variants.add(dep)
    # Also add a simple pluralized form
    variants.add(word + "s")
    return variants


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "foodkeeper_data.json"

_products: list[dict] = []
_keyword_index: dict[str, list[int]] = {}   # keyword → list of product indices
_name_index: dict[str, int] = {}            # lowercase product name → index


def _load_data() -> None:
    """Load preprocessed FoodKeeper JSON and build search indices."""
    global _products, _keyword_index, _name_index

    if _products:
        return  # already loaded

    if not _DATA_PATH.exists():
        logger.warning("FoodKeeper data file not found at %s", _DATA_PATH)
        return

    with open(_DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    _products = raw.get("products", [])
    logger.info("Loaded %d FoodKeeper products", len(_products))

    # Build indices
    for idx, product in enumerate(_products):
        # Name index (exact lowercase) — first product wins for duplicate names
        name_lower = (product.get("name") or "").strip().lower()
        if name_lower:
            _name_index.setdefault(name_lower, idx)

            # Also index depluralized name variant
            name_dep = " ".join(_depluralize(t) for t in name_lower.split())
            if name_dep != name_lower:
                _name_index.setdefault(name_dep, idx)

            # Also index "name, subtitle" variant
            subtitle = (product.get("name_subtitle") or "").strip().lower()
            if subtitle:
                _name_index.setdefault(f"{name_lower}, {subtitle}", idx)
                _name_index.setdefault(f"{name_lower} {subtitle}", idx)

        # Keyword index
        keywords_raw = product.get("keywords") or ""
        for kw in keywords_raw.split(","):
            kw_clean = kw.strip().lower()
            if kw_clean and len(kw_clean) > 1:
                _keyword_index.setdefault(kw_clean, []).append(idx)
                # Also index depluralized keyword
                kw_dep = _depluralize(kw_clean)
                if kw_dep != kw_clean:
                    _keyword_index.setdefault(kw_dep, []).append(idx)


# ---------------------------------------------------------------------------
# Metric → days conversion
# ---------------------------------------------------------------------------
_METRIC_TO_DAYS: dict[str, float] = {
    "days":   1.0,
    "hours":  1.0 / 24.0,
    "weeks":  7.0,
    "months": 30.0,
    "years":  365.0,
    "year":   365.0,
}

# Metrics that indicate "don't store here" or "use package date"
_NON_NUMERIC_METRICS = {
    "not recommended",
    "package use-by date",
    "when ripe",
    "indefinitely",
}


def _metric_to_days(value: Optional[float], metric: Optional[str]) -> Optional[float]:
    """Convert a FoodKeeper min/max value + metric into days."""
    if value is None or metric is None:
        return None
    metric_lower = metric.strip().lower()
    if metric_lower in _NON_NUMERIC_METRICS:
        return None
    multiplier = _METRIC_TO_DAYS.get(metric_lower)
    if multiplier is None:
        logger.debug("Unknown FoodKeeper metric: %s", metric)
        return None
    return value * multiplier


# ---------------------------------------------------------------------------
# Shelf-life extraction per storage type
# ---------------------------------------------------------------------------

def _extract_shelf_life_days(product: dict, storage: str) -> Optional[float]:
    """
    Extract shelf-life in days for a product at the given storage location.

    Priority:
      1. DOP (Date of Purchase) variant — matches Pantry Pulse's tracking model
      2. After-opening variant — more conservative
      3. General variant
    Returns the *max* value (USDA upper bound) in days, or None if unavailable.
    """
    if storage in ("fridge", "counter"):
        prefixes = [
            # DOP variants first (most aligned with our model)
            ("dop_refrigerate_min", "dop_refrigerate_max", "dop_refrigerate_metric"),
            # After-opening (conservative)
            ("refrigerate_after_opening_min", "refrigerate_after_opening_max", "refrigerate_after_opening_metric"),
            # General refrigerate
            ("refrigerate_min", "refrigerate_max", "refrigerate_metric"),
        ]
        # For counter storage, also check pantry fields
        if storage == "counter":
            prefixes = [
                ("dop_pantry_min", "dop_pantry_max", "dop_pantry_metric"),
                ("pantry_after_opening_min", "pantry_after_opening_max", "pantry_after_opening_metric"),
                ("pantry_min", "pantry_max", "pantry_metric"),
            ] + prefixes  # fall back to fridge data for counter
    elif storage == "freezer":
        prefixes = [
            ("dop_freeze_min", "dop_freeze_max", "dop_freeze_metric"),
            ("freeze_min", "freeze_max", "freeze_metric"),
        ]
    elif storage == "pantry":
        prefixes = [
            ("dop_pantry_min", "dop_pantry_max", "dop_pantry_metric"),
            ("pantry_after_opening_min", "pantry_after_opening_max", "pantry_after_opening_metric"),
            ("pantry_min", "pantry_max", "pantry_metric"),
        ]
    else:
        return None

    for min_key, max_key, metric_key in prefixes:
        metric = product.get(metric_key)
        if not metric:
            continue
        metric_lower = metric.strip().lower()
        if metric_lower in _NON_NUMERIC_METRICS:
            if metric_lower == "indefinitely":
                return 3650.0  # ~10 years — effectively non-perishable
            continue  # skip "not recommended", "package use-by date", etc.

        max_val = product.get(max_key)
        min_val = product.get(min_key)
        # Prefer max (USDA upper bound), fall back to min
        value = max_val if max_val is not None else min_val
        days = _metric_to_days(value, metric)
        if days is not None and days > 0:
            return days

    return None


# ---------------------------------------------------------------------------
# Product matching
# ---------------------------------------------------------------------------

def _score_keyword_match(item_tokens: set[str], product: dict) -> float:
    """
    Score 0-1 based on token overlap with product keywords.
    Handles pluralization and prefers whole-word matches.
    """
    keywords_raw = (product.get("keywords") or "").lower()
    product_kw_tokens = {t.strip() for t in keywords_raw.split(",") if t.strip()}
    product_name = _normalise(product.get("name") or "")
    product_name_tokens = set(product_name.split())
    all_product_tokens = product_kw_tokens | product_name_tokens

    if not all_product_tokens or not item_tokens:
        return 0.0

    # Build expanded sets with singular/plural variants
    item_expanded: set[str] = set()
    for t in item_tokens:
        item_expanded.update(_token_variants(t))

    product_expanded: set[str] = set()
    for t in all_product_tokens:
        product_expanded.update(_token_variants(t))

    # Direct overlap (including depluralized/pluralized forms)
    overlap = item_expanded & product_expanded
    if not overlap:
        return 0.0

    # Score is based on how many of the original item tokens matched
    matched_item_tokens = 0
    for it in item_tokens:
        variants = _token_variants(it)
        if variants & product_expanded:
            matched_item_tokens += 1

    score = matched_item_tokens / max(len(item_tokens), 1)

    # Bonus: if the product name is an exact (depluralized) match, boost heavily
    item_norm = " ".join(sorted(item_tokens))
    prod_norm = " ".join(sorted(product_name_tokens))
    if item_norm == prod_norm:
        score = 1.0
    # Also check depluralized product name match
    prod_dep_tokens = {_depluralize(t) for t in product_name_tokens}
    item_dep_tokens = {_depluralize(t) for t in item_tokens}
    if item_dep_tokens == prod_dep_tokens:
        score = max(score, 0.95)

    return min(1.0, score)


def _fuzzy_score(a: str, b: str) -> float:
    """SequenceMatcher ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def find_product(item_name: str) -> Optional[dict]:
    """
    Find the best-matching FoodKeeper product for an item name.

    Returns the product dict or None if no confident match found.
    """
    _load_data()
    if not _products:
        return None

    normalised = _normalise(item_name)
    if not normalised:
        return None

    # 1. Exact name match (including depluralized)
    if normalised in _name_index:
        return _products[_name_index[normalised]]

    # Try depluralized form
    dep_name = " ".join(_depluralize(t) for t in normalised.split())
    if dep_name in _name_index:
        return _products[_name_index[dep_name]]

    # Try pluralized form
    plural_name = normalised + "s"
    if plural_name in _name_index:
        return _products[_name_index[plural_name]]

    # 2. Keyword-based scoring with depluralization
    item_tokens = set(normalised.split())
    item_token_variants: set[str] = set()
    for t in item_tokens:
        item_token_variants.update(_token_variants(t))

    # Gather candidate product indices from keyword index
    candidate_indices: set[int] = set()
    for variant in item_token_variants:
        if variant in _keyword_index:
            candidate_indices.update(_keyword_index[variant])

    best_kw_score = 0.0
    best_kw_idx: Optional[int] = None
    best_kw_name_len = 999

    for idx in candidate_indices:
        score = _score_keyword_match(item_tokens, _products[idx])
        # Penalize products whose name is much longer (avoids "apple" -> "apple cider vinegar")
        prod_name = _normalise(_products[idx].get("name") or "")
        prod_name_len = len(prod_name.split())
        item_len = len(item_tokens)
        if prod_name_len > item_len * 2:
            score *= 0.6  # penalize multi-word names for single-word queries

        # Tiebreaker: prefer shorter product names (more direct match)
        # and lower indices (more common products listed first)
        is_better = (
            score > best_kw_score
            or (score == best_kw_score and prod_name_len < best_kw_name_len)
            or (score == best_kw_score and prod_name_len == best_kw_name_len and (best_kw_idx is None or idx < best_kw_idx))
        )
        if is_better:
            best_kw_score = score
            best_kw_idx = idx
            best_kw_name_len = prod_name_len

    if best_kw_score >= 0.5 and best_kw_idx is not None:
        return _products[best_kw_idx]

    # 3. Fuzzy match on product names (only if keyword search found nothing)
    best_fuzzy = 0.0
    best_fuzzy_idx: Optional[int] = None
    for idx, product in enumerate(_products):
        pname = _normalise(product.get("name") or "")
        score = _fuzzy_score(normalised, pname)
        # Also try depluralized fuzzy
        pname_dep = " ".join(_depluralize(t) for t in pname.split())
        score = max(score, _fuzzy_score(dep_name, pname_dep))
        if score > best_fuzzy:
            best_fuzzy = score
            best_fuzzy_idx = idx

    if best_fuzzy >= 0.6 and best_fuzzy_idx is not None:
        return _products[best_fuzzy_idx]

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@lru_cache(maxsize=2048)
def get_foodkeeper_shelf_life(item_name: str, storage: str) -> Optional[float]:
    """
    Look up USDA FoodKeeper shelf-life for an item in days.

    Parameters
    ----------
    item_name : str  — the food item name (e.g. "chicken breast", "milk", "butter")
    storage   : str  — storage location: fridge / freezer / pantry / counter

    Returns
    -------
    float — shelf life in days, or None if no match found.
    """
    product = find_product(item_name)
    if product is None:
        return None

    days = _extract_shelf_life_days(product, storage)
    if days is not None:
        logger.debug(
            "FoodKeeper match: '%s' → '%s' (%s) = %.1f days",
            item_name,
            product.get("name"),
            storage,
            days,
        )
    return days


def get_foodkeeper_decay_rate(item_name: str, storage: str) -> Optional[float]:
    """
    Compute a decay rate (points/day) from FoodKeeper shelf-life data.

    decay_rate = 100.0 / shelf_life_days

    This is a drop-in replacement for the category-based rates in
    FRESHNESS_DECAY_RATES.  Returns None if no FoodKeeper match found
    (caller should fall back to category rate).
    """
    days = get_foodkeeper_shelf_life(item_name, storage)
    if days is None or days <= 0:
        return None
    return round(100.0 / days, 4)


def get_foodkeeper_info(item_name: str) -> Optional[dict]:
    """
    Return full FoodKeeper product info for an item, including all
    storage-specific shelf-life data and tips.  Useful for the frontend
    to display USDA-sourced guidance.
    """
    _load_data()
    product = find_product(item_name)
    if product is None:
        return None

    result = {
        "matched_product": product.get("name"),
        "subtitle": product.get("name_subtitle"),
        "usda_category": product.get("category_name"),
        "shelf_life": {},
        "tips": {},
    }

    for storage in ("fridge", "freezer", "pantry", "counter"):
        days = _extract_shelf_life_days(product, storage)
        if days is not None:
            result["shelf_life"][storage] = {
                "days": round(days, 1),
                "decay_rate": round(100.0 / days, 4) if days > 0 else None,
            }

    # Collect tips
    for tip_key in ("pantry_tips", "refrigerate_tips", "freeze_tips"):
        tip = product.get(tip_key)
        if tip:
            storage_name = tip_key.replace("_tips", "").replace("refrigerate", "fridge")
            result["tips"][storage_name] = tip

    return result
