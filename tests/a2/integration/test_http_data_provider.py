"""
Isolated unit & integration tests for HttpDataProvider adapter.
Mocks all HTTP responses using httpx.MockTransport so tests run completely
offline without requiring a live A1 server.

Covered:
- Successful member fetch
- Successful history fetch
- 404 member handling
- 404 history handling
- Invalid / nonexistent member ID KeyError
- Network connection failure (ConnectionError)
- Timeout failure (TimeoutError)
- Unexpected non-2xx status code (RuntimeError)
- Score-input metric derivation (sorting, on-time %, streak, tenure, missed count)
- ScoreService using HttpDataProvider
- OfferService using HttpDataProvider
- Member 1 normal eligible case
- Empty history case
- Ineligible case
- Missing A1_API_BASE_URL error
"""

import json
import os
import pytest
import httpx

from backend.a2.integration.http_data_provider import HttpDataProvider
from backend.a2.scoring.service import ScoreService
from backend.a2.offers.service import OfferService


def create_mock_transport(handler):
    return httpx.MockTransport(handler)


class TestHttpDataProvider:
    def test_missing_base_url_raises_value_error(self, monkeypatch):
        monkeypatch.delenv("A1_API_BASE_URL", raising=False)
        provider = HttpDataProvider(base_url="")
        with pytest.raises(ValueError, match="A1_API_BASE_URL is not configured"):
            provider.get_member("1")

    def test_provider_selection_default_is_mock(self, monkeypatch):
        from backend.a2.integration.data_provider import get_default_data_provider, MockDataProvider
        monkeypatch.delenv("A2_DATA_PROVIDER", raising=False)
        monkeypatch.setenv("A1_API_BASE_URL", "http://10.28.73.240:5000")  # presence of URL alone must not override default mock
        provider = get_default_data_provider()
        assert isinstance(provider, MockDataProvider)

    def test_provider_selection_explicit_mock(self, monkeypatch):
        from backend.a2.integration.data_provider import get_default_data_provider, MockDataProvider
        monkeypatch.setenv("A2_DATA_PROVIDER", "mock")
        monkeypatch.setenv("A1_API_BASE_URL", "http://10.28.73.240:5000")
        provider = get_default_data_provider()
        assert isinstance(provider, MockDataProvider)

    def test_provider_selection_explicit_http_with_url(self, monkeypatch):
        from backend.a2.integration.data_provider import get_default_data_provider
        monkeypatch.setenv("A2_DATA_PROVIDER", "http")
        monkeypatch.setenv("A1_API_BASE_URL", "http://mock-a1:5000")
        provider = get_default_data_provider()
        assert isinstance(provider, HttpDataProvider)
        assert provider.base_url == "http://mock-a1:5000"

    def test_provider_selection_explicit_http_missing_url(self, monkeypatch):
        from backend.a2.integration.data_provider import get_default_data_provider
        monkeypatch.setenv("A2_DATA_PROVIDER", "http")
        monkeypatch.delenv("A1_API_BASE_URL", raising=False)
        with pytest.raises(ValueError, match="A2_DATA_PROVIDER is configured as 'http', but A1_API_BASE_URL is missing"):
            get_default_data_provider()

    def test_provider_selection_invalid_mode_raises_value_error(self, monkeypatch):
        from backend.a2.integration.data_provider import get_default_data_provider
        monkeypatch.setenv("A2_DATA_PROVIDER", "unsupported_mode")
        with pytest.raises(ValueError, match="Invalid A2_DATA_PROVIDER"):
            get_default_data_provider()

    def test_successful_member_fetch(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/member/1"
            return httpx.Response(
                status_code=200,
                json={
                    "member": {
                        "member_id": 1,
                        "name": "Arun Kumar",
                        "phone": "+91 9840000000",
                        "language_pref": "ta",
                        "chit_group_id": 1,
                    }
                },
            )

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)
        member = provider.get_member("1")

        assert member is not None
        assert member["member_id"] == 1
        assert member["name"] == "Arun Kumar"
        assert member["phone"] == "+91 9840000000"

    def test_successful_history_fetch(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/member/1/history"
            return httpx.Response(
                status_code=200,
                json={
                    "member_id": 1,
                    "count": 2,
                    "history": [
                        {
                            "id": 1,
                            "member_id": 1,
                            "chit_group_id": 1,
                            "due_date": "2024-07-24",
                            "amount_due": 500,
                            "amount_paid": 500,
                            "paid_on_time": True,
                        },
                        {
                            "id": 2,
                            "member_id": 1,
                            "chit_group_id": 1,
                            "due_date": "2024-08-24",
                            "amount_due": 500,
                            "amount_paid": 500,
                            "paid_on_time": True,
                        },
                    ],
                },
            )

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)
        contributions = provider.get_member_contributions("1")

        assert len(contributions) == 2
        assert contributions[0]["due_date"] == "2024-07-24"
        assert contributions[1]["paid_on_time"] is True

    def test_404_member_returns_none(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=404, json={"error": "Member not found"})

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)
        assert provider.get_member("999") is None

    def test_404_history_returns_empty_list(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=404, json={"error": "History not found"})

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)
        assert provider.get_member_contributions("999") == []

    def test_nonexistent_member_score_inputs_raises_key_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=404, json={"error": "Member not found"})

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)
        with pytest.raises(KeyError, match="Member with ID '999' not found"):
            provider.get_member_score_inputs("999")

    def test_network_connection_failure_raises_connection_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)
        with pytest.raises(ConnectionError, match="Failed to connect to A1 backend"):
            provider.get_member("1")

    def test_timeout_failure_raises_timeout_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Read timed out")

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)
        with pytest.raises(TimeoutError, match="Request to A1 backend timed out"):
            provider.get_member("1")

    def test_unexpected_500_status_raises_runtime_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=500, text="Internal Database Error")

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)
        with pytest.raises(RuntimeError, match="A1 backend returned unexpected status 500"):
            provider.get_member("1")

    def test_score_input_metric_derivation(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/member/1":
                return httpx.Response(status_code=200, json={"member": {"member_id": 1, "name": "Arun"}})
            elif request.url.path == "/member/1/history":
                # Unordered records with a break in streak
                return httpx.Response(
                    status_code=200,
                    json={
                        "member_id": 1,
                        "history": [
                            {"id": 4, "due_date": "2024-08-01", "paid_on_time": True},   # Latest: on-time (streak +1)
                            {"id": 1, "due_date": "2024-05-01", "paid_on_time": True},   # Oldest: on-time
                            {"id": 3, "due_date": "2024-07-01", "paid_on_time": True},   # on-time (streak +1)
                            {"id": 2, "due_date": "2024-06-01", "paid_on_time": False},  # Missed (breaks streak)
                        ],
                    },
                )
            return httpx.Response(status_code=404)

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)
        score_input = provider.get_member_score_inputs("1")

        # Total = 4, On-time = 3 (75%), Missed = 1, Streak (from 08-01 and 07-01) = 2, Tenure = 4
        assert score_input.member_id == "1"
        assert score_input.on_time_pct == 75.0
        assert score_input.streak_count == 2
        assert score_input.tenure_cycles == 4
        assert score_input.missed_payment_count == 1

    def test_empty_history_derivation(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/member/2":
                return httpx.Response(status_code=200, json={"member": {"member_id": 2, "name": "Newbie"}})
            elif request.url.path == "/member/2/history":
                return httpx.Response(status_code=200, json={"member_id": 2, "count": 0, "history": []})
            return httpx.Response(status_code=404)

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)
        score_input = provider.get_member_score_inputs("2")

        assert score_input.on_time_pct == 0.0
        assert score_input.streak_count == 0
        assert score_input.tenure_cycles == 0
        assert score_input.missed_payment_count == 0

    def test_score_and_offer_service_with_http_provider(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/member/1":
                return httpx.Response(status_code=200, json={"member": {"member_id": 1, "name": "Arun Kumar"}})
            elif request.url.path == "/member/1/history":
                # 6 consecutive on-time payments
                history = [
                    {"id": i, "due_date": f"2024-0{i}-01", "paid_on_time": True}
                    for i in range(1, 7)
                ]
                return httpx.Response(status_code=200, json={"member_id": 1, "history": history})
            return httpx.Response(status_code=404)

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)

        score_service = ScoreService(data_provider=provider)
        offer_service = OfferService(score_service=score_service, data_provider=provider)

        score_res = score_service.get_score_for_member("1")
        assert score_res.member_id == "1"
        assert score_res.on_time_pct == 100.0
        assert score_res.streak_count == 6
        assert score_res.tenure_cycles == 6
        assert score_res.breakdown is not None
        assert score_res.breakdown.missed_payment_penalty == 0.0
        # raw = 0.5*100 (50) + 0.2*60 (12) + 0.2*60 (12) = 74 -> Silver
        assert score_res.score_value == 74
        assert score_res.score_band == "Silver"

        offer_res = offer_service.get_offer_for_member("1")
        assert offer_res.member_id == "1"
        assert offer_res.eligible_amount == 15000.0
        assert offer_res.interest_rate == 14.0
        assert offer_res.is_eligible is True
        assert offer_res.score_band == "Silver"
        assert offer_res.term_months == 24

    def test_ineligible_member_with_http_provider(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/member/3":
                return httpx.Response(status_code=200, json={"member": {"member_id": 3, "name": "Defaulter"}})
            elif request.url.path == "/member/3/history":
                # 1 on-time, 4 missed
                history = [
                    {"id": 1, "due_date": "2024-01-01", "paid_on_time": True},
                    {"id": 2, "due_date": "2024-02-01", "paid_on_time": False},
                    {"id": 3, "due_date": "2024-03-01", "paid_on_time": False},
                    {"id": 4, "due_date": "2024-04-01", "paid_on_time": False},
                    {"id": 5, "due_date": "2024-05-01", "paid_on_time": False},
                ]
                return httpx.Response(status_code=200, json={"member_id": 3, "history": history})
            return httpx.Response(status_code=404)

        client = httpx.Client(transport=create_mock_transport(handler))
        provider = HttpDataProvider(base_url="http://mock-a1:5000", client=client)

        score_service = ScoreService(data_provider=provider)
        offer_service = OfferService(score_service=score_service, data_provider=provider)

        score_res = score_service.get_score_for_member("3")
        assert score_res.score_band == "Not Yet Eligible"

        offer_res = offer_service.get_offer_for_member("3")
        assert offer_res.eligible_amount == 0.0
        assert offer_res.interest_rate == 0.0
        assert offer_res.is_eligible is False
