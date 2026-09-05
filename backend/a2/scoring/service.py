"""
Public Score Service interface for A2.

Exposes high-level methods to evaluate a member's score using an underlying
DataProvider and the pure scoring engine.
"""

from __future__ import annotations
from typing import Optional

from backend.a2.integration.data_provider import DataProvider, get_default_data_provider
from backend.a2.scoring.engine import calculate_score, calculate_score_band
from backend.a2.validation.models import ScoreInput, ScoreResult


class ScoreService:
    """Service layer coordinating data extraction and score calculation."""

    def __init__(self, data_provider: Optional[DataProvider] = None):
        self._provider = data_provider or get_default_data_provider()

    def get_score_for_member(self, member_id: str, include_breakdown: bool = True) -> ScoreResult:
        """Fetch member data from provider and calculate canonical Chit Credit Score."""
        score_input = self._provider.get_member_score_inputs(member_id)
        return calculate_score(
            on_time_pct=score_input.on_time_pct,
            streak_count=score_input.streak_count,
            tenure_cycles=score_input.tenure_cycles,
            missed_payment_count=score_input.missed_payment_count,
            member_id=member_id,
            include_breakdown=include_breakdown,
        )

    def calculate_custom_score(
        self,
        on_time_pct: float,
        streak_count: int,
        tenure_cycles: int,
        missed_payment_count: int = 0,
        member_id: str = "custom",
        include_breakdown: bool = True,
    ) -> ScoreResult:
        """Direct calculation helper bypassing provider lookup."""
        return calculate_score(
            on_time_pct=on_time_pct,
            streak_count=streak_count,
            tenure_cycles=tenure_cycles,
            missed_payment_count=missed_payment_count,
            member_id=member_id,
            include_breakdown=include_breakdown,
        )


# Global singleton instance with default provider for easy importing
default_score_service = ScoreService()
