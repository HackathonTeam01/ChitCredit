"""
Domain data models and contract validation structures for Person A2.
Pure Python dataclasses with serialization and dictionary representations,
independent of any specific web framework or ORM.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ScoreInput:
    """Raw metric inputs required to compute Chit Credit Score."""
    member_id: str
    on_time_pct: float
    streak_count: int
    tenure_cycles: int
    missed_payment_count: int = 0

    def validate(self) -> None:
        """Validate input ranges and logical bounds."""
        if not isinstance(self.member_id, str) or not self.member_id.strip():
            raise ValueError("member_id must be a non-empty string")
        if not (0.0 <= self.on_time_pct <= 100.0):
            raise ValueError(f"on_time_pct must be between 0 and 100, got {self.on_time_pct}")
        if self.streak_count < 0:
            raise ValueError(f"streak_count cannot be negative, got {self.streak_count}")
        if self.tenure_cycles < 0:
            raise ValueError(f"tenure_cycles cannot be negative, got {self.tenure_cycles}")
        if self.missed_payment_count < 0:
            raise ValueError(f"missed_payment_count cannot be negative, got {self.missed_payment_count}")


@dataclass(frozen=True)
class ScoreBreakdown:
    """Detailed mathematical breakdown of score components."""
    on_time_component: float
    streak_component: float
    tenure_component: float
    missed_payment_penalty: float
    raw_score: float
    clamped_score: int
    weights: Dict[str, float]
    normalization_convention: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScoreResult:
    """Canonical Chit Credit Score contract output."""
    member_id: str
    on_time_pct: float
    streak_count: int
    tenure_cycles: int
    score_value: int
    score_band: str
    breakdown: Optional[ScoreBreakdown] = None

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "member_id": self.member_id,
            "on_time_pct": self.on_time_pct,
            "streak_count": self.streak_count,
            "tenure_cycles": self.tenure_cycles,
            "score_value": self.score_value,
            "score_band": self.score_band,
        }
        if self.breakdown is not None:
            res["breakdown"] = self.breakdown.to_dict()
        return res


@dataclass(frozen=True)
class OfferResult:
    """Canonical Credit Offer contract output."""
    member_id: str
    eligible_amount: float
    interest_rate: float
    unlock_date: str
    partner_nbfc: str
    is_eligible: bool = True
    score_band: str = "Bronze"
    term_months: int = 12
    disclaimer: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "member_id": self.member_id,
            "eligible_amount": self.eligible_amount,
            "interest_rate": self.interest_rate,
            "unlock_date": self.unlock_date,
            "partner_nbfc": self.partner_nbfc,
            "is_eligible": self.is_eligible,
            "score_band": self.score_band,
            "term_months": self.term_months,
            "disclaimer": self.disclaimer,
        }
