from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from typing import Any

import pytesseract
from PIL import Image, ImageOps

NON_FOOD_KEYWORDS = {
    "tax", "total", "subtotal", "change", "cash", "visa", "mastercard", "card", "payment",
    "coupon", "discount", "save", "bag", "bags", "bottle deposit", "deposit", "fee", "balance",
    "auth", "merchant", "expiry", "visit", "points", "image id", "comments", "www", ".com",
    "receipt", "terminal", "till", "seq", "code", "pan", "contactless", "approved",
    "fresh", "my pantry",
    "includes", "points", "earned", "reward", "loyalty", "subtotal",
}

# Categories listed in priority order — first matching category wins.
# Keep dairy before fruit so "yogurt berry" resolves to dairy, not fruit.
CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "dairy": {"milk", "cheese", "yogurt", "yoghurt", "yog", "butter", "cream", "almond milk"},
    "eggs": {"egg", "eggs"},
    "meat": {"beef", "chicken", "pork", "turkey", "bacon", "ham", "sausage", "mince", "steak"},
    "seafood": {"salmon", "tuna", "shrimp", "fish", "cod", "tilapia"},
    "fruit": {"apple", "banana", "orange", "grape", "berry", "avocado", "lemon", "lime", "mandarin", "citrus", "grapefruit", "tangerine"},
    "vegetable": {"lettuce", "spinach", "tomato", "onion", "carrot", "broccoli", "pepper", "cucumber"},
    "bread": {"bread", "bagel", "bun", "tortilla"},
    "condiment": {"ketchup", "mustard", "mayo", "sauce", "dressing"},
    "canned": {"canned", "beans", "soup", "tinned"},
    "dry_goods": {"rice", "pasta", "penne", "spaghetti", "flour", "oats", "oat", "cereal", "lentil", "noodle"},
    "beverage": {"juice", "soda", "water", "coffee", "tea", "uht"},
    "frozen": {"frozen"},
}

NON_PERISHABLE_CATEGORIES = {"canned", "dry_goods", "condiment"}
DATE_PATTERNS = [r"\b(\d{4}-\d{2}-\d{2})\b", r"\b(\d{2}/\d{2}/\d{2,4})\b", r"\b(\d{2}/\d{2}/\d{2})\b"]
MIN_FOOD_CONFIDENCE = 2
KNOWN_FOOD_TERMS = {term for keywords in CATEGORY_KEYWORDS.values() for term in keywords}


def _tokenize(line: str) -> list[str]:
    return [tok for tok in re.split(r"\s+", line.lower()) if tok]


def _food_confidence(line: str) -> int:
    score = 0
    lowered = line.lower()
    for keywords in CATEGORY_KEYWORDS.values():
        for keyword in keywords:
            if keyword in lowered:
                score += 2
    if re.search(r"\b(kg|g|lb|oz|ml|l|pack|pk|ct|x)\b", lowered):
        score += 1
    if re.search(r"\d+\.\d{2}$", lowered):
        score += 1
    # Short product-like names are common on receipts, e.g. "H Milk".
    alpha_tokens = re.findall(r"[a-z]+", lowered)
    if any(token in KNOWN_FOOD_TERMS for token in alpha_tokens):
        score += 1
    elif len(alpha_tokens) == 1 and len(alpha_tokens[0]) >= 5:
        score += 1
    return score


def _looks_like_item_name(line: str) -> bool:
    lowered = line.lower().strip()
    alpha_tokens = re.findall(r"[a-z]+", lowered)
    if not alpha_tokens:
        return False

    # Reject single-letter OCR fragments (e.g. "7 A")
    if max(len(token) for token in alpha_tokens) < 2:
        return False

    # For one-word names, require either a known food term or at least 5 letters.
    if len(alpha_tokens) == 1:
        token = alpha_tokens[0]
        if token not in KNOWN_FOOD_TERMS and len(token) < 5:
            return False

    return True


def _clean_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    line = re.sub(r"[^\w\s\-./]", "", line)
    return line


def _looks_like_non_food(line: str) -> bool:
    lower = line.lower()
    if any(token in lower for token in NON_FOOD_KEYWORDS):
        return True
    if "http" in lower or "www." in lower or ".com" in lower:
        return True
    return False


# Abbreviation expansions for cleaner item names
ABBREVIATION_MAP = {
    "yog": "yogurt",
    "bberry": "blueberry",
    "berry": "berry",
    "imp": "imported",
    "uht": "",  # ultra-high-temp — typically just prefix for milk, drop it
    "cav": "cavolo",
    "barn": "",  # brand name, drop it
    "org": "organic",
    "conv": "conventional",
}


def _clean_item_name(name: str) -> str:
    """Clean OCR/receipt item names: expand abbreviations, remove size, standardize format."""
    cleaned = name.strip()
    
    # Remove trailing size/unit info (e.g. "1L", "350G", "/Kg", "x 12")
    cleaned = re.sub(r"\s*[\d.]+\s*(?:ml|l|g|kg|oz|lb|item|items|pack|x)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*/\s*[a-z]+\s*$", "", cleaned, flags=re.IGNORECASE)
    
    # Split into tokens and expand abbreviations
    tokens = cleaned.split()
    expanded = []
    for token in tokens:
        lower = token.lower()
        # Check if token matches an abbreviation
        if lower in ABBREVIATION_MAP:
            expanded_token = ABBREVIATION_MAP[lower]
            if expanded_token:  # don't add empty expansions
                expanded.append(expanded_token.title())
        else:
            expanded.append(token)
    
    cleaned = " ".join(expanded).strip()
    
    # Remove consecutive duplicate words (e.g. "Milk Milk" → "Milk")
    words = cleaned.split()
    deduped = []
    for word in words:
        if not deduped or word.lower() != deduped[-1].lower():
            deduped.append(word)
    cleaned = " ".join(deduped)
    
    return cleaned if cleaned else name




