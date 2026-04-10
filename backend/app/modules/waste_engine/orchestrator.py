"""
Triple-Check Orchestrator for Exit Strategy Decision Engine

This module implements the core decision logic for triaging food items with
critical freshness scores (< 50) into three exit paths:
  - UPCYCLE: Creative recipes to use before spoilage
  - SHARE: Donation to charities/community
  - BIN: Sustainable disposal via waste protocols

The Triple-Check Guardrail validates decisions across three data sources:
  1. Freshness Score (from FreshSave inventory model)
  2. Visual Spoilage (from PJ's multimodal analysis module)
  3. Safety/Age Limits (from RAG-retrieved food safety guidelines)
"""

from datetime import date
from typing import Optional
from app.models.exit_strategy import (
    ExitPath,
    TripleCheckInput,
    TripleCheckGate,
    ExitStrategyResult,
    ExitStrategyRecommendation,
)
from app.modules.waste_engine.rag_retriever import RAGRetriever


# ============================================================================
# GATE EVALUATORS: Each gate returns a TripleCheckGate with pass/fail + confidence
# ============================================================================


def _evaluate_freshness_gate(score: float) -> TripleCheckGate:
    """
    Gate 1: Freshness Score Evaluation

    The freshness score is a real-time decay model based on:
    - Item category (dairy, meat, fruit, vegetable, etc.)
    - Storage location (fridge, freezer, pantry, counter)
    - Days since added

    Scoring:
      70-100: Good (meal planner territory)
      50-70:  Use Soon (meal planner territory)
      40-50:  Critical but salvageable (UPCYCLE)
      20-40:  Very critical (UPCYCLE or BIN)
      0-20:   Likely spoiled (BIN)
    """
    if score < 20:
        return TripleCheckGate(
            passed=False,
            confidence=95.0,
            reason="Score < 20: Likely already spoiled, unsafe to consume",
        )
    elif score < 40:
        return TripleCheckGate(
            passed=False,
            confidence=90.0,
            reason="Score < 40: Critically low, high spoilage risk, salvageable via upcycling only",
        )
    elif score < 50:
        return TripleCheckGate(
            passed=False,
            confidence=85.0,
            reason="Score < 50: Critical freshness, needs immediate action",
        )
    else:
        return TripleCheckGate(
            passed=True,
            confidence=90.0,
            reason="Score >= 50: Above critical threshold, route to meal planner",
        )


def _evaluate_visual_gate(spoilage_detected: bool, confidence: float) -> TripleCheckGate:
    """
    Gate 2: Visual Spoilage Detection (from PJ's multimodal module)

    Integration point: When PJ's visual analysis module is ready, it will provide:
    - spoilage_detected: bool (mold, discoloration, wilting, sliminess detected)
    - confidence: 0-1 scale of detection confidence

    Current behavior: Defaults to no spoilage if data not available (optimistic).
    This will be overridden once PJ's module integrates.
    """
    if not spoilage_detected:
        return TripleCheckGate(
            passed=True,
            confidence=confidence * 100.0,
            reason=f"No visual spoilage detected (confidence: {confidence * 100:.0f}%)",
        )
    else:
        return TripleCheckGate(
            passed=False,
            confidence=confidence * 100.0,
            reason=f"Visual spoilage detected: mold, discoloration, or unusual appearance (confidence: {confidence * 100:.0f}%)",
        )


def _evaluate_age_gate(
    category: str,
    added_date: str,
    verified_age_days: Optional[int],
    storage: str,
    rag_retriever: RAGRetriever,
) -> TripleCheckGate:
    """
    Gate 3: Food Safety & Age Limits (from RAG system)

    Integration point: Queries the RAG knowledge base for category-specific safety limits.
    If RAG returns a limit, we compare actual age against it.

    Example limits (from EFSA/FDA):
      - Seafood in fridge: 2 days max
      - Meat in fridge: 4 days max
      - Dairy in fridge: 7 days max
      - Vegetables in fridge: 7-10 days max

    Fallback: If RAG is unavailable, uses conservative estimates.
    """
    # Compute actual age if not provided
    age_days = verified_age_days or _compute_age_from_date(added_date)

    # Retrieve safety limit from RAG
    safety_limit = rag_retriever.get_category_safety_limit(category, storage)

    if age_days > safety_limit["max_days"]:
        return TripleCheckGate(
            passed=False,
            confidence=80.0,
            reason=f"{category} in {storage} exceeds safe storage ({age_days} days > {safety_limit['max_days']} day limit per {safety_limit['source']})",
        )
    else:
        return TripleCheckGate(
            passed=True,
            confidence=75.0,
            reason=f"Age OK: {age_days} days is within safe storage for {category} in {storage}",
        )


# ============================================================================
# DECISION LOGIC: Determine exit path based on all three gates
# ============================================================================


def _decide_exit_path(
    freshness_gate: TripleCheckGate,
    visual_gate: TripleCheckGate,
    age_gate: TripleCheckGate,
    freshness_score: float,
) -> ExitPath:
    """
    Exit Path Decision Tree

    Priority:
    1. If any gate fails (spoilage OR age expired) → BIN (unsafe)
    2. If freshness > 40 but gates pass → UPCYCLE (salvageable)
    3. If all gates pass and good condition → SHARE (donate)
    4. Otherwise → BIN (default safe choice)
    """
    # Safety priority: if spoilage OR age issues → BIN immediately
    if not visual_gate.passed or not age_gate.passed:
        return ExitPath.BIN

    # If freshness score allows salvage → UPCYCLE
    if freshness_score >= 40:
        return ExitPath.UPCYCLE

    # If score is very low but all gates pass → still try UPCYCLE
    if freshness_score >= 20:
        return ExitPath.UPCYCLE

    # Fallback: when in doubt, bin it safely
    return ExitPath.BIN


