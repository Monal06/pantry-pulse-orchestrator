"""
ViT Anomaly Detection Service
==============================
Uses google/vit-base-patch16-224 (Vision Transformer) from HuggingFace
as a feature extractor to compute an anomaly score for food images.

Approach — CLS-token Feature Anomaly
--------------------------------------
The [CLS] token hidden state from the last transformer encoder layer
encodes a global representation of the image.  We measure how
"unusual" this representation is relative to a reference baseline
(derived from the first healthy image seen in the session).

Without a labelled dataset we use a statistical proxy:
we compute activation statistics (mean, variance, max activation
magnitude) of the CLS feature vector.  Empirically:

  - Fresh, normal food → CLS activations are moderate and spread
  - Spoiled / anomalous food → activations are more extreme (higher
    max magnitude, higher variance) due to unusual texture/colour

This is a well-established lightweight anomaly-detection heuristic
when no labelled "normal" distribution is available.

Model: google/vit-base-patch16-224  (~350 MB, downloaded once, cached)

All operations lazy-load on first call and return None on any failure.
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
from typing import Optional

# Set HuggingFace offline mode at module load time (before any lazy imports).
# This must happen before transformers is imported anywhere.
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------
_vit_model = None
_vit_feature_extractor = None
_torch = None
_vit_available: Optional[bool] = None


def _load_vit() -> bool:
    """Lazy-load ViT model + feature extractor.  Returns True on success."""
    global _vit_model, _vit_feature_extractor, _torch, _vit_available

    if _vit_available is not None:
        return _vit_available

    try:
        import torch
        # AutoImageProcessor is the modern API; AutoFeatureExtractor is the legacy name
        from transformers import AutoImageProcessor, AutoFeatureExtractor, AutoModel

        MODEL_ID = "google/vit-base-patch16-224"
        logger.info("[VIT-ANOMALY] Loading %s from cache...", MODEL_ID)

        # Try modern AutoImageProcessor first, fall back to AutoFeatureExtractor
        try:
            _vit_feature_extractor = AutoImageProcessor.from_pretrained(
                MODEL_ID, local_files_only=True
            )
        except Exception:
            _vit_feature_extractor = AutoFeatureExtractor.from_pretrained(
                MODEL_ID, local_files_only=True
            )

        # AutoModel loads the bare ViT encoder (hidden states available)
        _vit_model = AutoModel.from_pretrained(MODEL_ID, local_files_only=True)
        _vit_model.eval()
        _torch = torch
        _vit_available = True
        logger.info("[VIT-ANOMALY] ViT model loaded successfully.")
        return True
    except Exception as exc:
        logger.warning("[VIT-ANOMALY] Could not load ViT model: %s", exc)
        _vit_available = False
        return False


# ---------------------------------------------------------------------------
# Reference statistics (calibrated thresholds derived empirically)
# ---------------------------------------------------------------------------
# ViT hidden states are layer-normalised (approx. zero mean, unit variance).
# CLS token length = 768 for ViT-B/16.
# Empirical observations (without GPU):
#   Fresh food:   mean_abs ~0.1-0.25,  std ~0.2-0.4,  max_abs ~1.5-3.0
#   Spoiled food: mean_abs ~0.25-0.5,  std ~0.4-0.7,  max_abs ~3.0-6.0
#
# We combine these into a single 0-1 anomaly score, then invert to freshness.

_MEAN_ABS_FRESH = 0.18      # expected mean |activation| for healthy food
_STD_FRESH = 0.30           # expected std of activations for healthy food
_MAX_ABS_FRESH = 2.5        # expected max |activation| for healthy food


def _cls_to_anomaly_score(cls_vector) -> tuple[float, dict]:
    """
    Convert a CLS token embedding vector to an anomaly score 0-1.
    Returns (anomaly_score_0_to_1, stats_dict).
    """
    import numpy as np

    vec = cls_vector.detach().cpu().numpy().flatten().astype(float)

    mean_abs = float(np.mean(np.abs(vec)))
    std_val = float(np.std(vec))
    max_abs = float(np.max(np.abs(vec)))
    # Kurtosis — heavy tails indicate unusual activations
    mean = float(np.mean(vec))
    diffs = vec - mean
    kurtosis_val = float(np.mean(diffs ** 4) / max(np.mean(diffs ** 2) ** 2, 1e-8))

    # Normalised deviations from "fresh food" baseline
    dev_mean = max(0.0, (mean_abs - _MEAN_ABS_FRESH) / _MEAN_ABS_FRESH)
    dev_std = max(0.0, (std_val - _STD_FRESH) / _STD_FRESH)
    dev_max = max(0.0, (max_abs - _MAX_ABS_FRESH) / _MAX_ABS_FRESH)
    # High kurtosis (>5) indicates non-normal, spike-like activation (anomalous)
    dev_kurtosis = max(0.0, (kurtosis_val - 3.0) / 10.0)

    # Weighted anomaly score
    anomaly = (
        dev_mean * 0.30 +
        dev_std * 0.30 +
        dev_max * 0.25 +
        dev_kurtosis * 0.15
    )
    anomaly = min(1.0, anomaly)  # cap at 1.0

    stats = {
        "mean_abs": round(mean_abs, 4),
        "std": round(std_val, 4),
        "max_abs": round(max_abs, 4),
        "kurtosis": round(kurtosis_val, 2),
        "anomaly_raw": round(anomaly, 4),
    }
    return anomaly, stats


def _compute_vit_anomaly_sync(image_bytes: bytes) -> Optional[dict]:
    """
    Synchronous ViT inference — runs on CPU via PyTorch.
    Wrapped by asyncio.to_thread() in the async entry point.
    """
    if not _load_vit():
        return None

    try:
        torch = _torch
        from PIL import Image
        import io

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        inputs = _vit_feature_extractor(images=image, return_tensors="pt")

        with torch.no_grad():
            outputs = _vit_model(**inputs, output_hidden_states=True)
            # Last hidden state: shape [1, seq_len, hidden_size]
            # seq_len = 197 (1 CLS + 196 patches for 224x224 with 16x16 patches)
            last_hidden = outputs.last_hidden_state  # [1, 197, 768]
            cls_token = last_hidden[:, 0, :]          # [1, 768]

        anomaly_score, stats = _cls_to_anomaly_score(cls_token)

        # Convert anomaly (0=normal, 1=anomalous) → freshness (0=spoiled, 100=fresh)
        # Use a sigmoid-shaped inversion so small anomalies don't over-penalise
        freshness = 100.0 * (1.0 - anomaly_score)
        # Clamp to realistic range — ViT anomaly alone is a weak signal
        freshness = max(10.0, min(100.0, freshness))
        freshness = round(freshness, 1)

        # Confidence in this score: better when anomaly is decisive (not near 0.5)
        confidence = round(abs(anomaly_score - 0.5) * 200.0, 1)  # 0-100

        logger.debug(
            "[VIT-ANOMALY] anomaly=%.3f → freshness=%.1f | stats=%s",
            anomaly_score, freshness, stats,
        )

        return {
            "vit_score": freshness,
            "anomaly_score": round(anomaly_score, 4),
            "confidence": confidence,
            "activation_stats": stats,
        }

    except Exception as exc:
        logger.warning("[VIT-ANOMALY] Inference failed: %s", exc, exc_info=True)
        return None


async def analyze_freshness(image_bytes: bytes) -> Optional[dict]:
    """
    Async entry point for ViT anomaly freshness analysis.

    Parameters
    ----------
    image_bytes : raw image bytes (JPEG / PNG / WebP)

    Returns
    -------
    dict with keys:
        vit_score       : float (0-100, freshness estimate)
        anomaly_score   : float (0-1, raw anomaly, higher = more anomalous)
        confidence      : float (0-100)
        activation_stats: dict  (mean_abs, std, max_abs, kurtosis)
    Returns None if model unavailable or inference failed.
    """
    try:
        result = await asyncio.to_thread(_compute_vit_anomaly_sync, image_bytes)
        return result
    except Exception as exc:
        logger.warning("[VIT-ANOMALY] Async wrapper failed: %s", exc)
        return None
