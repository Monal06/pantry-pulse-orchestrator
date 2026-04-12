"""
CLIP Zero-Shot Freshness Assessment Service
============================================
Uses OpenAI CLIP (ViT-B/32) via HuggingFace transformers to perform
zero-shot freshness estimation without any fine-tuning.

Approach
--------
We compare the food image against a curated set of text prompts that
describe freshness states.  The cosine-similarity softmax scores are
mapped to a 0-100 freshness score.

Prompt design
-------------
Four anchor prompts (fine-grained):
  1. "a photo of fresh, vibrant food in perfect condition"
  2. "a photo of slightly old food that is still edible"
  3. "a photo of very old or wilted food"
  4. "a photo of moldy, rotten, or spoiled food with visible mold"

The weighted sum of prompt similarities → freshness score.

Model
-----
  openai/clip-vit-base-patch32   (~600 MB first download, cached after)

All heavy work is lazy-loaded on first call.  Any failure returns None
so the ensemble layer skips this signal.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

# Set HuggingFace offline mode at module load time (before any lazy imports).
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level cache — model loaded once, reused for all requests
# ---------------------------------------------------------------------------
_clip_model = None
_clip_processor = None
_torch = None
_clip_available: Optional[bool] = None   # None = untried, True/False = known


def _load_clip() -> bool:
    """Lazy-load CLIP model.  Returns True on success, False on failure."""
    global _clip_model, _clip_processor, _torch, _clip_available

    if _clip_available is not None:
        return _clip_available

    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor

        logger.info("[CLIP] Loading openai/clip-vit-base-patch32 from cache...")
        _clip_processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32",
            local_files_only=True,
        )
        _clip_model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32",
            local_files_only=True,
        )
        _clip_model.eval()
        _torch = torch
        _clip_available = True
        logger.info("[CLIP] Model loaded successfully.")
        return True
    except Exception as exc:
        logger.warning("[CLIP] Could not load CLIP model: %s", exc)
        _clip_available = False
        return False


# ---------------------------------------------------------------------------
# Freshness prompt anchors
# ---------------------------------------------------------------------------

# (prompt_text, freshness_score_mapping)
# Each anchor maps to a freshness score if it were the dominant match.
FRESHNESS_PROMPTS = [
    ("a photo of fresh, vibrant food in perfect condition",         100.0),
    ("a photo of slightly old food that is still edible",            65.0),
    ("a photo of very old or wilted food past its prime",            30.0),
    ("a photo of moldy, rotten, or spoiled food with visible mold",   5.0),
]

PROMPT_TEXTS = [p[0] for p in FRESHNESS_PROMPTS]
PROMPT_SCORES = [p[1] for p in FRESHNESS_PROMPTS]


def _compute_clip_freshness_sync(image_bytes: bytes) -> Optional[dict]:
    """
    Synchronous CLIP inference — runs on CPU.
    Called via asyncio.to_thread() to avoid blocking the event loop.
    """
    if not _load_clip():
        return None

    try:
        torch = _torch
        from PIL import Image
        import io

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        inputs = _clip_processor(
            text=PROMPT_TEXTS,
            images=image,
            return_tensors="pt",
            padding=True,
        )

        with torch.no_grad():
            outputs = _clip_model(**inputs)
            # image-text similarity scores (logits per image)
            logits = outputs.logits_per_image   # shape [1, num_prompts]
            probs = torch.softmax(logits, dim=-1).squeeze().tolist()

        if isinstance(probs, float):
            probs = [probs]

        # Weighted freshness score
        freshness = sum(p * s for p, s in zip(probs, PROMPT_SCORES))
        freshness = round(max(0.0, min(100.0, freshness)), 1)

        # Identify dominant prompt
        dominant_idx = probs.index(max(probs))
        dominant_prompt = PROMPT_TEXTS[dominant_idx]
        dominant_prob = round(probs[dominant_idx] * 100.0, 1)

        # Mold/rot flag
        mold_prob = probs[3]  # last prompt = moldy
        rot_detected = mold_prob > 0.35

        logger.debug(
            "[CLIP] score=%.1f | probs=%s | dominant='%s'",
            freshness, [round(p, 3) for p in probs], dominant_prompt[:40],
        )

        return {
            "clip_score": freshness,
            "prompt_probabilities": {
                text[:50]: round(prob, 4)
                for text, prob in zip(PROMPT_TEXTS, probs)
            },
            "dominant_assessment": dominant_prompt,
            "dominant_confidence": dominant_prob,
            "rot_detected": rot_detected,
            "mold_probability": round(mold_prob * 100.0, 1),
        }

    except Exception as exc:
        logger.warning("[CLIP] Inference failed: %s", exc, exc_info=True)
        return None


async def analyze_freshness(image_bytes: bytes) -> Optional[dict]:
    """
    Async wrapper for CLIP freshness assessment.

    Parameters
    ----------
    image_bytes : raw image bytes (JPEG / PNG / WebP)

    Returns
    -------
    dict with keys:
        clip_score          : float (0-100)
        prompt_probabilities: dict
        dominant_assessment : str
        dominant_confidence : float
        rot_detected        : bool
        mold_probability    : float
    Returns None if model unavailable or inference failed.
    """
    try:
        result = await asyncio.to_thread(_compute_clip_freshness_sync, image_bytes)
        return result
    except Exception as exc:
        logger.warning("[CLIP] Async wrapper failed: %s", exc)
        return None
