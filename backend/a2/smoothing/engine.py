"""Income smoothing and auto-payment simulation for Chit Credit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class SmoothingDay:
    date: str
    daily_earning: float
    trailing_average: float
    reserve_pct: float
    reserve_amount: float
    wallet_balance: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SmoothingResult:
    amount_due: float
    trailing_window: int
    base_pct: float
    days: list[SmoothingDay]
    target_reached_date: Optional[str]
    auto_payment: Optional[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount_due": self.amount_due,
            "trailing_window": self.trailing_window,
            "base_pct": self.base_pct,
            "days": [day.to_dict() for day in self.days],
            "target_reached_date": self.target_reached_date,
            "auto_payment": self.auto_payment,
        }


def _normalise_dates(values: Iterable[Any]) -> list[str]:
    dates = []
    for value in values:
        if isinstance(value, date):
            dates.append(value.isoformat())
        else:
            dates.append(str(value))
    return dates


def calculate_smoothing_reserve(
    daily_earnings: Iterable[float],
    amount_due: float,
    dates: Optional[Iterable[Any]] = None,
    trailing_window: int = 7,
    base_pct: float = 0.15,
) -> SmoothingResult:
    """Build a variable reserve that reaches a fixed contribution target.

    Earnings above the trailing average reserve 1.25x the base percentage;
    earnings below it reserve 0.75x. The first day uses its own earning as
    the average, avoiding a misleading boost before a window exists.
    """
    earnings = [float(value) for value in daily_earnings]
    if amount_due <= 0:
        raise ValueError("amount_due must be greater than 0")
    if trailing_window < 1:
        raise ValueError("trailing_window must be at least 1")
    if not 0 < base_pct < 1:
        raise ValueError("base_pct must be between 0 and 1")
    if any(value < 0 for value in earnings):
        raise ValueError("daily earnings cannot be negative")

    day_dates = _normalise_dates(dates or range(1, len(earnings) + 1))
    if len(day_dates) != len(earnings):
        raise ValueError("dates must have the same length as daily_earnings")

    wallet = 0.0
    reached_date: Optional[str] = None
    days: list[SmoothingDay] = []
    for index, earning in enumerate(earnings):
        window = earnings[max(0, index - trailing_window + 1): index + 1]
        average = sum(window) / len(window)
        reserve_pct = base_pct if index == 0 else (base_pct * 1.25 if earning > average else base_pct * 0.75)
        reserve_amount = earning * reserve_pct
        wallet = min(amount_due, wallet + reserve_amount)
        if reached_date is None and wallet >= amount_due:
            reached_date = day_dates[index]
        days.append(SmoothingDay(
            date=day_dates[index],
            daily_earning=round(earning, 2),
            trailing_average=round(average, 2),
            reserve_pct=round(reserve_pct, 4),
            reserve_amount=round(reserve_amount, 2),
            wallet_balance=round(wallet, 2),
        ))

    auto_payment = None
    if reached_date is not None:
        auto_payment = {
            "status": "ready",
            "date": reached_date,
            "amount": round(amount_due, 2),
            "source": "savings_wallet",
        }
    return SmoothingResult(amount_due, trailing_window, base_pct, days, reached_date, auto_payment)


def calculate_forecast(daily_earnings: Iterable[float], window: int = 7) -> dict[str, Any]:
    """Flag a slow period when moving averages decline for three windows."""
    values = [float(value) for value in daily_earnings]
    if window < 1:
        raise ValueError("window must be at least 1")
    if any(value < 0 for value in values):
        raise ValueError("daily earnings cannot be negative")
    averages = [round(sum(values[index - window + 1:index + 1]) / window, 2)
                for index in range(window - 1, len(values))]
    declines = sum(current < previous for previous, current in zip(averages, averages[1:]))
    return {
        "window": window,
        "moving_averages": averages,
        "slow_period_predicted": declines >= 3,
        "declining_windows": declines,
    }
