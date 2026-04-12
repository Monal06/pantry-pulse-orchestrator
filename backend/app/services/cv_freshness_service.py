"""
CV Freshness Service — OpenCV + scikit-image Computer Vision Pipeline
=====================================================================
Analyses food images in multiple colour spaces (HSV, LAB) to extract
objective visual freshness signals:

  • Saturation score      — vibrant colour = fresh
  • Brown/discoloration   — brown/dark patches = aging
  • Texture quality       — Laplacian variance (blurry/mushy = spoiled)
  • Brightness assessment — context-aware (yellow foods treated differently)
  • Mold region detection — green/white/black colour masks + morphological filter

Context-aware rules
-------------------
- Yellow foods (banana, lemon, corn, pepper): HIGH yellow/brightness is GOOD
  → suppress the "browning" penalty for yellow hues
- Green foods (broccoli, spinach, cucumber): vibrant green is GOOD
  → dark-green patches are NOT mold
- Dark foods (blueberry, aubergine, black bean): naturally dark
  → suppress darkness penalty

All functions return None (or a safe fallback dict) on any exception
so that the ensemble layer can skip this signal without crashing.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy imports — keep server startup fast; only pull in heavy libs on first call
# ---------------------------------------------------------------------------
_cv2 = None
_np = None


def _import_cv():
    """Lazy-import OpenCV + NumPy."""
    global _cv2, _np
    if _cv2 is not None:
        return True
    try:
        import cv2          # opencv-python-headless
        import numpy as np
        _cv2 = cv2
        _np = np
        logger.info("[CV-FRESHNESS] OpenCV + NumPy loaded successfully.")
        return True
    except ImportError as exc:
        logger.warning("[CV-FRESHNESS] Could not import CV libraries: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Context-aware food classification
# ---------------------------------------------------------------------------

# Foods whose natural colour is yellow/bright — don't penalise high yellow
NATURALLY_YELLOW = {
    "banana", "lemon", "corn", "yellow pepper", "yellow capsicum",
    "pineapple", "mango", "cantaloupe", "yellow squash", "butternut squash",
    "golden apple", "yellow onion",
}

# Foods whose natural colour is dark green
NATURALLY_DARK_GREEN = {
    "broccoli", "kale", "spinach", "avocado", "cucumber", "courgette",
    "zucchini", "peas", "green beans", "asparagus", "brussels sprouts",
}

# Foods that are naturally very dark
NATURALLY_DARK = {
    "blueberry", "blackberry", "aubergine", "eggplant", "black bean",
    "dark chocolate", "dates", "prune", "black olive", "beetroot",
}


def _classify_food_context(food_name: str) -> dict:
    """Return context flags that modify scoring thresholds."""
    name_lower = food_name.lower() if food_name else ""
    return {
        "is_naturally_yellow": any(y in name_lower for y in NATURALLY_YELLOW),
        "is_naturally_dark_green": any(g in name_lower for g in NATURALLY_DARK_GREEN),
        "is_naturally_dark": any(d in name_lower for d in NATURALLY_DARK),
    }


# ---------------------------------------------------------------------------
# Core image loading
# ---------------------------------------------------------------------------

def _bytes_to_bgr(image_bytes: bytes):
    """Decode raw image bytes to a BGR NumPy array."""
    np = _np
    cv2 = _cv2
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("cv2.imdecode returned None — invalid image bytes")
    return img


def _resize_for_analysis(img, max_dim: int = 512):
    """Resize to at most max_dim on the longest side (speed vs accuracy trade-off)."""
    cv2 = _cv2
    h, w = img.shape[:2]
    if max(h, w) <= max_dim:
        return img
    scale = max_dim / max(h, w)
    return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


# ---------------------------------------------------------------------------
# Individual metric extractors
# ---------------------------------------------------------------------------

def _saturation_score(hsv_img) -> float:
    """
    Mean saturation of the image (S channel of HSV, range 0-255).
    Fresh produce has vibrant, saturated colours.
    Returns 0-100 score (higher = fresher).
    """
    np = _np
    s_channel = hsv_img[:, :, 1].astype(np.float32)
    mean_s = float(np.mean(s_channel))
    # Map 0-255 → 0-100, but very low saturation (<30) is a spoilage hint
    score = min(100.0, (mean_s / 255.0) * 130)  # slight boost for vibrant foods
    return round(max(0.0, score), 1)


def _browning_ratio(hsv_img, bgr_img, context: dict) -> tuple[float, float]:
    """
    Detect brown/dark-discoloured pixels characteristic of oxidation and aging.
    Returns (browning_ratio_percent, score_0_to_100).

    Context-aware: yellow foods have overlapping hue range with brown/yellow —
    suppress penalty for naturally-yellow foods.
    """
    np = _np
    cv2 = _cv2

    h_ch = hsv_img[:, :, 0].astype(np.float32)   # 0-179 in OpenCV
    s_ch = hsv_img[:, :, 1].astype(np.float32)   # 0-255
    v_ch = hsv_img[:, :, 2].astype(np.float32)   # 0-255

    # Brown: hue ≈ 10-30 deg (OpenCV units: 5-15), low-moderate saturation,
    # moderate-low value.  Avoid catching vibrant orange/red fruits.
    brown_hue_mask = (h_ch >= 5) & (h_ch <= 18)
    brown_sat_mask = (s_ch >= 40) & (s_ch <= 180)
    brown_val_mask = (v_ch >= 30) & (v_ch <= 180)
    brown_mask = brown_hue_mask & brown_sat_mask & brown_val_mask

    # If the food is naturally yellow, the brown hue range overlaps heavily
    # with natural yellow hue (hue 20-35 in OpenCV ≈ 40-70 degrees).
    # Suppress the penalty by halving it.
    total_px = h_ch.size
    brown_px = int(np.sum(brown_mask))
    ratio = brown_px / total_px * 100.0  # as percentage

    if context.get("is_naturally_yellow"):
        ratio *= 0.35   # heavily suppress for yellow foods

    # Dark-patch penalty: very dark regions that aren't naturally dark foods
    if not context.get("is_naturally_dark"):
        dark_mask = (v_ch < 40) & (s_ch > 20)
        dark_ratio = float(np.sum(dark_mask)) / total_px * 100.0
        ratio = ratio + dark_ratio * 0.3  # partial contribution

    ratio = min(ratio, 100.0)
    # Score: 0% browning = 100, 30%+ browning = 0
    score = max(0.0, 100.0 - (ratio / 30.0) * 100.0)
    return round(ratio, 2), round(score, 1)


def _texture_quality_score(gray_img) -> float:
    """
    Laplacian variance as a texture sharpness proxy.
    Fresh produce has clear edges and fine texture.
    Over-ripe / mushy food appears blurry / homogeneous.
    Returns 0-100 score (higher = sharper texture = fresher).
    """
    np = _np
    cv2 = _cv2
    lap = cv2.Laplacian(gray_img, cv2.CV_64F)
    variance = float(np.var(lap))
    # Typical food images: variance > 500 = sharp, < 50 = very blurry
    # Log-scale mapping to 0-100
    import math
    score = min(100.0, max(0.0, 20.0 * math.log10(max(variance, 1.0))))
    return round(score, 1)


def _brightness_score(hsv_img, context: dict) -> float:
    """
    Mean brightness (V channel).
    Very dark AND very bright images lose points (unless naturally so).
    Returns 0-100 score.
    """
    np = _np
    v_ch = hsv_img[:, :, 2].astype(np.float32)
    mean_v = float(np.mean(v_ch))  # 0-255
    norm = mean_v / 255.0           # 0-1

    if context.get("is_naturally_yellow") or context.get("is_naturally_dark_green"):
        # For bright/vibrant foods, high brightness is GOOD, not suspicious
        # Score peaks at mean_v=200+
        score = min(100.0, norm * 120.0)
    elif context.get("is_naturally_dark"):
        # Dark foods: score peaks at medium-dark values
        score = 100.0 - abs(norm - 0.35) * 180.0
    else:
        # Generic: optimal brightness at 60-80% (150-200/255)
        # Below 30%: too dark/rotted; above 90%: over-exposed/bleached
        score = 100.0 - abs(norm - 0.65) * 160.0

    return round(max(0.0, min(100.0, score)), 1)


def _mold_detection(hsv_img, context: dict) -> tuple[float, list[str]]:
    """
    Detect mold by looking for:
      - Green mold: hue 35-85 (OpenCV), moderate saturation
        (suppressed for naturally-green foods)
      - White mold: low saturation, high value
      - Black mold: very low value, any saturation

    Uses morphological opening to remove noise (min region size filter).
    Returns (mold_area_percent, list_of_detected_types).
    """
    np = _np
    cv2 = _cv2

    h_ch = hsv_img[:, :, 0]
    s_ch = hsv_img[:, :, 1]
    v_ch = hsv_img[:, :, 2]
    total_px = h_ch.size

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    detected_types: list[str] = []
    total_mold_px = 0

    # --- Green mold ---
    if not context.get("is_naturally_dark_green"):
        green_mask = (
            (h_ch >= 35) & (h_ch <= 85) &
            (s_ch >= 60) & (s_ch <= 230) &
            (v_ch >= 30) & (v_ch <= 200)
        ).astype(np.uint8)
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
        green_px = int(np.sum(green_mask))
        if green_px / total_px > 0.015:   # >1.5% of image
            detected_types.append("green_mold")
            total_mold_px += green_px

    # --- White mold (fuzzy white patches) ---
    white_mask = (
        (s_ch < 40) & (v_ch >= 200)
    ).astype(np.uint8)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
    white_px = int(np.sum(white_mask))
    if white_px / total_px > 0.02:
        detected_types.append("white_mold")
        total_mold_px += white_px

    # --- Black mold ---
    black_mask = (
        (v_ch < 25) & (s_ch > 15)
    ).astype(np.uint8)
    black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, kernel)
    black_px = int(np.sum(black_mask))
    if black_px / total_px > 0.01:
        detected_types.append("black_mold")
        total_mold_px += black_px

    mold_pct = min(100.0, total_mold_px / total_px * 100.0)
    return round(mold_pct, 2), detected_types


def _image_quality_check(gray_img) -> dict:
    """
    Check if the image itself is suitable for analysis:
    - Blur check (Laplacian variance)
    - Exposure check (mean brightness)
    Returns {"is_good": bool, "blur_score": float, "exposure": str}
    """
    np = _np
    cv2 = _cv2
    lap = cv2.Laplacian(gray_img, cv2.CV_64F)
    blur_var = float(np.var(lap))
    mean_v = float(np.mean(gray_img))
    is_blurry = blur_var < 30.0
    is_overexposed = mean_v > 240
    is_underexposed = mean_v < 15

    exposure = "normal"
    if is_overexposed:
        exposure = "overexposed"
    elif is_underexposed:
        exposure = "underexposed"

    return {
        "is_good": not (is_blurry or is_overexposed or is_underexposed),
        "blur_score": round(blur_var, 1),
        "exposure": exposure,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_food_image(
    image_bytes: bytes,
    food_name: str = "unknown",
) -> Optional[dict]:
    """
    Run the full CV freshness pipeline on raw image bytes.

    Parameters
    ----------
    image_bytes : bytes
        Raw image file content (JPEG, PNG, WebP supported).
    food_name : str
        Human-readable food name — used for context-aware adjustments.

    Returns
    -------
    dict with keys:
        cv_score            : float (0-100, composite)
        saturation_score    : float
        browning_score      : float
        texture_score       : float
        brightness_score    : float
        mold_area_pct       : float
        mold_types          : list[str]
        browning_ratio_pct  : float
        visual_flags        : list[dict]
        image_quality       : dict
        food_context        : dict
    Returns None on any failure (caller must handle gracefully).
    """
    if not _import_cv():
        return None

    try:
        cv2 = _cv2
        np = _np

        # Decode + resize
        bgr = _bytes_to_bgr(image_bytes)
        bgr = _resize_for_analysis(bgr, max_dim=512)

        # Convert colour spaces
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        # Context flags
        context = _classify_food_context(food_name)

        # Image quality check first
        iq = _image_quality_check(gray)

        # Individual metrics
        sat_score = _saturation_score(hsv)
        browning_ratio, browning_score = _browning_ratio(hsv, bgr, context)
        texture_score = _texture_quality_score(gray)
        bright_score = _brightness_score(hsv, context)
        mold_pct, mold_types = _mold_detection(hsv, context)

        # Visual flags list (for UI display)
        visual_flags: list[dict] = []

        if mold_pct > 1.5:
            severity = min(100.0, mold_pct * 8)
            visual_flags.append({
                "type": "mold",
                "severity": round(severity, 1),
                "confidence": round(min(95.0, mold_pct * 10), 1),
                "description": f"Possible {'/'.join(mold_types)} mold detected ({mold_pct:.1f}% of image area)",
            })

        if browning_ratio > 10.0:
            severity = min(100.0, browning_ratio * 2.5)
            visual_flags.append({
                "type": "browning",
                "severity": round(severity, 1),
                "confidence": round(min(90.0, browning_ratio * 3), 1),
                "description": f"Browning/discoloration detected ({browning_ratio:.1f}% of image area)",
            })

        if texture_score < 20.0:
            visual_flags.append({
                "type": "texture_loss",
                "severity": round(100.0 - texture_score, 1),
                "confidence": 65.0,
                "description": "Texture appears soft or mushy (low Laplacian variance)",
            })

        # Weighted composite CV score
        # Weights: saturation 20%, browning 30%, texture 20%, brightness 15%, mold penalty 15%
        mold_penalty = min(100.0, mold_pct * 12)
        mold_score = max(0.0, 100.0 - mold_penalty)

        cv_score = (
            sat_score * 0.20 +
            browning_score * 0.30 +
            texture_score * 0.20 +
            bright_score * 0.15 +
            mold_score * 0.15
        )
        cv_score = round(max(0.0, min(100.0, cv_score)), 1)

        # Hard caps: mold → cap at 25, severe browning → cap at 40
        if mold_pct > 5.0:
            cv_score = min(cv_score, 25.0)
        elif browning_ratio > 30.0:
            cv_score = min(cv_score, 40.0)

        # Penalise poor image quality (reduce confidence, don't change score)
        if not iq["is_good"]:
            logger.debug("[CV-FRESHNESS] Image quality issue: %s", iq)

        return {
            "cv_score": cv_score,
            "saturation_score": sat_score,
            "browning_score": browning_score,
            "texture_score": texture_score,
            "brightness_score": bright_score,
            "mold_area_pct": mold_pct,
            "mold_types": mold_types,
            "browning_ratio_pct": browning_ratio,
            "visual_flags": visual_flags,
            "image_quality": iq,
            "food_context": context,
        }

    except Exception as exc:
        logger.warning("[CV-FRESHNESS] Analysis failed: %s", exc, exc_info=True)
        return None
