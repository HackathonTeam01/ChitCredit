"""
A2 Score and Credit Offer API Route handlers.

Thin HTTP adapters delegating completely to ScoreService and OfferService.
No business logic, scoring formulas, or tier mappings are duplicated here.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.a2.offers.service import default_offer_service, OfferService
from backend.a2.scoring.service import default_score_service, ScoreService

router = APIRouter(tags=["Credit Scoring & Offers (A2)"])


@router.get("/member/{member_id}/score", response_model=None)
def get_member_score(
    member_id: str,
    include_breakdown: bool = Query(True, description="Include explainable calculation breakdown"),
) -> Dict[str, Any]:
    """
    Retrieve the canonical Chit Credit Score for a given member.
    Delegates strictly to A2 ScoreService.
    """
    try:
        score_result = default_score_service.get_score_for_member(
            member_id=member_id,
            include_breakdown=include_breakdown,
        )
        return score_result.to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scoring error: {str(exc)}")


@router.get("/member/{member_id}/credit-offer", response_model=None)
def get_member_credit_offer(
    member_id: str,
    unlock_date: Optional[str] = Query(None, description="Optional custom ISO date for offer generation"),
) -> Dict[str, Any]:
    """
    Retrieve the pre-approved NBFC credit offer based on member's score tier.
    Delegates strictly to A2 OfferService.
    """
    try:
        offer_result = default_offer_service.get_offer_for_member(
            member_id=member_id,
            unlock_date=unlock_date,
        )
        return offer_result.to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Offer evaluation error: {str(exc)}")
