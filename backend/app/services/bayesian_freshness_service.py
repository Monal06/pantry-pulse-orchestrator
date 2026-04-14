"""
Bayesian Freshness Model
========================
Extends the existing linear decay model with a Bayesian update step
when visual scan data is available.

This module has the functions:

  compute_bayesian_freshness(...)
      Drop-in compatible with compute_freshness() for the deep-analysis
      endpoint.  When visual_score=None it returns the IDENTICAL result
      as the original formula.

  predict_days_remaining(...)
      Estimates how many more days the item can be safely stored.

  compute_confidence_interval(...)
      Returns a (lower, upper) confidence interval that widens over time
      (uncertainty grows as food ages).

Bayesian model description
---------------------------
  We model freshness as f(t) = 100 - t * λ  (the current linear model)
  where λ is the category/storage decay rate.
  This gives us a Gaussian prior centred on the linear prediction with
  variance σ²_prior = (λ * days)² * 0.05  (uncertainty ∝ elapsed time).

Likelihood (when visual scan available):
  The visual ensemble score v is modelled as:
    v | f ~ N(f, σ²_obs)   with σ²_obs = ((100 - confidence) / 100 * 30)²
  i.e. a noisy observation of the true freshness with observation noise
  proportional to the ensemble's own uncertainty.

Posterior (Gaussian-Gaussian conjugate update):
  μ_post = (μ_prior / σ²_prior + v / σ²_obs) / (1/σ²_prior + 1/σ²_obs)
  σ²_post = 1 / (1/σ²_prior + 1/σ²_obs)

When confidence is 100 the posterior collapses to the visual score.
When confidence is 0 the posterior equals the prior (time-based score).
"""

from __future__ import annotations

import math
from datetime import date
from typing import Optional

from app.models.inventory import get_decay_rate, compute_freshness


# ---------------------------------------------------------------------------
# Core Bayesian update
# ---------------------------------------------------------------------------

def compute_bayesian_freshness(
    added_date: date,
    category: str,
    storage: str,
    purchase_date: Optional[date] = None,
    visual_score: Optional[float] = None,
    visual_confidence: float = 0.0,
    item_name: Optional[str] = None,
) -> dict:
    """
    Compute freshness with optional Bayesian visual update.

    Parameters
    ----------
    added_date       : date  — when item was added to system
    category         : str   — food category (from FRESHNESS_DECAY_RATES)
    storage          : str   — fridge / freezer / pantry / counter
    purchase_date    : date  — when item was purchased (preferred over added_date)
    visual_score     : float — ensemble freshness score from image analysis (0-100)
                               Pass None to use time-based prior only (legacy behaviour).
    visual_confidence: float — ensemble confidence 0-100
                               Only meaningful when visual_score is provided.
    item_name        : str   — food item name for USDA FoodKeeper lookup (optional)

    Returns
    -------
    dict with keys:
        prior_score          : float   — time-based linear score (identical to compute_freshness)
        posterior_score      : float   — Bayesian updated score (= prior if no visual)
        visual_weight        : float   — how much visual data influenced result (0-1)
        prior_uncertainty    : float   — 1-sigma uncertainty on prior
        posterior_uncertainty: float   — 1-sigma uncertainty on posterior (always ≤ prior)
        decay_rate           : float   — λ used
        days_elapsed         : int
        foodkeeper_match     : bool    — whether USDA FoodKeeper data was used
    """
    # --- Prior: identical to existing compute_freshness() ---
    age_ref = purchase_date if purchase_date else added_date
    days_elapsed = max(0, (date.today() - age_ref).days)
    decay = get_decay_rate(category, storage, item_name)
    prior_score = max(0.0, 100.0 - days_elapsed * decay)

    # Check if FoodKeeper was used for this item
    foodkeeper_used = False
    if item_name:
        try:
            from app.services.foodkeeper_service import get_foodkeeper_decay_rate
            foodkeeper_used = get_foodkeeper_decay_rate(item_name, storage) is not None
        except Exception:
            pass

    # Prior uncertainty grows with age (decays poorly → more uncertainty)
    # σ_prior = max(5, 0.15 * days * decay)  capped at 25
    prior_std = min(25.0, max(5.0, 0.15 * days_elapsed * decay))
    var_prior = prior_std ** 2

    # --- If no visual data, return prior only ---
    if visual_score is None or visual_confidence <= 0:
        return {
            "prior_score": round(prior_score, 1),
            "posterior_score": round(prior_score, 1),
            "visual_weight": 0.0,
            "prior_uncertainty": round(prior_std, 2),
            "posterior_uncertainty": round(prior_std, 2),
            "decay_rate": decay,
            "days_elapsed": days_elapsed,
            "update_applied": False,
            "foodkeeper_match": foodkeeper_used,
        }

    # --- Likelihood: visual ensemble as noisy observation ---
    # Observation noise: low confidence → high noise, high confidence → low noise
    obs_noise_std = max(2.0, (100.0 - visual_confidence) / 100.0 * 35.0)
    var_obs = obs_noise_std ** 2

    # --- Gaussian-Gaussian conjugate posterior ---
    precision_prior = 1.0 / var_prior
    precision_obs = 1.0 / var_obs

    posterior_mean = (
        precision_prior * prior_score + precision_obs * visual_score
    ) / (precision_prior + precision_obs)

    var_posterior = 1.0 / (precision_prior + precision_obs)
    posterior_std = math.sqrt(var_posterior)

    # Visual weight: fraction of posterior pulled by visual (vs prior)
    visual_weight = precision_obs / (precision_prior + precision_obs)

    posterior_score = max(0.0, min(100.0, posterior_mean))

    return {
        "prior_score": round(prior_score, 1),
        "posterior_score": round(posterior_score, 1),
        "visual_weight": round(visual_weight, 3),
        "prior_uncertainty": round(prior_std, 2),
        "posterior_uncertainty": round(posterior_std, 2),
        "decay_rate": decay,
        "days_elapsed": days_elapsed,
        "update_applied": True,
        "foodkeeper_match": foodkeeper_used,
    }


def predict_days_remaining(
    current_score: float,
    category: str,
    storage: str,
    critical_threshold: float = 50.0,
    item_name: Optional[str] = None,
) -> float:
    """
    Estimate days until freshness drops below critical_threshold.

    Uses the current score and decay rate to extrapolate forward.
    Returns 0.0 if already below threshold.
    """
    decay = get_decay_rate(category, storage, item_name)
    if decay <= 0:
        return 9999.0  # non-perishable
    if current_score <= critical_threshold:
        return 0.0
    days = (current_score - critical_threshold) / decay
    return round(max(0.0, days), 1)


def compute_confidence_interval(
    posterior_score: float,
    posterior_uncertainty: float,
    z: float = 1.96,
) -> tuple[float, float]:
    """
    Return a (lower, upper) 95% confidence interval for the freshness score.

    Parameters
    ----------
    posterior_score       : float — point estimate
    posterior_uncertainty : float — 1-sigma (std dev) from Bayesian model
    z                     : float — z-score (1.96 for 95% CI)

    Returns
    -------
    (lower_bound, upper_bound) clamped to [0, 100]
    """
    lower = max(0.0, posterior_score - z * posterior_uncertainty)
    upper = min(100.0, posterior_score + z * posterior_uncertainty)
    return round(lower, 1), round(upper, 1)
