"""Elastic repayment simulation for Chit Credit offers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class RepaymentDay:
    day: int
    daily_earning: float
    deduction_pct: float
    deduction_amount: float
    remaining_balance: float
    slow_period_predicted: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def calculate_elastic_repayment(
    daily_earnings: Iterable[float],
    loan_balance: float,
    deduction_pct: float = 0.10,
    moving_average_window: int = 7,
) -> dict[str, Any]:
    """Deduct a percentage of earnings, halving it during a slow trend."""
    earnings = [float(value) for value in daily_earnings]
    if loan_balance < 0:
        raise ValueError("loan_balance cannot be negative")
    if not 0 < deduction_pct <= 1:
        raise ValueError("deduction_pct must be between 0 and 1")
    if moving_average_window < 1:
        raise ValueError("moving_average_window must be at least 1")
    if any(value < 0 for value in earnings):
        raise ValueError("daily earnings cannot be negative")

    remaining = float(loan_balance)
    schedule: list[RepaymentDay] = []
    for index, earning in enumerate(earnings):
        previous = earnings[max(0, index - moving_average_window):index]
        slow_period = len(previous) >= moving_average_window and earning < sum(previous) / len(previous)
        effective_pct = deduction_pct / 2 if slow_period else deduction_pct
        deduction = min(earning * effective_pct, remaining)
        remaining = max(0.0, remaining - deduction)
        schedule.append(RepaymentDay(
            day=index + 1,
            daily_earning=round(earning, 2),
            deduction_pct=round(effective_pct, 4),
            deduction_amount=round(deduction, 2),
            remaining_balance=round(remaining, 2),
            slow_period_predicted=slow_period,
        ))

    return {
        "loan_balance": round(float(loan_balance), 2),
        "deduction_pct": deduction_pct,
        "remaining_balance": round(remaining, 2),
        "paid_off": remaining == 0,
        "schedule": [day.to_dict() for day in schedule],
    }


def calculate_today_repayment(
    daily_earning: float,
    loan_balance: float,
    deduction_pct: float = 0.10,
) -> dict[str, Any]:
    """Return the single-day value used by the interactive repayment demo."""
    result = calculate_elastic_repayment([daily_earning], loan_balance, deduction_pct)
    return result["schedule"][0]
