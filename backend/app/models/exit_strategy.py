from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from datetime import date
from typing import Optional
from pydantic import BaseModel


class ExitPath(str, Enum):
    UPCYCLE = "upcycle"    # Score 40-50: Recipes to use before waste
    SHARE = "share"         # Good condition: Donation to charities
    BIN = "bin"             # Spoiled/unsafe: Disposal protocol


@dataclass
class TripleCheckInput:
    """The three data sources for the Triple-Check guardrail"""
    # Source 1: From existing PantryItem (always available)
    item_id: str
    item_name: str
    category: str
    freshness_score: float
    added_date: str          # ISO date string
    storage: str
    quantity: float

    # Source 2: From visual spoilage detection module (optional, future integration)
    visual_spoilage_detected: bool = False
    visual_confidence: float = 0.5  # 0-1 scale

    # Source 3: age verification (optional, future integration)
    verified_age_days: Optional[int] = None


@dataclass
class TripleCheckGate:
    """Result of each individual check"""
    passed: bool
    confidence: float  # 0-100
    reason: str


@dataclass
class ExitStrategyRecommendation:
    """A specific action the user can take based on exit path"""
    type: str  # "recipe", "charity", "disposal_method"
    title: str
    description: str
    action_key: str  # For calling next agent module
    details: dict = field(default_factory=dict)


@dataclass
class ExitStrategyResult:
    """Final orchestration output from Triple-Check"""
    item_id: str
    item_name: str
    exit_path: ExitPath
    confidence: float
    reasoning: str
    checks: dict  # {"freshness": TripleCheckGate, "visual": ..., "age": ...}
    recommendations: list[ExitStrategyRecommendation] = field(default_factory=list)
    rag_context: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        """Serialize to JSON-compatible dict"""
        return {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "exit_path": self.exit_path.value,
            "confidence": round(self.confidence, 1),
            "reasoning": self.reasoning,
            "checks": {
                k: {
                    "passed": v.passed,
                    "confidence": round(v.confidence, 1),
                    "reason": v.reason,
                }
                for k, v in self.checks.items()
            },
            "recommendations": [
                {
                    "type": r.type,
                    "title": r.title,
                    "description": r.description,
                    "action_key": r.action_key,
                    "details": r.details,
                }
                for r in self.recommendations
            ],
            "rag_context": self.rag_context,
        }


# Pydantic models for API responses
class ExitStrategyResponseModel(BaseModel):
    item_id: str
    item_name: str
    exit_path: str
    confidence: float
    reasoning: str
    checks: dict
    recommendations: list[dict]
    rag_context: dict

    class Config:
        from_attributes = True
