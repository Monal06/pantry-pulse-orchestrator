"""
Ensemble Freshness Orchestrator
================================
Combines signals from four independent analysis methods to produce a
single robust freshness score with a confidence level.

Signal weights (when all methods are available)
------------------------------------------------
  Gemini visual assessment    40%   — authoritative, multimodal LLM
  CV pipeline (OpenCV)        25%   — objective colour/texture metrics
  ViT anomaly detection       20%   — transformer feature-space anomaly
  CLIP zero-shot              15%   — zero-shot semantic similarity

Weight redistribution
---------------------
If any method is unavailable (returns None), its weight is distributed
proportionally to the remaining methods.  This ensures:
  - All weights always sum to 1.0
  - The score is always computable as long as ≥ 1 method works
  - Gemini is the last fallback (most reliable)

Confidence scoring
------------------
Confidence is computed from three factors:
  1. Image quality  — blurry or over/under-exposed images reduce confidence
  2. Method agreement — high variance across methods → lower confidence
  3. Individual method certainties — if CLIP is 90% sure, that adds confidence

Hard caps (safety-critical overrides)
--------------------------------------
  - Any mold detection by CV or CLIP → ensemble_score capped at 25
  - Rot/heavy spoilage signal → capped at 30
  These override the weighted average to prevent dangerous optimism.
"""

from __future__ import annotations

import asyncio
import logging
import math
from datetime import date
from typing import Optional, Any

from app.services import cv_freshness_service, clip_freshness_service, vit_anomaly_service
from app.services import llm_reasoning_service, bayesian_freshness_service
from app.services import gemini_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Base weights (all methods available)
# ---------------------------------------------------------------------------
BASE_WEIGHTS = {
    "gemini":      0.40,
    "cv_pipeline": 0.25,
    "vit_anomaly": 0.20,
    "clip":        0.15,
}


def _redistribute_weights(available: dict[str, bool]) -> dict[str, float]:
    """
    Redistribute BASE_WEIGHTS proportionally for available methods only.
    Any method with available=False gets weight=0.
    """
    active = {k: v for k, v in BASE_WEIGHTS.items() if available.get(k, False)}
    if not active:
        return {k: 0.0 for k in BASE_WEIGHTS}
    total = sum(active.values())
    return {
        k: (v / total if k in active else 0.0)
        for k, v in BASE_WEIGHTS.items()
    }


def _gemini_result_to_score(gemini_result: Optional[dict]) -> Optional[float]:
    """
    Convert Gemini check_spoilage() or fridge-photo spoilage report to 0-100.
    Gemini returns spoilage_detected (bool) + confidence (0-1).
    """
    if not gemini_result:
        return None

    # Handle check_spoilage() format
    if "overall_assessment" in gemini_result:
        assessment_map = {
            "safe to eat":      95.0,
            "use immediately":  55.0,
            "questionable":     35.0,
            "do not consume":   10.0,
        }
        assessment = gemini_result.get("overall_assessment", "").lower()
        base = next((v for k, v in assessment_map.items() if k in assessment), None)
        if base is not None:
            return base

    # Handle boolean spoilage_detected + confidence
    spoiled = gemini_result.get("spoilage_detected", False)
    confidence = float(gemini_result.get("confidence", 0.5))

    if spoiled:
        # Spoiled with high confidence → low freshness
        return round(max(0.0, 40.0 - confidence * 35.0), 1)
    else:
        # Not spoiled: freshness scales with 1 - confidence of spoilage
        return round(min(100.0, 60.0 + (1.0 - confidence) * 40.0), 1)


def _compute_confidence(
    method_scores: dict[str, Optional[float]],
    weights: dict[str, float],
    image_quality: Optional[dict],
) -> float:
    """
    Compute overall ensemble confidence (0-100).

    Factors:
    1. Number of available methods: more = higher base confidence
    2. Agreement: low variance across method scores = higher confidence
    3. Image quality: blurry/bad exposure reduces confidence
    """
    scores = [v for v in method_scores.values() if v is not None]
    n = len(scores)

    if n == 0:
        return 0.0
    if n == 1:
        base_conf = 40.0
    elif n == 2:
        base_conf = 60.0
    elif n == 3:
        base_conf = 75.0
    else:
        base_conf = 85.0

    # Agreement factor: coefficient of variation (lower CV = better agreement)
    if n > 1:
        mean = sum(scores) / n
        std = math.sqrt(sum((s - mean) ** 2 for s in scores) / n)
        cv = std / max(mean, 1.0)                         # 0 = perfect agreement
        agreement_factor = max(0.0, 1.0 - cv * 1.5)       # 0-1
        base_conf *= (0.5 + 0.5 * agreement_factor)       # up to full credit

    # Image quality penalty
    if image_quality:
        if not image_quality.get("is_good", True):
            exposure = image_quality.get("exposure", "normal")
            if exposure != "normal":
                base_conf *= 0.75   # 25% penalty for bad exposure
            elif image_quality.get("blur_score", 100) < 30:
                base_conf *= 0.80   # 20% penalty for blur

    return round(min(100.0, max(0.0, base_conf)), 1)


