import pytest

from backend.a2.repayment.engine import calculate_elastic_repayment
from backend.a2.smoothing.engine import calculate_forecast, calculate_smoothing_reserve


def test_smoothing_returns_target_and_auto_payment_contract():
    result = calculate_smoothing_reserve(
        [1000, 800, 1200],
        amount_due=400,
        dates=["2026-09-01", "2026-09-02", "2026-09-03"],
    )

    assert result.target_reached_date == "2026-09-03"
    assert result.days[-1].wallet_balance == 400
    assert result.auto_payment == {
        "status": "ready",
        "date": "2026-09-03",
        "amount": 400,
        "source": "savings_wallet",
    }


def test_smoothing_keeps_unreached_target_explicit():
    result = calculate_smoothing_reserve([100], amount_due=500)

    assert result.target_reached_date is None
    assert result.auto_payment is None
    assert result.days[0].wallet_balance == 15


def test_repayment_halves_rate_for_slow_day_and_caps_balance():
    result = calculate_elastic_repayment([1000] * 7 + [100], loan_balance=1000)

    assert result["schedule"][7]["deduction_pct"] == 0.05
    assert result["remaining_balance"] >= 0


def test_forecast_flags_three_declining_windows():
    result = calculate_forecast([100, 90, 80, 70, 60, 50, 40, 30], window=3)

    assert result["slow_period_predicted"] is True
    assert result["declining_windows"] >= 3


@pytest.mark.parametrize("kwargs", [
    {"daily_earnings": [-1], "amount_due": 500},
    {"daily_earnings": [100], "amount_due": 0},
])
def test_smoothing_rejects_unsafe_inputs(kwargs):
    with pytest.raises(ValueError):
        calculate_smoothing_reserve(**kwargs)
