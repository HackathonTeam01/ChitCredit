"""
Pure, framework-independent Chit Credit Score Engine.

Calculates the deterministic, explainable Chit Credit Score from:
- on_time_pct: On-time payment percentage (0-100)
- streak_count: Current consecutive on-time contribution streak
- tenure_cycles: Number of completed chit cycles / milestones
- missed_payment_count: Total count of missed or defaulted payments

Formula:
  Score = (w1 * On-Time %) + (w2 * Streak Length capped) + (w3 * Tenure capped) - (w4 * Missed Penalty)
  where:
    w1 = 0.5, w2 = 0.2, w3 = 0.2, w4 = 0.1
    Streak and Tenure normalized to 0-100 scale (capped at 10 cycles)
    Missed penalty = missed_payment_count * 10
    Final score is clamped between 0 and 100.
"""

from __future__ import annotations
from typing import Optional

from backend.a2.scoring.rules import load_score_rules, get_tier_for_score
from backend.a2.validation.models import ScoreBreakdown, ScoreInput, ScoreResult


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a numerical value between min_val and max_val."""
    return max(min_val, min(value, max_val))


def calculate_score_band(score_value: int) -> str:
    """Deterministically determine the credit tier band from a score value."""
    rules = load_score_rules()
    tier_bands = rules.get("tier_bands")
    return get_tier_for_score(score_value, tier_bands)


def calculate_score_breakdown(
    on_time_pct: float,
    streak_count: int,
    tenure_cycles: int,
    missed_payment_count: int = 0,
) -> ScoreBreakdown:
    """
    Compute full mathematical component breakdown for explainability.
    """
    rules = load_score_rules()
    weights = rules.get("weights", {})
    w1 = weights.get("w1_on_time_pct", 0.5)
    w2 = weights.get("w2_streak_count", 0.2)
    w3 = weights.get("w3_tenure_cycles", 0.2)
    w4 = weights.get("w4_missed_penalty", 0.1)

    # Normalization convention
    on_time_component = float(on_time_pct)
    streak_component = (min(streak_count, 10) / 10.0) * 100.0
    tenure_component = (min(tenure_cycles, 10) / 10.0) * 100.0
    missed_payment_penalty = float(missed_payment_count) * 10.0

    raw_score = (
        (w1 * on_time_component)
        + (w2 * streak_component)
        + (w3 * tenure_component)
        - (w4 * missed_payment_penalty)
    )

    clamped_score = int(round(clamp(raw_score, 0.0, 100.0)))

    return ScoreBreakdown(
        on_time_component=round(on_time_component, 2),
        streak_component=round(streak_component, 2),
        tenure_component=round(tenure_component, 2),
        missed_payment_penalty=round(missed_payment_penalty, 2),
        raw_score=round(raw_score, 4),
        clamped_score=clamped_score,
        weights={
            "w1_on_time": w1,
            "w2_streak": w2,
            "w3_tenure": w3,
            "w4_missed_penalty": w4,
        },
        normalization_convention=(
            "Streak & tenure capped at 10 cycles mapped to 0-100; "
            "missed penalty at 10 pts per missed payment; clamped to [0, 100]"
        ),
    )


def calculate_score(
    on_time_pct: float,
    streak_count: int,
    tenure_cycles: int,
    missed_payment_count: int = 0,
    member_id: Optional[str] = None,
    include_breakdown: bool = True,
) -> ScoreResult:
    """
    Primary pure scoring function.
    Accepts validated metrics and produces the canonical ScoreResult.
    """
    # Defensive validation
    inp = ScoreInput(
        member_id=member_id or "anonymous",
        on_time_pct=float(on_time_pct),
        streak_count=int(streak_count),
        tenure_cycles=int(tenure_cycles),
        missed_payment_count=int(missed_payment_count),
    )
    inp.validate()

    breakdown = calculate_score_breakdown(
        on_time_pct=inp.on_time_pct,
        streak_count=inp.streak_count,
        tenure_cycles=inp.tenure_cycles,
        missed_payment_count=inp.missed_payment_count,
    )

    score_value = breakdown.clamped_score
    score_band = calculate_score_band(score_value)

    return ScoreResult(
        member_id=inp.member_id,
        on_time_pct=inp.on_time_pct,
        streak_count=inp.streak_count,
        tenure_cycles=inp.tenure_cycles,
        score_value=score_value,
        score_band=score_band,
        breakdown=breakdown if include_breakdown else None,
    )