# ============================================================================
# RECOMMENDATION GENERATION: Based on exit path, generate action items
# ============================================================================


async def _generate_recommendations(
    exit_path: ExitPath, input: TripleCheckInput, rag_retriever: RAGRetriever
) -> list[ExitStrategyRecommendation]:
    """
    Generate actionable recommendations based on exit path

    UPCYCLE: Suggest creative recipes using the item
    SHARE: Find nearby charities, suggest donation
    BIN: Provide sustainable disposal method
    """
    recommendations = []

    if exit_path == ExitPath.UPCYCLE:
        recommendations.append(
            ExitStrategyRecommendation(
                type="recipe",
                title=f"Upcycle {input.item_name}",
                description="Generate creative recipes to use this item before it fully spoils",
                action_key="generate_recipes",
                details={
                    "category": input.category,
                    "item": input.item_name,
                    "freshness_score": input.freshness_score,
                    "quantity": input.quantity,
                },
            )
        )

    elif exit_path == ExitPath.SHARE:
        recommendations.append(
            ExitStrategyRecommendation(
                type="charity",
                title="Donate to Local Charity",
                description="Find nearby food banks and community sharing options in Galway",
                action_key="find_charities",
                details={
                    "location": "Galway",
                    "item": input.item_name,
                    "quantity": input.quantity,
                },
            )
        )

    elif exit_path == ExitPath.BIN:
        recommendations.append(
            ExitStrategyRecommendation(
                type="disposal_method",
                title="Sustainable Disposal",
                description="Learn the best way to dispose of this item according to local waste protocols",
                action_key="fetch_disposal_protocol",
                details={"category": input.category, "location": "Galway"},
            )
        )

    return recommendations


# ============================================================================
# RAG CONTEXT RETRIEVAL: Fetch relevant safety & disposal info
# ============================================================================


async def _fetch_rag_context(
    category: str, exit_path: ExitPath, rag_retriever: RAGRetriever
) -> dict:
    """
    Retrieve relevant context from RAG knowledge base:
    - Food safety guidelines (FDA/EFSA)
    - Storage recommendations
    - Disposal protocols (Galway waste management)
    - Donation/sharing resources
    """
    context = {}

    # Always fetch safety guidelines
    context["safety_guidelines"] = rag_retriever.get_safety_guidelines(category)

    if exit_path == ExitPath.UPCYCLE:
        context["storage_tips"] = rag_retriever.get_storage_tips(category)
    elif exit_path == ExitPath.SHARE:
        context["donation_tips"] = rag_retriever.get_donation_guidelines()
    elif exit_path == ExitPath.BIN:
        context["disposal_protocol"] = rag_retriever.get_disposal_protocol(category)

    return context


# ============================================================================
# MAIN ORCHESTRATOR: Triple-Check Guardrail
# ============================================================================


async def triple_check_orchestrator(
    input: TripleCheckInput, rag_retriever: Optional[RAGRetriever] = None
) -> ExitStrategyResult:
    """
    Triple-Check Orchestrator: Main entry point for exit strategy decision

    This is the core of the waste engine. It:
    1. Evaluates three independent gates (freshness, visual, age)
    2. Combines results to decide exit path (upcycle/share/bin)
    3. Generates recommendations for the user
    4. Retrieves relevant RAG context (food safety, disposal info)

    Args:
        input: TripleCheckInput with item data + optional visual/age data
        rag_retriever: RAG system for fetching safety guidelines (optional, uses mock if None)

    Returns:
        ExitStrategyResult with decision, confidence, reasoning, and recommendations
    """
    # Initialize RAG retriever if not provided (use mock retriever)
    if rag_retriever is None:
        from app.modules.waste_engine.rag_retriever import MockRAGRetriever

        rag_retriever = MockRAGRetriever()

    # GATE 1: Freshness Score
    freshness_gate = _evaluate_freshness_gate(input.freshness_score)

    # GATE 2: Visual Spoilage (integration point for PJ's module)
    visual_gate = _evaluate_visual_gate(
        input.visual_spoilage_detected, input.visual_confidence
    )

    # GATE 3: Safety/Age Rules (integration point for RAG)
    age_gate = _evaluate_age_gate(
        input.category,
        input.added_date,
        input.verified_age_days,
        input.storage,
        rag_retriever,
    )

    # DECISION: Determine exit path
    exit_path = _decide_exit_path(freshness_gate, visual_gate, age_gate, input.freshness_score)

    # RECOMMENDATIONS: Generate action items
    recommendations = await _generate_recommendations(exit_path, input, rag_retriever)

    # RAG CONTEXT: Fetch relevant information
    rag_context = await _fetch_rag_context(exit_path.value, exit_path, rag_retriever)

    # CONFIDENCE: Average across all three gates
    avg_confidence = (
        freshness_gate.confidence + visual_gate.confidence + age_gate.confidence
    ) / 3.0

    # BUILD RESULT
    result = ExitStrategyResult(
        item_id=input.item_id,
        item_name=input.item_name,
        exit_path=exit_path,
        confidence=round(avg_confidence, 1),
        reasoning=(
            f"Score {input.freshness_score}/100 | "
            f"Spoilage: {visual_gate.reason} | "
            f"Age: {age_gate.reason}"
        ),
        checks={
            "freshness": freshness_gate,
            "visual": visual_gate,
            "age": age_gate,
        },
        recommendations=recommendations,
        rag_context=rag_context,
    )

    return result


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _compute_age_from_date(added_date: str) -> int:
    """Convert ISO date string to days elapsed"""
    added = date.fromisoformat(added_date)
    return (date.today() - added).days
