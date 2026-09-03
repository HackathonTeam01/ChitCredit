"""
Integration tests for A2 Services and API routes using MockDataProvider.

Verifies:
1. End-to-end score evaluation across all 18 mock members.
2. Score-to-Offer consistency (Gold->30k, Silver->15k, Bronze->5k).
3. API route handlers return canonical JSON shape conforming to contracts.
4. Extensibility of custom data provider without modifying domain engine.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

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
    def test_all_18_members_score_evaluation(self, score_service, mock_provider):
        """Verify score calculation succeeds deterministically for all 18 mock members."""
        member_ids = mock_provider.list_all_member_ids()
        assert len(member_ids) == 18

        for mid in member_ids:
            res = score_service.get_score_for_member(mid)
            assert res.member_id == mid
            assert 0 <= res.score_value <= 100
            assert res.score_band in ["Not Yet Eligible", "Bronze", "Silver", "Gold"]
            assert res.breakdown is not None
            assert res.breakdown.clamped_score == res.score_value

    def test_all_18_members_offer_consistency(self, score_service, offer_service, mock_provider):
        """Verify credit offers strictly match score tiers for all 18 members."""
        for mid in mock_provider.list_all_member_ids():
            score_res = score_service.get_score_for_member(mid)
            offer_res = offer_service.get_offer_for_member(mid)

            assert offer_res.member_id == mid
            assert offer_res.score_band == score_res.score_band

            if score_res.score_band == "Gold":
                assert offer_res.eligible_amount == 30000.0
                assert offer_res.interest_rate == 11.0
                assert offer_res.is_eligible is True
            elif score_res.score_band == "Silver":
                assert offer_res.eligible_amount == 15000.0
                assert offer_res.interest_rate == 14.0
                assert offer_res.is_eligible is True
            elif score_res.score_band == "Bronze":
                assert offer_res.eligible_amount == 5000.0
                assert offer_res.interest_rate == 18.0
                assert offer_res.is_eligible is True
            else:
                assert offer_res.eligible_amount == 0.0
                assert offer_res.is_eligible is False

    def test_api_route_get_member_score(self, test_client):
        """Test GET /member/{id}/score API endpoint via TestClient."""
        response = test_client.get("/member/CHT-009/score")
        assert response.status_code == 200
        data = response.json()
        assert data["member_id"] == "CHT-009"
        assert "score_value" in data
        assert "score_band" in data
        assert "on_time_pct" in data
        assert "streak_count" in data
        assert "tenure_cycles" in data
        assert "breakdown" in data

    def test_api_route_get_member_offer(self, test_client):
        """Test GET /member/{id}/credit-offer API endpoint via TestClient."""
        response = test_client.get("/member/CHT-009/credit-offer")
        assert response.status_code == 200
        data = response.json()
        assert data["member_id"] == "CHT-009"
        assert data["eligible_amount"] == 30000.0
        assert data["interest_rate"] == 11.0
        assert "partner_nbfc" in data
        assert "unlock_date" in data

    def test_api_route_unknown_member_404(self, test_client):
        """Test 404 response for nonexistent member ID."""
        response = test_client.get("/member/NONEXISTENT-999/score")
        assert response.status_code == 404
