"""
Pure, framework-independent Credit Offer Engine.

Maps score tiers (Bronze, Silver, Gold, Not Yet Eligible) to pre-approved
working capital offers and simulated NBFC terms.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

from backend.a2.offers.rules import load_offer_rules
from backend.a2.validation.models import OfferResult


def get_credit_offer(
    score_band: str,
    member_id: str,
    unlock_date: Optional[str] = None,
) -> OfferResult:
    """
    Generate the canonical OfferResult based on member_id and score_band.

    Deterministic mapping:
      - Gold:   ₹30,000 at 11% APR (36 months)
      - Silver: ₹15,000 at 14% APR (24 months)
      - Bronze:  ₹5,000 at 18% APR (12 months)
      - Below Bronze / Not Yet Eligible / invalid: ₹0 at 0% APR (not eligible)
    """
    if not isinstance(member_id, str) or not member_id.strip():
        raise ValueError("member_id must be a non-empty string")

    rules = load_offer_rules()
    partner_nbfc = rules.get("partner_nbfc_name", "ChitCredit Demo NBFC Partner (Simulated)")
    disclaimer = rules.get("disclaimer", "")
    tier_offers = rules.get("tier_offers", {})

    # Normalize band name
    normalized_band = score_band.strip() if isinstance(score_band, str) else "Not Yet Eligible"

    # Default to not eligible if band is unknown
    tier_info = tier_offers.get(
        normalized_band,
        tier_offers.get("Not Yet Eligible", {
            "eligible_amount": 0,
            "interest_rate": 0.0,
            "term_months": 0,
            "is_eligible": False,
        })
    )

    if unlock_date is None:
        unlock_date = datetime.now(timezone.utc).date().isoformat()

    return OfferResult(
        member_id=member_id,
        eligible_amount=float(tier_info["eligible_amount"]),
        interest_rate=float(tier_info["interest_rate"]),
        unlock_date=unlock_date,
        partner_nbfc=partner_nbfc,
        is_eligible=bool(tier_info["is_eligible"]),
        score_band=normalized_band if normalized_band in tier_offers else "Not Yet Eligible",
        term_months=int(tier_info["term_months"]),
        disclaimer=disclaimer,
    )
