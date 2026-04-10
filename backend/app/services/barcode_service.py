from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

OPEN_FOOD_FACTS_API = "https://world.openfoodfacts.net/api/v2/product"

CATEGORY_MAPPING = {
    "en:milks": "dairy",
    "en:cheeses": "dairy",
    "en:yogurts": "dairy",
    "en:butters": "dairy",
    "en:creams": "dairy",
    "en:meats": "meat",
    "en:poultry": "meat",
    "en:beef": "meat",
    "en:pork": "meat",
    "en:fishes": "seafood",
    "en:shrimps": "seafood",
    "en:fruits": "fruit",
    "en:vegetables": "vegetable",
    "en:breads": "bread",
    "en:eggs": "eggs",
    "en:canned-foods": "canned",
    "en:cereals": "dry_goods",
    "en:pastas": "dry_goods",
    "en:rices": "dry_goods",
    "en:beverages": "beverage",
    "en:waters": "beverage",
    "en:juices": "beverage",
    "en:frozen-foods": "frozen",
    "en:sauces": "condiment",
    "en:spices": "condiment",
}

PERISHABLE_CATEGORIES = {"dairy", "meat", "seafood", "fruit", "vegetable", "bread", "eggs", "leftover"}


def _map_category(categories_tags: list[str]) -> str:
    for tag in categories_tags:
        tag_lower = tag.lower()
        for key, value in CATEGORY_MAPPING.items():
            if key in tag_lower:
                return value
    return "other"


async def lookup_barcode(barcode: str) -> dict | None:
    """Look up a barcode using the free Open Food Facts API."""
    url = f"{OPEN_FOOD_FACTS_API}/{barcode}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers={"User-Agent": "FreshSave/1.0"})
            if response.status_code != 200:
                return None

            data = response.json()
            if data.get("status") != 1:
                return None

            product = data.get("product", {})
            name = product.get("product_name", "Unknown Item")
            categories_tags = product.get("categories_tags", [])
            category = _map_category(categories_tags)
            quantity_str = product.get("quantity", "1")

            return {
                "name": name,
                "category": category,
                "quantity": 1,
                "unit": "item",
                "is_perishable": category in PERISHABLE_CATEGORIES,
                "barcode": barcode,
                "brand": product.get("brands", ""),
                "image_url": product.get("image_url", ""),
                "quantity_label": quantity_str,
            }
    except Exception:
        logger.exception("Barcode lookup failed for %s", barcode)
        return None
