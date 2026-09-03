"""
Integration tests for A2 Services and API routes using MockDataProvider.

Verifies:
1. GET /member/1/score
2. GET /member/1/credit-offer
3. Unknown member 404 handling
4. Invalid member ID 400 handling
5. Empty contribution history handling
6. Bronze tier score and offer verification
7. Silver tier score and offer verification
8. Gold tier score and offer verification
9. Below Bronze (Not Yet Eligible) score and offer verification
10. Canonical response schema conformity
11. Score -> Tier -> Credit Offer consistency proof
12. End-to-end evaluation across all 18 circle members
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.a2.api.routes import router as a2_router
from backend.a2.integration.data_provider import MockDataProvider
from backend.a2.offers.service import OfferService
from backend.a2.scoring.service import ScoreService


@pytest.fixture
def mock_provider():
    return MockDataProvider()


@pytest.fixture
def score_service(mock_provider):
    return ScoreService(data_provider=mock_provider)


@pytest.fixture
def offer_service(score_service, mock_provider):
    return OfferService(score_service=score_service, data_provider=mock_provider)


@pytest.fixture
def test_client():
    app = FastAPI()
    app.include_router(a2_router)
    return TestClient(app)


class TestA2Integration:
    def test_get_member_1_score(self, test_client):
        """Test GET /member/1/score returns canonical Gold score response."""
        response = test_client.get("/member/1/score")
        assert response.status_code == 200
        data = response.json()
        assert data["member_id"] == "1"
        assert data["score_value"] >= 85
        assert data["score_band"] == "Gold"
        assert data["on_time_pct"] == 98.0
        assert data["streak_count"] == 10
        assert data["tenure_cycles"] == 8
        assert "breakdown" in data
        assert data["breakdown"]["clamped_score"] == data["score_value"]

    def test_get_member_1_credit_offer(self, test_client):
        """Test GET /member/1/credit-offer returns canonical Gold offer response."""
        response = test_client.get("/member/1/credit-offer")
        assert response.status_code == 200
        data = response.json()
        assert data["member_id"] == "1"
        assert data["eligible_amount"] == 30000.0
        assert data["interest_rate"] == 11.0
        assert data["is_eligible"] is True
        assert data["score_band"] == "Gold"
        assert data["term_months"] == 36
        assert "partner_nbfc" in data
        assert "unlock_date" in data
        assert "disclaimer" in data

    def test_unknown_member_returns_404(self, test_client):
        """Test 404 response for nonexistent member on both score and offer routes."""
        score_resp = test_client.get("/member/NONEXISTENT-999/score")
        assert score_resp.status_code == 404

        offer_resp = test_client.get("/member/NONEXISTENT-999/credit-offer")
        assert offer_resp.status_code == 404

    def test_invalid_member_id_returns_400(self, test_client):
        """Test 400 Bad Request for empty or whitespace-only member ID."""
        score_resp = test_client.get("/member/%20%20/score")
        assert score_resp.status_code == 400

        offer_resp = test_client.get("/member/%20%20/credit-offer")
        assert offer_resp.status_code == 400

    def test_empty_contribution_history_handled_gracefully(self, test_client):
        """Test member with empty history returns valid zero score and zero offer without crashing."""
        score_resp = test_client.get("/member/CHT-EMPTY/score")
        assert score_resp.status_code == 200
        score_data = score_resp.json()
        assert score_data["member_id"] == "CHT-EMPTY"
        assert score_data["score_value"] == 0
        assert score_data["score_band"] == "Not Yet Eligible"

        offer_resp = test_client.get("/member/CHT-EMPTY/credit-offer")
        assert offer_resp.status_code == 200
        offer_data = offer_resp.json()
        assert offer_data["eligible_amount"] == 0.0
        assert offer_data["interest_rate"] == 0.0
        assert offer_data["is_eligible"] is False

    def test_bronze_tier_score_and_offer(self, test_client):
        """Test Bronze member yields ₹5,000 at 18% APR."""
        score_resp = test_client.get("/member/CHT-013/score")
        assert score_resp.status_code == 200
        assert score_resp.json()["score_band"] == "Bronze"

        offer_resp = test_client.get("/member/CHT-013/credit-offer")
        assert offer_resp.status_code == 200
        offer_data = offer_resp.json()
        assert offer_data["eligible_amount"] == 5000.0
        assert offer_data["interest_rate"] == 18.0
        assert offer_data["is_eligible"] is True
        assert offer_data["term_months"] == 12

    def test_silver_tier_score_and_offer(self, test_client):
        """Test Silver member yields ₹15,000 at 14% APR."""
        score_resp = test_client.get("/member/CHT-010/score")
        assert score_resp.status_code == 200
        assert score_resp.json()["score_band"] == "Silver"

        offer_resp = test_client.get("/member/CHT-010/credit-offer")
        assert offer_resp.status_code == 200
        offer_data = offer_resp.json()
        assert offer_data["eligible_amount"] == 15000.0
        assert offer_data["interest_rate"] == 14.0
        assert offer_data["is_eligible"] is True
        assert offer_data["term_months"] == 24

    def test_gold_tier_score_and_offer(self, test_client):
        """Test Gold member yields ₹30,000 at 11% APR."""
        score_resp = test_client.get("/member/CHT-009/score")
        assert score_resp.status_code == 200
        assert score_resp.json()["score_band"] == "Gold"

        offer_resp = test_client.get("/member/CHT-009/credit-offer")
        assert offer_resp.status_code == 200
        offer_data = offer_resp.json()
        assert offer_data["eligible_amount"] == 30000.0
        assert offer_data["interest_rate"] == 11.0
        assert offer_data["is_eligible"] is True
        assert offer_data["term_months"] == 36

    def test_below_bronze_ineligible_score_and_offer(self, test_client):
        """Test Below Bronze member yields ₹0 at 0% APR and is_eligible=False."""
        score_resp = test_client.get("/member/CHT-INELIGIBLE/score")
        assert score_resp.status_code == 200
        assert score_resp.json()["score_band"] == "Not Yet Eligible"

        offer_resp = test_client.get("/member/CHT-INELIGIBLE/credit-offer")
        assert offer_resp.status_code == 200
        offer_data = offer_resp.json()
        assert offer_data["eligible_amount"] == 0.0
        assert offer_data["interest_rate"] == 0.0
        assert offer_data["is_eligible"] is False

    def test_response_schema_canonical_conformity(self, test_client):
        """Verify API response structures strictly conform to credit contract JSON schemas."""
        score_data = test_client.get("/member/1/score").json()
        required_score_fields = [
            "member_id", "on_time_pct", "streak_count",
            "tenure_cycles", "score_value", "score_band"
        ]
        for f in required_score_fields:
            assert f in score_data, f"Missing required score field: {f}"

        assert isinstance(score_data["member_id"], str)
        assert isinstance(score_data["on_time_pct"], (int, float))
        assert isinstance(score_data["streak_count"], int)
        assert isinstance(score_data["tenure_cycles"], int)
        assert isinstance(score_data["score_value"], int)
        assert score_data["score_band"] in ["Not Yet Eligible", "Bronze", "Silver", "Gold"]

        offer_data = test_client.get("/member/1/credit-offer").json()
        required_offer_fields = [
            "member_id", "eligible_amount", "interest_rate",
            "unlock_date", "partner_nbfc"
        ]
        for f in required_offer_fields:
            assert f in offer_data, f"Missing required offer field: {f}"

        assert isinstance(offer_data["member_id"], str)
        assert isinstance(offer_data["eligible_amount"], (int, float))
        assert isinstance(offer_data["interest_rate"], (int, float))
        assert isinstance(offer_data["unlock_date"], str)
        assert isinstance(offer_data["partner_nbfc"], str)

    def test_score_to_tier_to_offer_consistency_proof(self, test_client):
        """
        Proof of consistency:
        score calculation -> score_band -> offer engine -> correct credit terms.
        """
        members_to_check = ["1", "CHT-009", "CHT-010", "CHT-011", "CHT-012", "CHT-INELIGIBLE"]
        for mid in members_to_check:
            score_json = test_client.get(f"/member/{mid}/score").json()
            offer_json = test_client.get(f"/member/{mid}/credit-offer").json()

            band = score_json["score_band"]
            assert offer_json["score_band"] == band

            if band == "Gold":
                assert offer_json["eligible_amount"] == 30000.0
                assert offer_json["interest_rate"] == 11.0
                assert offer_json["is_eligible"] is True
            elif band == "Silver":
                assert offer_json["eligible_amount"] == 15000.0
                assert offer_json["interest_rate"] == 14.0
                assert offer_json["is_eligible"] is True
            elif band == "Bronze":
                assert offer_json["eligible_amount"] == 5000.0
                assert offer_json["interest_rate"] == 18.0
                assert offer_json["is_eligible"] is True
            else:
                assert offer_json["eligible_amount"] == 0.0
                assert offer_json["is_eligible"] is False

    def test_all_18_circle_members_evaluation(self, score_service, offer_service, mock_provider):
        """Verify end-to-end evaluation for all 18 circle members."""
        circle_ids = [f"CHT-{str(i).padStart(3, '0')}" if hasattr(str(i), 'padStart') else f"CHT-{i:03d}" for i in range(9, 27)]
        for mid in circle_ids:
            score = score_service.get_score_for_member(mid)
            offer = offer_service.get_offer_for_member(mid)
            assert 0 <= score.score_value <= 100
            assert offer.score_band == score.score_band
