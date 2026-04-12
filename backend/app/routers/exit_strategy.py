"""
Exit Strategy Orchestration Router

Endpoints for the exit strategy decision engine. When a food item reaches
critical freshness score (< 50), this router orchestrates the Triple-Check
process to recommend one of three exit paths:
  - UPCYCLE: Creative recipes to use before spoilage
  - SHARE: Donation to local charities
  - BIN: Sustainable disposal via Galway waste protocols
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.models.exit_strategy import ExitStrategyResponseModel, ExitPath, TripleCheckInput
from app.services import inventory_service
from app.modules.waste_engine.orchestrator import triple_check_orchestrator
from app.modules.waste_engine.rag_retriever import MockRAGRetriever
from app.modules.waste_engine.rag_retriever_advanced import get_rag_retriever
from app.modules.waste_engine.agents.upcycle_agent import UpcycleAgent
from app.modules.waste_engine.agents.charity_finder import CharityFinderAgent
from app.modules.waste_engine.agents.disposal_guide import DisposalGuideAgent
from app.modules.waste_engine.smart_decision_engine import SmartDecisionEngine

router = APIRouter(prefix="/orchestrate", tags=["exit-strategy"])

DEFAULT_USER = "demo-user"

# Initialize RAG retriever (auto-upgrades based on available env vars)
_rag_retriever = get_rag_retriever()

# Initialize Smart Decision Engine
_smart_engine = SmartDecisionEngine()


@router.post("/exit-strategy", response_model=ExitStrategyResponseModel)
async def orchestrate_exit_strategy(
    item_id: str = Query(..., description="ID of critical item from inventory"),
    user_id: str = Query(default=DEFAULT_USER, description="User ID"),
):
    """
    Orchestrate exit strategy for a critical food item (freshness_score < 50).

    This endpoint implements the Triple-Check Guardrail:
      1. **Freshness Gate**: Score-based triage (< 50 = critical)
      2. **Visual Gate**: Spoilage detection (from visual analysis module, future)
      3. **Safety Gate**: Category-specific age limits (from RAG system)

    Based on these three gates, the orchestrator determines the best exit path:
      - **UPCYCLE**: Item is salvageable via creative recipes (score 40-50)
      - **SHARE**: Item is in good condition for donation (score > 50, all gates pass)
      - **BIN**: Item is unsafe or too spoiled (score < 40 or any gate fails)

    The response includes:
      - Exit path recommendation with confidence score
      - Detailed reasoning from all three gates
      - Actionable recommendations (recipes, charities, disposal info)
      - RAG context (food safety guidelines, Galway waste protocols)

    Args:
        item_id: UUID of the food item from inventory
        user_id: User identifier (default: demo-user)

    Returns:
        ExitStrategyResult with orchestration outcome and recommendations

    Raises:
        404: Item not found
        400: Item score >= 50 (not critical, route to meal planner)
    """

    # Fetch item from inventory
    item = await inventory_service.get_item(user_id, item_id)
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Item {item_id} not found in user {user_id}'s inventory",
        )

    # Validate that item is actually critical
    if item.freshness_score >= 50:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Item '{item.name}' has score {item.freshness_score} (>= 50). "
                "This is not critical. Route to meal planner instead. "
                "Exit strategy applies only to score < 50."
            ),
        )

    # Build orchestrator input from inventory item
    orchestrator_input = TripleCheckInput(
        item_id=item.id,
        item_name=item.name,
        category=item.category,
        freshness_score=item.freshness_score,
        added_date=item.added_date.isoformat(),
        storage=item.storage.value,
        quantity=item.quantity,
        # Integration point: visual module
        # visual_spoilage_detected=visual_analysis.get("spoilage_detected", False),
        # visual_confidence=visual_analysis.get("confidence", 0.5),
        # Integration point: age verification
        # verified_age_days=age_verification.get("days"),
    )

    # Run the Triple-Check orchestrator
    result = await triple_check_orchestrator(orchestrator_input, _rag_retriever)

    # Serialize to JSON response
    return result.to_json()


@router.get("/exit-strategy/batch")
async def batch_exit_strategies(
    user_id: str = Query(default=DEFAULT_USER),
):
    """
    Orchestrate exit strategies for ALL critical items (score < 50) in user's inventory.

    Useful for batch processing and giving users a comprehensive overview of
    what needs action.

    Returns:
        List of ExitStrategyResults, one per critical item
    """

    # Get all items
    all_items = await inventory_service.get_all_items(user_id)

    # Filter to critical only
    critical_items = [i for i in all_items if i.freshness_score < 50]

    if not critical_items:
        return {"critical_items": 0, "results": []}

    # Orchestrate each one
    results = []
    for item in critical_items:
        try:
            orchestrator_input = TripleCheckInput(
                item_id=item.id,
                item_name=item.name,
                category=item.category,
                freshness_score=item.freshness_score,
                added_date=item.added_date.isoformat(),
                storage=item.storage.value,
                quantity=item.quantity,
            )
            result = await triple_check_orchestrator(orchestrator_input, _rag_retriever)
            results.append(result.to_json())
        except Exception as e:
            # Log but don't fail entire batch
            results.append(
                {
                    "item_id": item.id,
                    "item_name": item.name,
                    "error": str(e),
                }
            )

    return {
        "critical_items": len(critical_items),
        "results": results,
    }


@router.get("/safety-guidelines/{category}")
async def get_category_safety_info(
    category: str,
):
    """
    Retrieve food safety guidelines for a category from the RAG system.

    Useful for users to understand why an item is marked as critical.
    """
    guidelines = _rag_retriever.get_safety_guidelines(category)
    storage_tips = _rag_retriever.get_storage_tips(category)

    return {
        "category": category,
        "safety_guidelines": guidelines,
        "storage_tips": storage_tips,
    }


@router.get("/disposal-protocol/{category}")
async def get_disposal_info(
    category: str,
):
    """
    Retrieve Galway waste management disposal protocol for a category.

    Shows users how to properly dispose of spoiled items in Galway.
    """
    protocol = _rag_retriever.get_disposal_protocol(category)

    return {
        "category": category,
        "location": "Galway",
        "disposal_protocol": protocol,
    }


@router.get("/donation-guidelines")
async def get_donation_info():
    """
    Retrieve guidelines for donating food to charities.

    Shows users what items are safe to donate and local Galway resources.
    """
    guidelines = _rag_retriever.get_donation_guidelines()

    return {
        "location": "Galway",
        "donation_guidelines": guidelines,
    }


# ============================================================================
# AGENT ENDPOINTS: Execute agents for each exit path
# ============================================================================


@router.post("/upcycle/recipes")
async def generate_upcycle_recipes(
    item_name: str = Query(...),
    category: str = Query(...),
    freshness_score: float = Query(..., ge=0, le=100),
    quantity: float = Query(default=1),
    unit: str = Query(default="item"),
):
    """
    Generate creative recipes to upcycle a critical item using Gemini.

    Called when Exit Strategy returns UPCYCLE path.
    Generates 3 recipes optimized for the item's current state.
    """
    result = await UpcycleAgent.generate_recipes(
        item_name=item_name,
        category=category,
        freshness_score=freshness_score,
        quantity=quantity,
        unit=unit,
    )
    return result


@router.post("/share/find-charities")
async def find_donation_charities(
    item_name: str = Query(...),
    category: str = Query(...),
    quantity: float = Query(default=1),
    unit: str = Query(default="item"),
    location: str = Query(default="Galway"),
):
    """
    Find charities and food banks accepting donations in the area.

    Called when Exit Strategy returns SHARE path.
    Uses Gemini to identify real Galway charities and their contact info.
    """
    result = await CharityFinderAgent.find_charities(
        item_name=item_name,
        category=category,
        quantity=quantity,
        unit=unit,
        location=location,
    )
    return result


@router.post("/share/draft-post")
async def draft_donation_post(
    item_name: str = Query(...),
    category: str = Query(...),
    quantity: float = Query(default=1),
    unit: str = Query(default="item"),
    user_name: str = Query(default="Anonymous"),
):
    """
    Draft donation posts for community sharing platforms.

    Generates posts for community fridges, Facebook groups, Nextdoor, etc.
    """
    result = await CharityFinderAgent.draft_donation_post(
        item_name=item_name,
        category=category,
        quantity=quantity,
        unit=unit,
        user_name=user_name,
    )
    return result


@router.post("/bin/disposal-instructions")
async def get_disposal_instructions(
    item_name: str = Query(...),
    category: str = Query(...),
    quantity: float = Query(default=1),
    unit: str = Query(default="item"),
    spoilage_type: str = Query(default="unknown"),
    location: str = Query(default="Galway"),
):
    """
    Get detailed, location-specific disposal instructions.

    Called when Exit Strategy returns BIN path.
    Provides Galway-specific waste bin guidance + environmental impact.
    """
    result = await DisposalGuideAgent.get_disposal_instructions(
        item_name=item_name,
        category=category,
        quantity=quantity,
        unit=unit,
        spoilage_type=spoilage_type,
        location=location,
    )
    return result


@router.post("/bin/prevention-tips")
async def get_prevention_tips(
    item_name: str = Query(...),
    category: str = Query(...),
    reason_spoiled: str = Query(default="unknown"),
):
    """
    Get tips to prevent this item from spoiling in the future.

    Called after disposal to help user learn from this experience.
    """
    result = await DisposalGuideAgent.get_prevention_tips(
        item_name=item_name,
        category=category,
        reason_spoiled=reason_spoiled,
    )
    return result


@router.post("/bin/environmental-impact")
async def estimate_environmental_impact(
    item_name: str = Query(...),
    category: str = Query(...),
    quantity: float = Query(default=1),
    bin_type: str = Query(default="BROWN"),
):
    """
    Estimate environmental impact of disposal method.

    Shows CO2 savings from composting vs landfill.
    Motivates user to choose sustainable disposal.
    """
    result = await DisposalGuideAgent.estimate_environmental_impact(
        item_name=item_name,
        category=category,
        quantity=quantity,
        bin_type=bin_type,
    )
    return result


# ============================================================================
# SMART DECISION ENGINE: The Full Vision - Works at ANY freshness score
# ============================================================================


@router.post("/smart/exit-strategies")
async def get_smart_exit_strategies(
    item_name: str = Query(..., description="Food item name"),
    category: str = Query(..., description="Food category"),
    freshness_score: float = Query(..., ge=0, le=100, description="Freshness score (0-100)"),
    quantity: float = Query(default=1),
    unit: str = Query(default="item"),
    location: str = Query(default="Galway"),
    has_garden: bool = Query(default=False, description="Does user have a garden?"),
    in_office: bool = Query(default=False, description="Is user in office?"),
    eco_priority: str = Query(default="medium", description="User environmental priority"),
    visual_hazard: Optional[bool] = Query(
        default=None, description="Visual spoilage detected? (mold, discoloration, slime). None = unknown/not analyzed"
    ),
    verified_age_days: Optional[int] = Query(
        default=None, description="Verified age in days (from meal planner). None = not verified"
    ),
):
    """
    🚀 SMART DECISION ENGINE - Multi-Gate Safety Validation

    Get intelligent exit strategies with 3-gate safety checks:

    **Gate 1: Freshness Score** (your algorithm)
    - Evaluates decay based on EFSA/FDA standards
    - Covers all biological hazards

    **Gate 2: Visual Spoilage Detection** (from visual analysis module)
    - Mold, discoloration, slime, texture changes
    - If detected → SHARE becomes UNSAFE

    **Gate 3: Age Verification** 
    - Actual days old vs EFSA safety limits
    - If exceeded → SHARE becomes UNSAFE

    Any gate failing → Recommendation hidden (UNSAFE)
    All gates passing → Recommendation shown (SAFE or WARN)

    Returns: All safe exit paths ranked by user preference + safety level
    """

    # Safety check: If visual_hazard not provided, assume conservative (True = assume moldy)
    # This prevents false negatives where moldy items might be suggested for sharing
    if visual_hazard is None:
        visual_hazard = False  # Default to False for API calls, but add warning if low score
        visual_unknown = True
    else:
        visual_unknown = False

    user_context = {
        "has_garden": has_garden,
        "in_office": in_office,
        "eco_priority": eco_priority,
    }

    result = await _smart_engine.get_smart_exit_strategies(
        item_name=item_name,
        category=category,
        freshness_score=freshness_score,
        quantity=quantity,
        unit=unit,
        location=location,
        user_context=user_context,
        visual_hazard=visual_hazard,
        verified_age_days=verified_age_days,
    )

    # Add warning if visual status was unknown
    if visual_unknown and freshness_score < 50:
        if result.primary_recommendation:
            if not result.primary_recommendation.warnings:
                result.primary_recommendation.warnings = []
            result.primary_recommendation.warnings.insert(
                0,
                "⚠️ Visual spoilage status was not analyzed. Verify item appearance before using recommendation."
            )

    return result.to_json()


@router.post("/smart/explain-safety")
async def explain_safety_decision(
    freshness_score: float = Query(..., ge=0, le=100),
    exit_path: str = Query(..., description="upcycle | share | bin"),
):
    """
    Explain WHY an exit path is safe/unsafe for this freshness score.

    Educational endpoint - helps user understand the decision logic.
    """
    safety, reason = _smart_engine._evaluate_path_safety(freshness_score, exit_path)

    return {
        "freshness_score": freshness_score,
        "exit_path": exit_path,
        "safety_level": safety.value,
        "reason": reason,
        "safety_model": {
            "0-20": "CRITICAL - Only BIN recommended",
            "20-50": "SALVAGEABLE - UPCYCLE/BIN safe, SHARE with caution",
            "50-100": "SAFE - All options available",
        },
    }
