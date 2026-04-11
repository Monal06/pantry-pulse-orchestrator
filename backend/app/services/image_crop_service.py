"""
Image Crop Service
==================
Crops individual food items out of a full fridge photo using normalised
bounding boxes returned by Gemini.

bbox format: [x1, y1, x2, y2]  — all values 0.0–1.0 relative to image size
  x1, y1 = top-left corner
  x2, y2 = bottom-right corner

The crop is padded by 5% on each side so context pixels aren't cut off at the edge.
Returns JPEG bytes of the cropped region, ready to pass into the ensemble engine.
"""

from __future__ import annotations

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def crop_item_from_image(
    image_bytes: bytes,
    bbox: list[float],
    pad: float = 0.05,
) -> Optional[bytes]:
    """
    Crop a single item from a full image using a normalised bounding box.

    Parameters
    ----------
    image_bytes : raw image bytes (JPEG / PNG / WebP)
    bbox        : [x1, y1, x2, y2] all 0.0-1.0 normalised
    pad         : fractional padding to add around the box (default 5%)

    Returns
    -------
    JPEG bytes of the cropped region, or None on failure.
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size

        x1, y1, x2, y2 = bbox

        # Validate box makes sense
        if x2 <= x1 or y2 <= y1:
            logger.warning("[CROP] Invalid bbox %s — skipping", bbox)
            return None

        # Apply padding (clamped to image bounds)
        pad_x = (x2 - x1) * pad
        pad_y = (y2 - y1) * pad
        x1 = max(0.0, x1 - pad_x)
        y1 = max(0.0, y1 - pad_y)
        x2 = min(1.0, x2 + pad_x)
        y2 = min(1.0, y2 + pad_y)

        # Convert to pixel coordinates
        px1 = int(x1 * w)
        py1 = int(y1 * h)
        px2 = int(x2 * w)
        py2 = int(y2 * h)

        # Minimum crop size guard (at least 32x32 px)
        if (px2 - px1) < 32 or (py2 - py1) < 32:
            logger.warning("[CROP] Crop region too small (%dx%d) — using full image", px2-px1, py2-py1)
            return image_bytes

        cropped = img.crop((px1, py1, px2, py2))

        buf = io.BytesIO()
        cropped.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    except Exception as exc:
        logger.warning("[CROP] Failed to crop image: %s", exc)
        return None


def validate_bbox(bbox) -> Optional[list[float]]:
    """
    Validate and normalise a bbox value from Gemini output.
    Returns a clean [x1, y1, x2, y2] list or None if invalid.
    """
    try:
        if not bbox or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            return None
        box = [float(v) for v in bbox]
        # All values must be 0-1
        if any(v < 0.0 or v > 1.0 for v in box):
            return None
        x1, y1, x2, y2 = box
        if x2 <= x1 or y2 <= y1:
            return None
        return box
    except Exception:
        return None
