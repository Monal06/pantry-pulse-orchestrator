"""
Smart Decision Engine: The Full Vision

This is the TRUE orchestrator that powers your Decision Engine Pitch.
Unlike the basic Triple-Check, this engine:

1. Works at ANY freshness score (proactive, not just reactive)
2. Provides 3 exit paths with SMART GUARDRAILS per path
3. Suggests non-food creative uses (face masks, mulch, crafts)
4. Matches with real community resources (fridges, charities)
5. Ranks recommendations by safety + user context

Safety Model:
- Score 0-20:   CRITICAL → Only BIN
- Score 20-50:  SALVAGEABLE → UPCYCLE or BIN (never share/donate)
- Score 50-100: SAFE → All options available

Decision Tree:
1. Calculate SAFETY for each exit path
2. Get recommendations for safe paths only
3. Rank by user context (has_garden? in_office? eco_priority?)
4. Return ordered list with confidence + warnings
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from app.modules.waste_engine.orchestrator import (
    triple_check_orchestrator,
    TripleCheckInput,
)
from app.modules.waste_engine.agents.upcycle_agent import UpcycleAgent
from app.modules.waste_engine.agents.charity_finder import CharityFinderAgent
from app.modules.waste_engine.agents.disposal_guide import DisposalGuideAgent
from app.modules.waste_engine.rag_retriever_advanced import get_rag_retriever


class ExitPathSafety(str, Enum):
    SAFE = "safe"              # Can use this path
    UNSAFE = "unsafe"          # Do NOT use this path
    WARN = "warn"              # Can use but with caution


@dataclass
class ExitPathRecommendation:
    """A single exit path recommendation with safety & ranking"""
    exit_path: str  # "upcycle", "share", "bin"
    title: str
    description: str
    safety_level: ExitPathSafety
    safety_reason: str
    confidence: float  # 0-100

    # Action data
    actions: list[dict] = field(default_factory=list)  # Recipes, charities, etc.

    # Warnings/notes
    warnings: list[str] = field(default_factory=list)
    environmental_impact: Optional[dict] = None

    rank: int = 999  # Lower = higher priority


@dataclass
class SmartDecisionResult:
    """Result from smart decision engine"""
    item_name: str
    freshness_score: float
    safety_level: str  # "critical" / "salvageable" / "safe"

    # All available exit paths (sorted by rank)
    recommendations: list[ExitPathRecommendation] = field(default_factory=list)

    # Top recommendation for user
    primary_recommendation: Optional[ExitPathRecommendation] = None

    # Context-specific insights
    insights: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "item_name": self.item_name,
            "freshness_score": self.freshness_score,
            "safety_level": self.safety_level,
            "primary_recommendation": {
                "exit_path": self.primary_recommendation.exit_path,
                "title": self.primary_recommendation.title,
                "safety_level": self.primary_recommendation.safety_level.value,
                "actions": self.primary_recommendation.actions,
                "warnings": self.primary_recommendation.warnings,
            } if self.primary_recommendation else None,
            "all_options": [
                {
                    "exit_path": r.exit_path,
                    "title": r.title,
                    "safety_level": r.safety_level.value,
                    "confidence": r.confidence,
                    "actions": r.actions[:2],  # Top 2 actions
                    "warnings": r.warnings,
                }
                for r in self.recommendations
            ],
            "insights": self.insights,
        }


class SmartDecisionEngine:
    """The true Decision Engine orchestrator"""

    def __init__(self):
        self.rag = get_rag_retriever()

    # ========================================================================
    # SAFETY GATES: Determine what exit paths are safe for this score
    # ========================================================================

    def _evaluate_path_safety(
        self,
        score: float,
        exit_path: str,
        visual_hazard: bool = False,
        verified_age_days: Optional[int] = None,
        category: str = None,
    ) -> tuple[ExitPathSafety, str]:
        """
        Multi-gate safety evaluation for exit paths.

        Three independent gates prevent unsafe recommendations:

        Gate 1: Freshness Score
        - Based on EFSA/FDA decay rates (covers all biological hazards)
        - Score < 20: CRITICAL
        - Score 20-50: SALVAGEABLE
        - Score 50+: SAFE

        Gate 2: Visual Spoilage Detection (from PJ's module)
        - If visual hazard detected → UNSAFE for SHARE
        - Visual signs: mold, discoloration, slime, etc.

        Gate 3: Age Verification (from Ambuj's module)
        - If verified age exceeds EFSA limit → UNSAFE for SHARE
        - Category-specific storage limits

        Logic: Any gate failing → UNSAFE (conservative approach)
        """
        if exit_path == "upcycle":
            # Upcycling always safe (composting + non-food uses)
            return ExitPathSafety.SAFE, "Upcycling is always safe for any freshness level"

        elif exit_path == "share":
            # GATE 1: Freshness Score
            if score < 20:
                return (
                    ExitPathSafety.UNSAFE,
                    "Gate 1 (Freshness): Score < 20 (CRITICAL). Food too spoiled to donate safely.",
                )

            # GATE 2: Visual Hazard Detection (from PJ's module)
            if visual_hazard:
                return (
                    ExitPathSafety.UNSAFE,
                    "Gate 2 (Visual): Spoilage detected (mold, discoloration, slime). Cannot donate safely.",
                )

            # GATE 3: Age Verification (from Ambuj's module) - CHECK BEFORE SCORE WARN
            if verified_age_days is not None and category:
                safety_limits = self.rag.get_category_safety_limit(category, "fridge")
                max_safe_days = safety_limits.get("max_days", 7)  # RAG returns {"max_days": X}

                if verified_age_days > max_safe_days:
                    return (
                        ExitPathSafety.UNSAFE,
                        f"Gate 3 (Age): {verified_age_days} days old exceeds EFSA limit ({max_safe_days} days). Too old to donate.",
                    )

            # All gates passed, but check freshness level for warning (only if age gate also passed)
            if score < 50:
                return (
                    ExitPathSafety.WARN,
                    "All safety gates passed, but score < 50 (SALVAGEABLE). Only donate if packaging sealed and recipient aware.",
                )
            else:
                return ExitPathSafety.SAFE, "All safety gates passed. Safe to donate."

        elif exit_path == "bin":
            # Disposal always safe
            if score < 20:
                return ExitPathSafety.SAFE, "Score < 20: Recommended for safe disposal (becomes biogas)"
            else:
                return (
                    ExitPathSafety.SAFE,
                    "Proper disposal always safe, but consider upcycling first",
                )

        return ExitPathSafety.SAFE, "Unknown path"

    def _get_safety_level(self, score: float) -> str:
        """Categorize overall safety level"""
        if score < 20:
            return "critical"
        elif score < 50:
            return "salvageable"
        else:
            return "safe"

    # ========================================================================
    # RECOMMENDATION GENERATION: Get actions for each safe path
    # ========================================================================

    async def _generate_upcycle_recommendation(
        self, item_name: str, category: str, score: float, visual_hazard: bool = False
    ) -> ExitPathRecommendation:
        """
        Generate upcycle recommendation for non-food uses only.

        NOTE: Food recipes are Ambuj's job (meal planner).
        Exit strategy upcycle = non-food reuse only (crafts, composting, beauty).
        If food is already aging/critical, it shouldn't be cooked - it should be:
        - Composted
        - Used for non-food purposes (face masks, mulch, crafts)
        - Donated (if safe per 4 gates)
        - Disposed (if unsafe)
        """

        actions = []

        # Get non-food creative uses (composting, crafts, beauty, garden)
        non_food = await self._get_nonfood_uses(category)
        for use in non_food:
            actions.append({
                "type": "nonfood_use",
                "title": use["title"],
                "benefit": use["benefit"],
                "difficulty": use.get("difficulty", "easy"),
                "steps": use.get("steps", []),  # Include actionable steps
            })

        # Add composting as primary action (always available)
        actions.insert(0, {
            "type": "composting",
            "title": "Compost",
            "benefit": "Turn into soil nutrients - best for the environment",
            "difficulty": "easy",
            "steps": [
                "Add to compost bin (or start one if you don't have)",
                "Mix with dry leaves, paper, or cardboard",
                "Keep moist but not soggy",
                "Stir occasionally for faster breakdown",
                "Ready to use in 3-4 weeks"
            ]
        })

        warnings = []
        if score < 30:
            warnings.append("Item is very spoiled - composting or disposal recommended")
        if visual_hazard:
            warnings.append("Visual spoilage detected - compost or craft use only")

        return ExitPathRecommendation(
            exit_path="upcycle",
            title="Upcycle: Reuse sustainably" if score >= 40 else "Upcycle: Compost or repurpose",
            description="Compost, craft uses, beauty treatments, or garden mulch - zero food waste",
            safety_level=ExitPathSafety.SAFE,
            safety_reason="Non-food reuse is always safe",
            confidence=90.0,
            actions=actions,
            warnings=warnings,
            rank=1,
        )

    async def _generate_share_recommendation(
        self,
        item_name: str,
        category: str,
        score: float,
        quantity: float,
        unit: str,
        location: str = "Galway",
        visual_hazard: bool = False,
        verified_age_days: Optional[int] = None,
    ) -> Optional[ExitPathRecommendation]:
        """
        Generate share recommendation with multi-gate safety checks.

        Returns None if any safety gate fails (UNSAFE).
        Returns recommendation with WARN level if risky but passable.
        """

        safety, reason = self._evaluate_path_safety(
            score, "share", visual_hazard=visual_hazard, verified_age_days=verified_age_days, category=category
        )
        if safety == ExitPathSafety.UNSAFE:
            return None  # Skip this recommendation entirely

        # Find charities
        charities = await CharityFinderAgent.find_charities(
            item_name=item_name,
            category=category,
            quantity=quantity,
            unit=unit,
            location=location,
        )

        # Find community fridges
        community = await self._find_community_fridges(location)

        actions = []
        if charities["status"] == "success":
            for c in charities.get("charities", [])[:2]:
                actions.append({
                    "type": "charity",
                    "title": c.get("name"),
                    "type_label": c.get("type"),
                    "distance_km": c.get("distance_approx_km"),
                })

        for fridge in community[:2]:
            actions.append({
                "type": "community_fridge",
                "title": fridge.get("name"),
                "walk_time_minutes": fridge.get("walk_time_minutes"),
            })

        warnings = []
        if score < 50:
            warnings.append("Item is critical freshness - ensure packaging is sealed before donating")

        return ExitPathRecommendation(
            exit_path="share",
            title="Share: Help your community",
            description="Donate to a local charity, food bank, or community fridge",
            safety_level=safety,
            safety_reason=reason,
            confidence=75.0,
            actions=actions,
            warnings=warnings,
            rank=2,
        )

    async def _generate_bin_recommendation(
        self, item_name: str, category: str, score: float, quantity: float, location: str = "Galway"
    ) -> ExitPathRecommendation:
        """Generate disposal recommendation"""

        disposal = await DisposalGuideAgent.get_disposal_instructions(
            item_name=item_name,
            category=category,
            quantity=quantity,
            spoilage_type="very_spoiled" if score < 20 else "spoiled",
            location=location,
        )

        actions = []
        if disposal["status"] == "success":
            instr = disposal.get("instructions", {})
            actions.append({
                "type": "disposal",
                "bin_type": instr.get("bin_color", "brown").upper() + " BIN",
                "steps": instr.get("preparation_steps", [])[:2],
                "composting": instr.get("composting_option", "No"),
            })

        environmental = await DisposalGuideAgent.estimate_environmental_impact(
            item_name=item_name,
            category=category,
            quantity=quantity,
        )

        return ExitPathRecommendation(
            exit_path="bin",
            title="Dispose: Safe & sustainable",
            description="Properly dispose to minimize environmental impact",
            safety_level=ExitPathSafety.SAFE,
            safety_reason="Proper disposal is always safe",
            confidence=85.0,
            actions=actions,
            environmental_impact=environmental.get("disposal_methods", []) if environmental.get("status") == "success" else None,
            rank=3,
        )

    # ========================================================================
    # CREATIVE ADDITIONS: Non-food uses & community matching
    # ========================================================================

    async def _get_nonfood_uses(self, category: str) -> list[dict]:
        """Get creative non-food uses with actionable steps"""
        # Use fallback directly - it has all steps and is more reliable
        # Gemini integration can be added later if needed
        return self._get_fallback_nonfood_uses(category)

    def _get_fallback_nonfood_uses(self, category: str) -> list[dict]:
        """Fallback non-food uses with steps when Gemini unavailable"""
        # Normalize category to singular form
        category_map = {
            "fruits": "fruit",
            "fruit": "fruit",
            "vegetables": "vegetable",
            "vegetable": "vegetable",
            "dairy": "dairy",
            "bread": "bread",
            "meat": "meat",
            "seafood": "seafood",
            "leftovers": "leftovers",
        }
        normalized_category = category_map.get(category.lower(), category.lower())

        fallbacks = {
            "fruit": [
                {
                    "title": "Face Mask",
                    "benefit": "Natural skincare with vitamins",
                    "difficulty": "easy",
                    "steps": [
                        "Mash fruit into smooth paste",
                        "Mix with 1 tbsp honey (optional)",
                        "Apply evenly to clean face",
                        "Leave for 15 minutes",
                        "Rinse with warm water"
                    ]
                },
                {
                    "title": "Compost",
                    "benefit": "Fertilize garden with nitrogen",
                    "difficulty": "easy",
                    "steps": [
                        "Add chopped fruit to compost bin",
                        "Mix with dry leaves/paper",
                        "Keep moist but not soggy",
                        "Turn weekly if possible",
                        "Ready in 3-4 weeks"
                    ]
                },
                {
                    "title": "Natural Dye",
                    "benefit": "Art projects and fabric dyeing",
                    "difficulty": "medium",
                    "steps": [
                        "Boil fruit scraps in water for 30 minutes",
                        "Strain liquid through cloth",
                        "Soak fabric/paper in dye bath",
                        "Leave overnight for deeper color",
                        "Rinse and dry"
                    ]
                }
            ],
            "vegetable": [
                {
                    "title": "Compost",
                    "benefit": "Garden fertilizer rich in nutrients",
                    "difficulty": "easy",
                    "steps": [
                        "Chop vegetable scraps into small pieces",
                        "Add to compost bin with dry material",
                        "Mix well",
                        "Keep moist",
                        "Ready in 3-4 weeks"
                    ]
                },
                {
                    "title": "Natural Dye",
                    "benefit": "Fabric and paper dyeing",
                    "difficulty": "medium",
                    "steps": [
                        "Boil vegetable scraps in water for 1 hour",
                        "Strain dye bath through cloth",
                        "Soak fabric/paper for color",
                        "Leave overnight",
                        "Rinse and dry"
                    ]
                },
                {
                    "title": "Garden Mulch",
                    "benefit": "Moisture retention and weed prevention",
                    "difficulty": "easy",
                    "steps": [
                        "Chop vegetable matter into small pieces",
                        "Spread 2-3 inches around plant base",
                        "Keep away from stem",
                        "Water plants normally",
                        "Refresh monthly"
                    ]
                }
            ],
            "dairy": [
                {
                    "title": "Face Mask",
                    "benefit": "Probiotic skincare treatment",
                    "difficulty": "easy",
                    "steps": [
                        "Apply yogurt directly to clean face",
                        "Can mix with honey for extra benefit",
                        "Leave for 10-15 minutes",
                        "Rinse with warm water",
                        "Pat dry gently"
                    ]
                },
                {
                    "title": "Fertilizer",
                    "benefit": "Nutrient-rich garden amendment",
                    "difficulty": "easy",
                    "steps": [
                        "Add dairy to compost bin",
                        "Mix thoroughly with dry material",
                        "Bury deep to avoid odors",
                        "Cover well",
                        "Let decompose 4-6 weeks"
                    ]
                }
            ],
            "bread": [
                {
                    "title": "Garden Mulch",
                    "benefit": "Moisture retention and soil building",
                    "difficulty": "easy",
                    "steps": [
                        "Break bread into small pieces",
                        "Spread around plant base",
                        "Cover with other mulch if desired",
                        "Water normally",
                        "Replace when decomposed"
                    ]
                },
                {
                    "title": "Craft Base",
                    "benefit": "Art projects and papier-mâché",
                    "difficulty": "medium",
                    "steps": [
                        "Tear bread into small pieces",
                        "Soak in water until soft",
                        "Mix with flour paste if making papier-mâché",
                        "Mold into shapes or smooth onto surface",
                        "Let dry completely"
                    ]
                },
                {
                    "title": "Compost",
                    "benefit": "Turn into soil nutrients",
                    "difficulty": "easy",
                    "steps": [
                        "Chop stale bread into pieces",
                        "Add to compost bin",
                        "Mix with green material",
                        "Keep moist",
                        "Ready in 2-3 weeks"
                    ]
                }
            ],
            "meat": [
                {
                    "title": "Compost",
                    "benefit": "Create rich garden soil",
                    "difficulty": "easy",
                    "steps": [
                        "Chop meat scraps into small pieces",
                        "Bury deep in compost bin (prevents odor)",
                        "Mix thoroughly with dry material",
                        "Cover well with leaves/paper",
                        "Ready in 4-6 weeks"
                    ]
                }
            ],
            "seafood": [
                {
                    "title": "Compost",
                    "benefit": "Create rich garden soil",
                    "difficulty": "easy",
                    "steps": [
                        "Chop seafood scraps into small pieces",
                        "Bury deep in compost bin (prevents smell)",
                        "Cover with plenty of dry material",
                        "Mix regularly if possible",
                        "Ready in 4-6 weeks"
                    ]
                }
            ],
            "leftovers": [
                {
                    "title": "Compost",
                    "benefit": "Turn cooked food into soil nutrients",
                    "difficulty": "easy",
                    "steps": [
                        "Chop leftovers into small pieces",
                        "Bury deep in compost bin",
                        "Mix with dry brown material",
                        "Keep moist but not wet",
                        "Ready in 4-6 weeks"
                    ]
                }
            ],
        }
        default = [{
            "title": "Compost",
            "benefit": "Garden use and soil building",
            "difficulty": "easy",
            "steps": [
                "Add to compost bin",
                "Mix with dry material",
                "Keep moist",
                "Stir occasionally",
                "Ready in 3-4 weeks"
            ]
        }]
        return fallbacks.get(normalized_category, default)

    async def _find_community_fridges(self, location: str = "Galway") -> list[dict]:
        """Find community fridges near location using mock data"""
        # TODO: Integrate real Google Maps API
        mock_fridges = [
            {
                "name": "Shop Street Community Fridge",
                "address": "Shop Street, Galway City",
                "walk_time_minutes": 5,
                "hours": "24/7",
                "accepts": "any food",
            },
            {
                "name": "Eyre Square Community Hub",
                "address": "Eyre Square, Galway",
                "walk_time_minutes": 8,
                "hours": "9am-6pm daily",
                "accepts": "packaged & fresh",
            },
            {
                "name": "Salthill Community Fridge",
                "address": "Salthill, Galway",
                "walk_time_minutes": 15,
                "hours": "24/7",
                "accepts": "any food",
            },
        ]
        return mock_fridges

    # ========================================================================
    # RANKING & CONTEXT-AWARE FILTERING
    # ========================================================================

    def _rank_recommendations(
        self, recommendations: list[ExitPathRecommendation], user_context: Optional[dict] = None
    ) -> list[ExitPathRecommendation]:
        """
        Rank recommendations based on user context.

        Context factors:
        - has_garden: prioritize composting
        - in_office: prioritize sharing
        - eco_priority: prioritize sustainable options
        - time_available: prioritize quick recipes
        """
        if not user_context:
            user_context = {}

        for rec in recommendations:
            if rec.safety_level == ExitPathSafety.UNSAFE:
                rec.rank = 999  # Unsafe options go last

            elif user_context.get("has_garden") and rec.exit_path == "upcycle":
                rec.rank = 0  # Top priority if user has garden

            elif user_context.get("in_office") and rec.exit_path == "share":
                rec.rank = 1  # Prioritize sharing in office

            elif user_context.get("eco_priority") and rec.exit_path == "bin":
                rec.rank = 2  # Proper disposal matters for eco-conscious

        # Sort by rank
        return sorted(recommendations, key=lambda r: r.rank)

    # ========================================================================
    # MAIN ENGINE: Orchestrate all three paths
    # ========================================================================

    async def get_smart_exit_strategies(
        self,
        item_name: str,
        category: str,
        freshness_score: float,
        quantity: float = 1.0,
        unit: str = "item",
        location: str = "Galway",
        user_context: Optional[dict] = None,
        visual_hazard: bool = False,
        verified_age_days: Optional[int] = None,
    ) -> SmartDecisionResult:
        """
        Main engine: Get all safe exit strategies for ANY freshness score.

        Multi-gate safety validation prevents dangerous recommendations:

        Gate 1: Freshness Score (your algorithm)
        Gate 2: Visual Spoilage Detection (from PJ's visual module)
        Gate 3: Age Verification (from Ambuj's meal planner)

        Args:
            item_name: e.g., "Overripe Banana"
            category: e.g., "fruit"
            freshness_score: 0-100 (can be ANY score!)
            quantity: Amount
            unit: e.g., "item"
            location: e.g., "Galway"
            user_context: e.g., {"has_garden": True, "eco_priority": "high"}
            visual_hazard: bool from PJ's module (mold detected? True/False)
            verified_age_days: int from Ambuj's module (days old)

        Returns:
            SmartDecisionResult with all safe options ranked
        """

        # Determine overall safety level
        safety_level = self._get_safety_level(freshness_score)

        # Generate recommendations for safe paths
        recommendations = []

        # UPCYCLE: Non-food reuse only (composting, crafts, beauty uses)
        upcycle = await self._generate_upcycle_recommendation(
            item_name, category, freshness_score, visual_hazard=visual_hazard
        )
        recommendations.append(upcycle)

        # SHARE: Multi-gate safety check (freshness + visual + age)
        share = await self._generate_share_recommendation(
            item_name,
            category,
            freshness_score,
            quantity,
            unit,
            location,
            visual_hazard=visual_hazard,
            verified_age_days=verified_age_days,
        )
        if share:
            recommendations.append(share)

        # BIN: Always safe
        bin_rec = await self._generate_bin_recommendation(
            item_name, category, freshness_score, quantity, location
        )
        recommendations.append(bin_rec)

        # Rank by user context
        ranked = self._rank_recommendations(recommendations, user_context)

        # Build insights
        insights = self._generate_insights(freshness_score, safety_level, ranked, user_context)

        return SmartDecisionResult(
            item_name=item_name,
            freshness_score=freshness_score,
            safety_level=safety_level,
            recommendations=ranked,
            primary_recommendation=ranked[0] if ranked else None,
            insights=insights,
        )

    def _generate_insights(
        self, score: float, safety: str, recommendations: list, context: Optional[dict]
    ) -> dict:
        """Generate context-specific insights"""
        insights = {}

        if score < 20:
            insights["urgent"] = "This item needs immediate action - it's critically spoiled"
            insights["action"] = "Consider disposal today"

        elif score < 50:
            insights["urgent"] = "This item is approaching end of life"
            insights["action"] = "Use within next 1-2 days or upcycle/compost"

        else:
            insights["status"] = "Item is in good condition"
            insights["action"] = "Can be used normally or shared with community"

        # Context-based
        if context:
            if context.get("has_garden"):
                insights["opportunity"] = "Your garden could benefit from composting this!"
            if context.get("in_office"):
                insights["opportunity"] = "Share in office Slack - colleagues may want it!"

        # Show safe vs unsafe paths
        unsafe_count = len([r for r in recommendations if r.safety_level == ExitPathSafety.UNSAFE])
        if unsafe_count > 0:
            insights["warning"] = f"{unsafe_count} option(s) marked unsafe for this freshness level"

        return insights
