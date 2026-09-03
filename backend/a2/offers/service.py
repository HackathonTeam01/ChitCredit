"""
Public Credit Offer Service interface for A2.

Coordinates looking up a member's score and generating their pre-approved offer.
"""

from __future__ import annotations
from typing import Optional

from backend.a2.integration.data_provider import DataProvider
from backend.a2.offers.engine import get_credit_offer
from backend.a2.scoring.service import ScoreService
from backend.a2.validation.models import OfferResult


class OfferService:
    """Service coordinating credit offer generation from member score."""

    def __init__(
        self,
        score_service: Optional[ScoreService] = None,
        data_provider: Optional[DataProvider] = None,
    ):
        self._score_service = score_service or ScoreService(data_provider=data_provider)

    def get_offer_for_member(
        self,
        member_id: str,
        unlock_date: Optional[str] = None,
    ) -> OfferResult:
        """Fetch member score band and compute tailored credit offer."""
        score_result = self._score_service.get_score_for_member(member_id)
        return get_credit_offer(
            score_band=score_result.score_band,
            member_id=member_id,
            unlock_date=unlock_date,
        )

    def get_offer_for_band(
        self,
        score_band: str,
        member_id: str = "custom",
        unlock_date: Optional[str] = None,
    ) -> OfferResult:
        """Direct credit offer calculation for an explicit score band."""
        return get_credit_offer(
            score_band=score_band,
            member_id=member_id,
            unlock_date=unlock_date,
        )


# Global default instance
default_offer_service = OfferService()
