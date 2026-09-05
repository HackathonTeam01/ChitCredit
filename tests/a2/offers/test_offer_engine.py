"""
Comprehensive unit tests for A2 Credit Offer Engine.

Covers:
17. Bronze (amount 5000, rate 18)
18. Silver (amount 15000, rate 14)
19. Gold (amount 30000, rate 11)
20. Below Bronze (not eligible)
21. Invalid band (safe fallback)
22. Member ID preserved
23. Correct amount matching contract
24. Correct interest rate matching contract
25. Mock partner NBFC identification
"""

import pytest
from backend.a2.offers.engine import get_credit_offer


class TestCreditOfferEngine:
    def test_bronze_offer_terms(self):
        """Test Bronze tier yields ₹5,000 limit at 18% APR."""
        offer = get_credit_offer(
            score_band="Bronze",
            member_id="CHT-012",
            unlock_date="2024-08-25",
        )
        assert offer.member_id == "CHT-012"
        assert offer.eligible_amount == 5000.0
        assert offer.interest_rate == 18.0
        assert offer.term_months == 12
        assert offer.is_eligible is True
        assert offer.score_band == "Bronze"
        assert offer.unlock_date == "2024-08-25"

    def test_silver_offer_terms(self):
        """Test Silver tier yields ₹15,000 limit at 14% APR."""
        offer = get_credit_offer(
            score_band="Silver",
            member_id="CHT-010",
            unlock_date="2024-08-25",
        )
        assert offer.member_id == "CHT-010"
        assert offer.eligible_amount == 15000.0
        assert offer.interest_rate == 14.0
        assert offer.term_months == 24
        assert offer.is_eligible is True
        assert offer.score_band == "Silver"

    def test_gold_offer_terms(self):
        """Test Gold tier yields ₹30,000 limit at 11% APR."""
        offer = get_credit_offer(
            score_band="Gold",
            member_id="CHT-009",
            unlock_date="2024-08-25",
        )
        assert offer.member_id == "CHT-009"
        assert offer.eligible_amount == 30000.0
        assert offer.interest_rate == 11.0
        assert offer.term_months == 36
        assert offer.is_eligible is True
        assert offer.score_band == "Gold"

    def test_below_bronze_not_eligible(self):
        """Test Not Yet Eligible band returns ₹0 and is_eligible=False."""
        offer = get_credit_offer(
            score_band="Not Yet Eligible",
            member_id="CHT-001",
        )
        assert offer.member_id == "CHT-001"
        assert offer.eligible_amount == 0.0
        assert offer.interest_rate == 0.0
        assert offer.is_eligible is False

    def test_invalid_band_fallback(self):
        """Test unknown band string gracefully defaults to not eligible."""
        offer = get_credit_offer(
            score_band="Diamond_Invalid",
            member_id="CHT-999",
        )
        assert offer.member_id == "CHT-999"
        assert offer.eligible_amount == 0.0
        assert offer.is_eligible is False

    def test_member_id_preserved(self):
        """Test member_id is passed through unaltered."""
        for mid in ["USER-001", "TEST_MEM_42", "CHT-789"]:
            offer = get_credit_offer(score_band="Silver", member_id=mid)
            assert offer.member_id == mid

    def test_partner_nbfc_mock_notice(self):
        """Test partner_nbfc and disclaimer clearly indicate simulated demo facility."""
        offer = get_credit_offer(score_band="Gold", member_id="CHT-009")
        assert "Simulated" in offer.partner_nbfc or "Demo" in offer.partner_nbfc
        assert len(offer.disclaimer) > 0

    def test_empty_member_id_rejected(self):
        """Test empty member_id raises ValueError."""
        with pytest.raises(ValueError):
            get_credit_offer(score_band="Bronze", member_id="")
        with pytest.raises(ValueError):
            get_credit_offer(score_band="Bronze", member_id="   ")
