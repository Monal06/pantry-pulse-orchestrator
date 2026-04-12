"""
Groq / Llama Reasoning Layer
=============================
Calls Llama 3.3 70B via Groq API to generate a human-readable safety
assessment from the ensemble freshness data.

Why LLM reasoning here?
-----------------------
- Numerical scores are hard for users to interpret in context.
- An LLM can synthesise conflicting signals ("CV says 60, CLIP says 80")
  into a coherent natural-language recommendation.
- At temperature=0.2 the response is factual, consistent, and safe.
- Groq's inference is very fast (typically < 2s even for 70B).

Graceful degradation
--------------------
If GROQ_API_KEY is absent, or the API call fails, the function returns
None.  The ensemble layer will omit "llm_reasoning" from the response
rather than crashing or returning a 500.

JSON schema enforced by strict prompt engineering (not function calling,
to avoid Groq schema compatibility issues across model versions).
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy Groq client
# ---------------------------------------------------------------------------
_groq_client = None
_groq_available: Optional[bool] = None


def _get_groq_client():
    global _groq_client, _groq_available
    if _groq_available is not None:
        return _groq_client if _groq_available else None

    api_key = get_settings().groq_api_key
    if not api_key:
        logger.info("[GROQ-REASONING] GROQ_API_KEY not set — Groq layer disabled.")
        _groq_available = False
        return None

    try:
        import httpx
        from groq import Groq

        # Build an httpx client that skips SSL verification (corporate networks)
        http_client = httpx.Client(verify=False)
        _groq_client = Groq(api_key=api_key, http_client=http_client)
        _groq_available = True
        logger.info("[GROQ-REASONING] Groq client initialised (Llama 3.3 70B, SSL verify=False).")
        return _groq_client
    except ImportError as exc:
        logger.warning("[GROQ-REASONING] Missing package: %s", exc)
        _groq_available = False
        return None
    except Exception as exc:
        logger.warning("[GROQ-REASONING] Failed to init Groq client: %s", exc)
        _groq_available = False
        return None


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_reasoning_prompt(
    food_name: str,
    ensemble_score: float,
    confidence: float,
    visual_flags: list[dict],
    method_scores: dict[str, Any],
) -> str:
    """Build the reasoning prompt for Llama."""
    flags_text = (
        "\n".join(
            f"  - {f['type']}: severity {f['severity']:.0f}/100, "
            f"confidence {f.get('confidence', 0):.0f}%"
            for f in visual_flags
        )
        if visual_flags
        else "  None detected"
    )

    methods_text = "\n".join(
        f"  - {k}: score={v.get('score', 'N/A')}, available={v.get('available', False)}"
        for k, v in method_scores.items()
    )

    return f"""You are a food safety expert AI assistant. Based on the following multi-method freshness analysis of a food item, provide a structured safety assessment.

FOOD ITEM: {food_name}

ANALYSIS RESULTS:
- Ensemble Freshness Score: {ensemble_score:.1f}/100 (higher = fresher)
- Overall Confidence: {confidence:.1f}%

INDIVIDUAL METHOD SCORES:
{methods_text}

VISUAL FLAGS DETECTED:
{flags_text}

FRESHNESS SCALE REFERENCE:
- 70-100: Fresh — safe, use normally
- 50-70:  Use Soon — safe but plan to use within 1-3 days
- 20-50:  Critical — use immediately (cooking only) or compost
- 0-20:   Spoiled — do not consume, dispose safely

YOUR TASK: Provide a JSON response with EXACTLY these fields (no extra fields, no markdown fences):
{{
  "safety_level": "safe" | "caution" | "unsafe",
  "recommended_action": "<one sentence, specific and actionable>",
  "edibility_assessment": "<one sentence on whether safe to eat>",
  "risk_factors": ["<list up to 3 specific risk factors, or empty list>"],
  "quality_indicators": ["<list up to 3 positive quality indicators, or empty list>"],
  "confidence_explanation": "<one sentence explaining how confident this assessment is and why>",
  "days_remaining_estimate": <integer, estimated days before food is unsafe, -1 if already unsafe>
}}

Be conservative with safety. When in doubt, recommend caution. Return ONLY the JSON object."""


# ---------------------------------------------------------------------------
# Sync call (wrapped for async use)
# ---------------------------------------------------------------------------

def _call_groq_sync(prompt: str) -> Optional[dict]:
    client = _get_groq_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a food safety expert. Always return valid JSON only. "
                        "Be conservative — food safety is critical."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        raw = response.choices[0].message.content.strip()
        logger.debug("[GROQ-REASONING] Raw response: %s", raw[:200])

        # Strip markdown fences if present
        if "```" in raw:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
            raw = match.group(1) if match else raw

        return json.loads(raw)

    except json.JSONDecodeError as exc:
        logger.warning("[GROQ-REASONING] JSON parse error: %s", exc)
        return None
    except Exception as exc:
        logger.warning("[GROQ-REASONING] Groq call failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def reason_about_freshness(
    food_name: str,
    ensemble_score: float,
    confidence: float,
    visual_flags: list[dict],
    method_scores: dict[str, Any],
) -> Optional[dict]:
    """
    Generate LLM safety reasoning using Groq Llama 3.3 70B.

    Parameters
    ----------
    food_name       : str   — e.g. "whole milk"
    ensemble_score  : float — 0-100 freshness score
    confidence      : float — 0-100 ensemble confidence
    visual_flags    : list  — detected visual issues from CV/Gemini
    method_scores   : dict  — per-method scores dict for context

    Returns
    -------
    dict with keys:
        safety_level            : "safe" | "caution" | "unsafe"
        recommended_action      : str
        edibility_assessment    : str
        risk_factors            : list[str]
        quality_indicators      : list[str]
        confidence_explanation  : str
        days_remaining_estimate : int
    Returns None if Groq is unavailable or the call fails.
    """
    if _get_groq_client() is None:
        return None

    try:
        prompt = _build_reasoning_prompt(
            food_name, ensemble_score, confidence, visual_flags, method_scores
        )
        result = await asyncio.to_thread(_call_groq_sync, prompt)
        if result:
            logger.info(
                "[GROQ-REASONING] %s → safety=%s, action='%s'",
                food_name,
                result.get("safety_level"),
                result.get("recommended_action", "")[:60],
            )
        return result
    except Exception as exc:
        logger.warning("[GROQ-REASONING] Async wrapper error: %s", exc)
        return None
