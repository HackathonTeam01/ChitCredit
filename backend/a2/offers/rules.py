"""
Centralized credit offer rules and configuration loader.
Reads rules directly from contracts/credit/offer_rules.json with fallback defaults.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_NBFC_NAME = "ChitCredit Demo NBFC Partner (Simulated)"
DEFAULT_DISCLAIMER = (
    "This pre-approved credit offer is a simulated mock calculation for demonstration "
    "purposes and does not represent a legally binding credit agreement."
)

DEFAULT_OFFER_RULES: Dict[str, Dict[str, Any]] = {
    "Not Yet Eligible": {
        "eligible_amount": 0,
        "interest_rate": 0.0,
        "term_months": 0,
        "is_eligible": False,
    },
    "Bronze": {
        "eligible_amount": 5000,
        "interest_rate": 18.0,
        "term_months": 12,
        "is_eligible": True,
    },
    "Silver": {
        "eligible_amount": 15000,
        "interest_rate": 14.0,
        "term_months": 24,
        "is_eligible": True,
    },
    "Gold": {
        "eligible_amount": 30000,
        "interest_rate": 11.0,
        "term_months": 36,
        "is_eligible": True,
    },
}


def load_offer_rules() -> Dict[str, Any]:
    """Load credit offer rules from the contracts directory if present."""
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[3]
    rules_path = repo_root / "contracts" / "credit" / "offer_rules.json"

    if rules_path.exists():
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "partner_nbfc_name": DEFAULT_NBFC_NAME,
        "disclaimer": DEFAULT_DISCLAIMER,
        "tier_offers": DEFAULT_OFFER_RULES,
    }
