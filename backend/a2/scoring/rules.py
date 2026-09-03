"""
Centralized score rules and configuration loader.
Reads rules directly from contracts/credit/score_rules.json with fallback defaults.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


# Default fallback rules matching the centralized contract
DEFAULT_WEIGHTS = {
    "w1_on_time_pct": 0.5,
    "w2_streak_count": 0.2,
    "w3_tenure_cycles": 0.2,
    "w4_missed_penalty": 0.1,
}

DEFAULT_NORMALIZATION = {
    "on_time_scale": 1.0,
    "streak_cap": 10,
    "streak_scale_multiplier": 10.0,
    "tenure_cap": 10,
    "tenure_scale_multiplier": 10.0,
    "missed_penalty_multiplier": 10.0,
    "score_clamp_min": 0,
    "score_clamp_max": 100,
}

DEFAULT_TIERS: List[Dict[str, Any]] = [
    {"band": "Not Yet Eligible", "min_score": 0, "max_score": 49},
    {"band": "Bronze", "min_score": 50, "max_score": 69},
    {"band": "Silver", "min_score": 70, "max_score": 84},
    {"band": "Gold", "min_score": 85, "max_score": 100},
]


def load_score_rules() -> Dict[str, Any]:
    """Load scoring rules from the contracts directory if present."""
    # Find repository root relative to this file
    current_file = Path(__file__).resolve()
    # Go up: backend/a2/scoring/rules.py -> scoring (parent) -> a2 -> backend -> repo root
    repo_root = current_file.parents[3]
    rules_path = repo_root / "contracts" / "credit" / "score_rules.json"

    if rules_path.exists():
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "weights": DEFAULT_WEIGHTS,
        "normalization_conventions": DEFAULT_NORMALIZATION,
        "tier_bands": DEFAULT_TIERS,
    }


def get_tier_for_score(score: int, tier_bands: List[Dict[str, Any]] = None) -> str:
    """Deterministically map a score value (0-100) to its tier band."""
    if tier_bands is None:
        tier_bands = DEFAULT_TIERS

    for tier in tier_bands:
        if tier["min_score"] <= score <= tier["max_score"]:
            return tier["band"]

    if score >= 85:
        return "Gold"
    elif score >= 70:
        return "Silver"
    elif score >= 50:
        return "Bronze"
    return "Not Yet Eligible"