def _confidence_level(confidence: float) -> str:
    if confidence >= 75:
        return "high"
    if confidence >= 50:
        return "medium"
    return "low"


def _freshness_level(score: float) -> str:
    if score >= 70:
        return "good"
    if score >= 50:
        return "use_soon"
    return "critical"


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

async def run_ensemble_analysis(
    image_bytes: bytes,
    food_name: str = "unknown",
    food_category: str = "other",
    storage: str = "fridge",
    added_date: Optional[date] = None,
    purchase_date: Optional[date] = None,
    mime_type: str = "image/jpeg",
) -> dict:
    """
    Run all four analysis methods concurrently and compute ensemble score.

    Parameters
    ----------
    image_bytes   : raw image bytes
    food_name     : human-readable item name (for context-aware CV + LLM prompt)
    food_category : food category (for Bayesian model + context)
    storage       : storage location (for Bayesian decay prior)
    added_date    : when item was added (for Bayesian prior)
    purchase_date : when item was bought (for Bayesian prior)
    mime_type     : MIME type of image

    Returns
    -------
    Complete ensemble result dict — see module docstring for schema.
    """
    today = date.today()
    added_date = added_date or today

    # -----------------------------------------------------------------------
    # Step 1: Run all analysis methods concurrently
    # -----------------------------------------------------------------------
    logger.info("[ENSEMBLE] Starting analysis for '%s' (%s)", food_name, food_category)

    gemini_task = asyncio.create_task(
        _run_gemini_safely(image_bytes, food_name, mime_type)
    )
    cv_task = asyncio.create_task(
        asyncio.to_thread(cv_freshness_service.analyze_food_image, image_bytes, food_name)
    )
    clip_task = asyncio.create_task(
        clip_freshness_service.analyze_freshness(image_bytes)
    )
    vit_task = asyncio.create_task(
        vit_anomaly_service.analyze_freshness(image_bytes)
    )

    gemini_result, cv_result, clip_result, vit_result = await asyncio.gather(
        gemini_task, cv_task, clip_task, vit_task,
        return_exceptions=False,
    )

    # -----------------------------------------------------------------------
    # Step 2: Extract scores + availability
    # -----------------------------------------------------------------------
    gemini_score = _gemini_result_to_score(gemini_result)
    cv_score = cv_result.get("cv_score") if cv_result else None
    clip_score = clip_result.get("clip_score") if clip_result else None
    vit_score = vit_result.get("vit_score") if vit_result else None

    available = {
        "gemini":      gemini_score is not None,
        "cv_pipeline": cv_score is not None,
        "vit_anomaly": vit_score is not None,
        "clip":        clip_score is not None,
    }
    method_scores: dict[str, Optional[float]] = {
        "gemini":      gemini_score,
        "cv_pipeline": cv_score,
        "vit_anomaly": vit_score,
        "clip":        clip_score,
    }

    logger.info("[ENSEMBLE] Scores — Gemini:%.1f CV:%.1f CLIP:%.1f ViT:%.1f",
                gemini_score or -1, cv_score or -1, clip_score or -1, vit_score or -1)

    # -----------------------------------------------------------------------
    # Step 3: Redistribute weights + weighted average
    # -----------------------------------------------------------------------
    weights = _redistribute_weights(available)
    weighted_sum = sum(
        weights[k] * v
        for k, v in method_scores.items()
        if v is not None
    )
    ensemble_score = round(max(0.0, min(100.0, weighted_sum)), 1)

    # -----------------------------------------------------------------------
    # Step 4: Safety hard caps
    # -----------------------------------------------------------------------
    visual_flags: list[dict] = []
    mold_capped = False
    rot_capped = False

    # Collect CV visual flags
    if cv_result and cv_result.get("visual_flags"):
        visual_flags.extend(cv_result["visual_flags"])

    # Mold from CV
    cv_mold_pct = (cv_result or {}).get("mold_area_pct", 0.0)
    if cv_mold_pct > 5.0:
        mold_capped = True

    # Mold / rot from CLIP
    if clip_result:
        if clip_result.get("mold_probability", 0) > 35:
            mold_capped = True
        if clip_result.get("rot_detected", False):
            rot_capped = True

    # Mold from Gemini spoilage signs
    if gemini_result:
        signs = [s.lower() for s in gemini_result.get("signs", [])]
        if any("mold" in s or "fuzzy" in s for s in signs):
            mold_capped = True
        if any("rot" in s for s in signs):
            rot_capped = True

    if mold_capped:
        ensemble_score = min(ensemble_score, 25.0)
        visual_flags.append({
            "type": "mold_cap_applied",
            "severity": 90.0,
            "confidence": 85.0,
            "description": "Mold detected — score capped at 25 for safety",
        })
    elif rot_capped:
        ensemble_score = min(ensemble_score, 30.0)
        visual_flags.append({
            "type": "rot_cap_applied",
            "severity": 85.0,
            "confidence": 80.0,
            "description": "Rot/decay detected — score capped at 30 for safety",
        })

    # Gemini spoilage flag
    if gemini_result and gemini_result.get("spoilage_detected"):
        spoilage_signs = gemini_result.get("signs", [])
        if spoilage_signs:
            visual_flags.append({
                "type": "gemini_spoilage",
                "severity": round((1.0 - gemini_result.get("confidence", 0.5)) * 50 + 50, 1),
                "confidence": round(gemini_result.get("confidence", 0.5) * 100, 1),
                "description": f"Gemini detected: {', '.join(spoilage_signs[:3])}",
            })

    # -----------------------------------------------------------------------
    # Step 5: Confidence
    # -----------------------------------------------------------------------
    image_quality = (cv_result or {}).get("image_quality")
    confidence = _compute_confidence(method_scores, weights, image_quality)

    # -----------------------------------------------------------------------
    # Step 6: Bayesian prediction
    # -----------------------------------------------------------------------
    bayes = bayesian_freshness_service.compute_bayesian_freshness(
        added_date=added_date,
        category=food_category,
        storage=storage,
        purchase_date=purchase_date,
        visual_score=ensemble_score,
        visual_confidence=confidence,
    )

    days_remaining = bayesian_freshness_service.predict_days_remaining(
        current_score=bayes["posterior_score"],
        category=food_category,
        storage=storage,
    )
    ci_lower, ci_upper = bayesian_freshness_service.compute_confidence_interval(
        bayes["posterior_score"],
        bayes["posterior_uncertainty"],
    )

    # Use Bayesian posterior as final score when we have scan data
    final_score = bayes["posterior_score"] if bayes["update_applied"] else ensemble_score

    # Re-apply safety caps to posterior (Bayesian can't lift a mold cap)
    if mold_capped:
        final_score = min(final_score, 25.0)
    elif rot_capped:
        final_score = min(final_score, 30.0)

    final_score = round(final_score, 1)

    # -----------------------------------------------------------------------
    # Step 7: LLM reasoning (async, non-blocking — skipped if Groq unavailable)
    # -----------------------------------------------------------------------
    methods_for_llm = {
        k: {"score": round(v, 1) if v else None, "available": available[k]}
        for k, v in method_scores.items()
    }
    llm_reasoning = await llm_reasoning_service.reason_about_freshness(
        food_name=food_name,
        ensemble_score=final_score,
        confidence=confidence,
        visual_flags=visual_flags,
        method_scores=methods_for_llm,
    )

    # -----------------------------------------------------------------------
    # Step 8: Assemble response
    # -----------------------------------------------------------------------
    decay_label = "slow"
    decay_rate = bayes.get("decay_rate", 0.0)
    if decay_rate >= 8.0:
        decay_label = "fast"
    elif decay_rate >= 4.0:
        decay_label = "moderate"

    return {
        "freshness_score":  final_score,
        "freshness_level":  _freshness_level(final_score),
        "confidence":       confidence,
        "confidence_level": _confidence_level(confidence),
        "methods": {
            "gemini": {
                "score":     round(gemini_score, 1) if gemini_score is not None else None,
                "available": available["gemini"],
            },
            "cv_pipeline": {
                "score":     round(cv_score, 1) if cv_score is not None else None,
                "available": available["cv_pipeline"],
                "details": {
                    "saturation":  (cv_result or {}).get("saturation_score"),
                    "browning":    (cv_result or {}).get("browning_score"),
                    "texture":     (cv_result or {}).get("texture_score"),
                    "brightness":  (cv_result or {}).get("brightness_score"),
                    "mold_pct":    (cv_result or {}).get("mold_area_pct"),
                } if cv_result else {},
            },
            "vit_anomaly": {
                "score":        round(vit_score, 1) if vit_score is not None else None,
                "available":    available["vit_anomaly"],
                "anomaly_score": (vit_result or {}).get("anomaly_score"),
            },
            "clip_freshness": {
                "score":            round(clip_score, 1) if clip_score is not None else None,
                "available":        available["clip"],
                "mold_probability": (clip_result or {}).get("mold_probability"),
                "dominant_prompt":  (clip_result or {}).get("dominant_assessment"),
            },
        },
        "visual_flags": visual_flags,
        "bayesian_prediction": {
            "predicted_days_remaining": days_remaining,
            "confidence_interval":      [ci_lower, ci_upper],
            "prior_score":              bayes["prior_score"],
            "posterior_score":          bayes["posterior_score"],
            "visual_weight":            bayes["visual_weight"],
            "decay_rate":               decay_label,
            "decay_rate_value":         bayes["decay_rate"],
        },
        "llm_reasoning": llm_reasoning,  # None if Groq unavailable
        "weights_used": {
            k: round(v, 3) for k, v in weights.items()
        },
        "image_quality": image_quality,
    }


# ---------------------------------------------------------------------------
# Gemini helper — calls check_spoilage as the Gemini signal
# ---------------------------------------------------------------------------

async def _run_gemini_safely(
    image_bytes: bytes,
    food_name: str,
    mime_type: str,
) -> Optional[dict]:
    """Call Gemini spoilage check; return None on failure."""
    try:
        result = await gemini_service.check_spoilage(image_bytes, food_name, mime_type)
        return result
    except Exception as exc:
        logger.warning("[ENSEMBLE] Gemini call failed: %s", exc)
        return None
