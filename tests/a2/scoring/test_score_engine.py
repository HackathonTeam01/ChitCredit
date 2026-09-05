"""
Comprehensive unit tests for A2 Chit Credit Score Engine.

Covers:
1. 100% on-time
2. 0% on-time
3. zero streak
4. large streak (capping at 10)
5. zero tenure
6. large tenure (capping at 10)
7. missed payments (penalty deduction)
8. score below zero before clamp (verifying clamp min=0)
9. score above 100 before clamp (verifying clamp max=100)
10. boundary around 49 (Not Yet Eligible)
11. boundary at 50 (Bronze)
12. boundary around 69 (Bronze)
13. boundary at 70 (Silver)
14. boundary around 84 (Silver)
15. boundary at 85 (Gold)
16. boundary at 100 (Gold)
17. Deterministic regression assertions.
"""

import pytest
from backend.a2.scoring.engine import (
    calculate_score,
    calculate_score_band,
    calculate_score_breakdown,
    clamp,
)
from backend.a2.validation.models import ScoreInput


class TestScoreEngine:
    def test_100_pct_on_time_perfect(self):
        """Test perfect on-time history with maximum streak and tenure."""
        # raw = 0.5*100 + 0.2*100 + 0.2*100 - 0.1*0 = 50 + 20 + 20 = 90
        res = calculate_score(
            on_time_pct=100.0,
            streak_count=10,
            tenure_cycles=10,
            missed_payment_count=0,
            member_id="M-100",
        )
        assert res.score_value == 90
        assert res.score_band == "Gold"
        assert res.member_id == "M-100"
        assert res.on_time_pct == 100.0

    def test_0_pct_on_time_zero_history(self):
        """Test zero on-time history produces minimum valid score."""
        res = calculate_score(
            on_time_pct=0.0,
            streak_count=0,
            tenure_cycles=0,
            missed_payment_count=0,
            member_id="M-0",
        )
        assert res.score_value == 0
        assert res.score_band == "Not Yet Eligible"

    def test_zero_streak(self):
        """Test streak=0 gives 0 streak component."""
        res = calculate_score(
            on_time_pct=80.0,
            streak_count=0,
            tenure_cycles=5,
            missed_payment_count=0,
        )
        # raw = 0.5*80 + 0.2*0 + 0.2*(5/10*100) = 40 + 0 + 10 = 50
        assert res.score_value == 50
        assert res.score_band == "Bronze"

    def test_large_streak_capping(self):
        """Test streak > 10 is capped at 10 (100 component points)."""
        res_10 = calculate_score(on_time_pct=90.0, streak_count=10, tenure_cycles=5)
        res_25 = calculate_score(on_time_pct=90.0, streak_count=25, tenure_cycles=5)
        res_100 = calculate_score(on_time_pct=90.0, streak_count=100, tenure_cycles=5)
        assert res_10.score_value == res_25.score_value == res_100.score_value

    def test_zero_tenure(self):
        """Test tenure=0 gives 0 tenure component."""
        res = calculate_score(
            on_time_pct=90.0,
            streak_count=5,
            tenure_cycles=0,
            missed_payment_count=0,
        )
        # raw = 0.5*90 + 0.2*(50) + 0.2*(0) = 45 + 10 + 0 = 55
        assert res.score_value == 55
        assert res.score_band == "Bronze"

    def test_large_tenure_capping(self):
        """Test tenure > 10 is capped at 10 (100 component points)."""
        res_10 = calculate_score(on_time_pct=80.0, streak_count=4, tenure_cycles=10)
        res_50 = calculate_score(on_time_pct=80.0, streak_count=4, tenure_cycles=50)
        assert res_10.score_value == res_50.score_value

    def test_missed_payments_penalty(self):
        """Test penalty deduction from missed payments."""
        res_clean = calculate_score(on_time_pct=90.0, streak_count=6, tenure_cycles=5, missed_payment_count=0)
        res_missed1 = calculate_score(on_time_pct=90.0, streak_count=6, tenure_cycles=5, missed_payment_count=1)
        res_missed3 = calculate_score(on_time_pct=90.0, streak_count=6, tenure_cycles=5, missed_payment_count=3)
        # 1 missed payment = - 0.1 * 10 = -1 point
        # 3 missed payments = - 0.1 * 30 = -3 points
        assert res_clean.score_value - res_missed1.score_value == 1
        assert res_clean.score_value - res_missed3.score_value == 3

    def test_score_below_zero_clamping(self):
        """Test extreme missed payments clamp score at 0."""
        res = calculate_score(
            on_time_pct=10.0,
            streak_count=0,
            tenure_cycles=0,
            missed_payment_count=20,  # penalty = 20 * 10 = 200 -> raw = 5 - 20 = -15
        )
        assert res.score_value == 0
        assert res.score_band == "Not Yet Eligible"

    def test_clamp_helper(self):
        """Test clamp helper boundaries."""
        assert clamp(-10.5, 0, 100) == 0
        assert clamp(150.0, 0, 100) == 100
        assert clamp(75.5, 0, 100) == 75.5

    def test_boundary_at_49_not_yet_eligible(self):
        """Test score of 49 falls in Not Yet Eligible."""
        # To get 49: on_time=78, streak=5, tenure=0, missed=0 -> 0.5*78 + 0.2*50 + 0 = 39 + 10 = 49
        res = calculate_score(on_time_pct=78.0, streak_count=5, tenure_cycles=0, missed_payment_count=0)
        assert res.score_value == 49
        assert res.score_band == "Not Yet Eligible"
        assert calculate_score_band(49) == "Not Yet Eligible"

    def test_boundary_at_50_bronze(self):
        """Test score of 50 is the exact threshold for Bronze."""
        # on_time=80, streak=5, tenure=0 -> 0.5*80 + 0.2*50 = 40 + 10 = 50
        res = calculate_score(on_time_pct=80.0, streak_count=5, tenure_cycles=0, missed_payment_count=0)
        assert res.score_value == 50
        assert res.score_band == "Bronze"
        assert calculate_score_band(50) == "Bronze"

    def test_boundary_at_69_bronze(self):
        """Test score of 69 is within Bronze."""
        # on_time=98, streak=5, tenure=5 -> 0.5*98 + 0.2*50 + 0.2*50 = 49 + 10 + 10 = 69
        res = calculate_score(on_time_pct=98.0, streak_count=5, tenure_cycles=5, missed_payment_count=0)
        assert res.score_value == 69
        assert res.score_band == "Bronze"
        assert calculate_score_band(69) == "Bronze"

    def test_boundary_at_70_silver(self):
        """Test score of 70 transitions to Silver."""
        # on_time=100, streak=5, tenure=5 -> 0.5*100 + 0.2*50 + 0.2*50 = 50 + 10 + 10 = 70
        res = calculate_score(on_time_pct=100.0, streak_count=5, tenure_cycles=5, missed_payment_count=0)
        assert res.score_value == 70
        assert res.score_band == "Silver"
        assert calculate_score_band(70) == "Silver"

    def test_boundary_at_84_silver(self):
        """Test score of 84 is upper bound of Silver."""
        # on_time=98, streak=9, tenure=8.5 -> 0.5*98 (49) + 0.2*90 (18) + 0.2*85 (17) = 84
        # with integer inputs: on_time=96, streak=9, tenure=9, missed=1 -> 48 + 18 + 18 - 1 = 83 (close)
        # directly test band function:
        assert calculate_score_band(84) == "Silver"

    def test_boundary_at_85_gold(self):
        """Test score of 85 is the exact threshold for Gold."""
        # on_time=90, streak=10, tenure=10 -> 0.5*90 (45) + 0.2*100 (20) + 0.2*100 (20) = 85
        res = calculate_score(on_time_pct=90.0, streak_count=10, tenure_cycles=10, missed_payment_count=0)
        assert res.score_value == 85
        assert res.score_band == "Gold"
        assert calculate_score_band(85) == "Gold"

    def test_boundary_at_100_gold(self):
        """Test score of 100 falls in Gold tier."""
        assert calculate_score_band(100) == "Gold"

    def test_deterministic_regression_cases(self):
        """Fixed test vectors ensuring stability across refactors."""
        vectors = [
            # (on_time, streak, tenure, missed, expected_score, expected_tier)
            (95.0, 8, 6, 0, 76, "Silver"),
            (75.0, 4, 3, 2, 50, "Bronze"),
            (60.0, 2, 2, 3, 35, "Not Yet Eligible"),
            (85.0, 6, 4, 1, 62, "Bronze"),
            (96.0, 9, 7, 0, 80, "Silver"),
            (98.0, 10, 8, 0, 85, "Gold"),
        ]
        for on_time, streak, tenure, missed, exp_score, exp_tier in vectors:
            res = calculate_score(
                on_time_pct=on_time,
                streak_count=streak,
                tenure_cycles=tenure,
                missed_payment_count=missed,
            )
            assert res.score_value == exp_score, f"Failed score for {on_time}, {streak}, {tenure}, {missed}"
            assert res.score_band == exp_tier, f"Failed tier for {on_time}, {streak}, {tenure}, {missed}"

    def test_input_validation(self):
        """Test bad inputs raise ValueError."""
        with pytest.raises(ValueError):
            calculate_score(on_time_pct=-5.0, streak_count=1, tenure_cycles=1)
        with pytest.raises(ValueError):
            calculate_score(on_time_pct=105.0, streak_count=1, tenure_cycles=1)
        with pytest.raises(ValueError):
            calculate_score(on_time_pct=50.0, streak_count=-1, tenure_cycles=1)
        with pytest.raises(ValueError):
            calculate_score(on_time_pct=50.0, streak_count=1, tenure_cycles=-1)
        with pytest.raises(ValueError):
            calculate_score(on_time_pct=50.0, streak_count=1, tenure_cycles=1, missed_payment_count=-1)