def _parse_quantity(line: str) -> tuple[float, str]:
    # Parse only explicit quantity formats to avoid reading dates/codes as quantity.
    lowered = line.lower()
    patterns = (
        r"^\s*(\d+(?:\.\d+)?)\s*x\s+",
        r"\bx\s*(\d+(?:\.\d+)?)\b",
        r"\b(\d+(?:\.\d+)?)\s*(?:ct|pk|pack)\b",
    )
    for pattern in patterns:
        qty_match = re.search(pattern, lowered)
        if not qty_match:
            continue
        value = float(qty_match.group(1))
        if 0 < value < 100:
            return value, "item"
    return 1.0, "item"


# Pre-compile word-boundary patterns for each keyword to avoid substring false-matches
# e.g. "roll" must not match "rolled", "can" must not match "Canterbury".
_CATEGORY_PATTERNS: list[tuple[str, list[re.Pattern]]] = [
    (cat, [re.compile(r"\b" + re.escape(kw) + r"\b") for kw in keywords])
    for cat, keywords in CATEGORY_KEYWORDS.items()
]


def _infer_category(name: str) -> str:
    lowered = name.lower()
    for category, patterns in _CATEGORY_PATTERNS:
        if any(p.search(lowered) for p in patterns):
            return category
    return "other"


def _extract_date(text: str) -> str:
    for pattern in DATE_PATTERNS:
        found = re.search(pattern, text)
        if not found:
            continue
        raw = found.group(1)
        if "-" in raw and len(raw) == 10:
            return raw
        # Try formats: MM/DD/YYYY, MM/DD/YY, then YY/MM/DD
        for fmt in ("%m/%d/%Y", "%m/%d/%y", "%y/%m/%d"):
            try:
                parsed = datetime.strptime(raw, fmt)
                # For 2-digit years, if year > current year, assume 19xx; otherwise 20xx
                if parsed.year > 2026:
                    parsed = parsed.replace(year=parsed.year - 100)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return ""


def _extract_store_name(lines: list[str]) -> str:
    for line in lines[:5]:
        candidate = _clean_line(line)
        if len(candidate) >= 3 and not re.search(r"\d", candidate):
            return candidate.title()
    return ""


def _extract_items(lines: list[str], store_name: str = "", relaxed: bool = False) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    store_name_lower = store_name.lower().strip()

    for raw in lines:
        line = _clean_line(raw)
        if not line or len(line) < 3:
            continue
        if store_name_lower and line.lower() == store_name_lower:
            continue
        if _looks_like_non_food(line):
            continue

        tokens = _tokenize(line)
        if not tokens:
            continue

        # Reject weight-price metadata lines (e.g., "165Kg Net 2.49 /Kg")
        if re.search(r"Net\s+\d+\.\d{2}\s+/Kg", line, re.IGNORECASE):
            continue

        # Ignore lines that are mostly numeric values or codes.
        if re.fullmatch(r"[\d\s./\-]+", line):
            continue

        # Skip very long narrative or survey/footer lines unlikely to be product names.
        if len(tokens) > 5 and _food_confidence(line) < 2:
            continue

        # Remove trailing prices like "3.99" or "12.49 A"
        line = re.sub(r"\s+\d+\.\d{2}(?:\s+[A-Z])?$", "", line)
        line = re.sub(r"\b[a-zA-Z]*\d{5,}[a-zA-Z0-9]*\b", "", line)  # remove long mixed OCR codes
        line = re.sub(r"\b\d{4,}\b", "", line)  # remove long product codes
        line = _clean_line(line)
        if len(line) < 3:
            continue
        if not _looks_like_item_name(line):
            continue

        # Require at least weak food confidence to keep OCR noise out of pantry.
        min_conf = 0 if relaxed else MIN_FOOD_CONFIDENCE
        if _food_confidence(line) < min_conf:
            continue

        qty, unit = _parse_quantity(line)
        category = _infer_category(line)
        clean_name = _clean_item_name(line)
        items.append(
            {
                "name": clean_name,
                "category": category,
                "quantity": qty,
                "unit": unit,
                "is_perishable": category not in NON_PERISHABLE_CATEGORIES,
            }
        )

    # Deduplicate by name while keeping first occurrence.
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = item["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _ocr_text(image_bytes: bytes) -> str:
    image = Image.open(BytesIO(image_bytes)).convert("L")
    image = ImageOps.autocontrast(image)
    return pytesseract.image_to_string(image)


async def analyze_receipt_photo(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict[str, Any]:
    del mime_type  # OCR fallback only relies on image bytes.

    try:
        text = _ocr_text(image_bytes)
    except Exception as exc:
        return {
            "error": (
                "Fallback receipt OCR failed. Ensure Tesseract is installed and available on PATH. "
                f"Details: {exc}"
            )
        }

    lines = [line for line in text.splitlines() if line.strip()]
    store_name = _extract_store_name(lines)
    items = _extract_items(lines, store_name=store_name, relaxed=False)

    # If strict parsing returns nothing, try a looser extraction before giving up.
    if not items:
        items = _extract_items(lines, store_name=store_name, relaxed=True)

    if not items:
        return {
            "items": [],
            "store_name": store_name,
            "date": _extract_date(text),
            "description": "",
        }

    return {
        "items": items,
        "store_name": store_name,
        "date": _extract_date(text),
        "description": "",
    }
