"""
Data provider interface and standalone mock implementation for A2.

This abstraction enables A2 scoring and offer services to run completely
independently in development and testing, while preparing a clean, read-only
handshake for A1's real database / ledger implementation later.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.a2.validation.models import ScoreInput


class DataProvider(ABC):
    """Abstract interface defining required data inputs for scoring and offers."""

    @abstractmethod
    def get_member(self, member_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve core member demographic/membership record."""
        pass

    @abstractmethod
    def get_member_contributions(self, member_id: str) -> List[Dict[str, Any]]:
        """Retrieve contribution history list for member."""
        pass

    @abstractmethod
    def get_member_score_inputs(self, member_id: str) -> ScoreInput:
        """Derive or fetch the metrics needed for Chit Credit Score calculation."""
        pass


class MockDataProvider(DataProvider):
    """
    In-memory mock data provider containing 18 member profiles covering
    Gold, Silver, Bronze, and Not Yet Eligible personas.
    """

    def __init__(self, custom_members: Optional[Dict[str, Dict[str, Any]]] = None):
        self._members: Dict[str, Dict[str, Any]] = custom_members or self._default_mock_members()

    def get_member(self, member_id: str) -> Optional[Dict[str, Any]]:
        return self._members.get(member_id)

    def get_member_contributions(self, member_id: str) -> List[Dict[str, Any]]:
        member = self._members.get(member_id)
        if not member:
            return []
        return member.get("contributions", [])

    def get_member_score_inputs(self, member_id: str) -> ScoreInput:
        member = self._members.get(member_id)
        if not member:
            raise KeyError(f"Member with ID '{member_id}' not found in DataProvider.")

        return ScoreInput(
            member_id=member_id,
            on_time_pct=float(member.get("on_time_pct", 0.0)),
            streak_count=int(member.get("streak_count", 0)),
            tenure_cycles=int(member.get("tenure_cycles", 0)),
            missed_payment_count=int(member.get("missed_payment_count", 0)),
        )

    def list_all_member_ids(self) -> List[str]:
        return list(self._members.keys())

    @staticmethod
    def _default_mock_members() -> Dict[str, Dict[str, Any]]:
        # 18 representative circle members plus test-suite personas (1, CHT-001, CHT-EMPTY)
        seed_data = [
            ("1", "Arun Kumar", 98.0, 10, 8, 0, "Gold"),
            ("CHT-001", "Arun Kumar", 98.0, 10, 8, 0, "Gold"),
            ("CHT-009", "Arun Kumar", 98.0, 10, 8, 0, "Gold"),
            ("CHT-010", "Meena S.", 95.0, 8, 6, 0, "Silver"),
            ("CHT-011", "Ravi Prakash", 75.0, 4, 3, 2, "Silver"),
            ("CHT-012", "Kavitha R.", 60.0, 2, 2, 3, "Bronze"),
            ("CHT-013", "Suresh Babu", 85.0, 6, 4, 1, "Silver"),
            ("CHT-014", "Priya D.", 96.0, 9, 7, 0, "Gold"),
            ("CHT-015", "Muthu K.", 80.0, 5, 3, 0, "Silver"),
            ("CHT-016", "Lakshmi R.", 90.0, 7, 5, 0, "Silver"),
            ("CHT-017", "Selvam P.", 65.0, 3, 2, 2, "Bronze"),
            ("CHT-018", "Geetha M.", 92.0, 8, 6, 0, "Silver"),
            ("CHT-019", "Manoj V.", 82.0, 5, 4, 0, "Silver"),
            ("CHT-020", "Anitha S.", 78.0, 4, 3, 1, "Silver"),
            ("CHT-021", "Dinesh K.", 94.0, 9, 7, 0, "Gold"),
            ("CHT-022", "Revathi P.", 62.0, 2, 2, 2, "Bronze"),
            ("CHT-023", "Bala M.", 88.0, 7, 5, 0, "Silver"),
            ("CHT-024", "Asha R.", 80.0, 5, 3, 0, "Silver"),
            ("CHT-025", "Karthik S.", 97.0, 10, 8, 0, "Gold"),
            ("CHT-026", "Nandhini V.", 83.0, 6, 4, 0, "Silver"),
            ("CHT-INELIGIBLE", "Ineligible Member", 20.0, 0, 0, 5, "Not Yet Eligible"),
            ("CHT-EMPTY", "New Member", 0.0, 0, 0, 0, "Not Yet Eligible"),
        ]

        members = {}
        for mid, name, on_time, streak, tenure, missed, _ in seed_data:
            contributions = []
            if mid != "CHT-EMPTY":
                contributions = [
                    {"date": "2024-08-24", "amount": 500, "on_time": True, "mode": "IppoPay UPI"},
                    {"date": "2024-07-24", "amount": 500, "on_time": True, "mode": "Wallet reserve"},
                ]
            members[mid] = {
                "id": mid,
                "name": name,
                "on_time_pct": on_time,
                "streak_count": streak,
                "tenure_cycles": tenure,
                "missed_payment_count": missed,
                "contributions": contributions,
            }
        return members


def get_default_data_provider() -> DataProvider:
    """
    Factory function returning the configured DataProvider.

    Configuration:
      - A2_DATA_PROVIDER: "mock" (default) or "http" (explicit live integration mode).
      - If A2_DATA_PROVIDER is unset or "mock": returns MockDataProvider().
      - If A2_DATA_PROVIDER is "http": returns HttpDataProvider using A1_API_BASE_URL.
        Raises ValueError if A1_API_BASE_URL is missing or empty.
      - If A2_DATA_PROVIDER is set to an unrecognized value: raises ValueError.
    """
    import os
    provider_mode = os.environ.get("A2_DATA_PROVIDER", "mock").strip().lower()

    if not provider_mode or provider_mode == "mock":
        return MockDataProvider()
    elif provider_mode == "http":
        base_url = os.environ.get("A1_API_BASE_URL", "").strip()
        if not base_url:
            raise ValueError(
                "A2_DATA_PROVIDER is configured as 'http', but A1_API_BASE_URL is missing or empty. "
                "Please set A1_API_BASE_URL (e.g. 'http://10.28.73.240:5000')."
            )
        from backend.a2.integration.http_data_provider import HttpDataProvider
        return HttpDataProvider(base_url=base_url)
    else:
        raise ValueError(
            f"Invalid A2_DATA_PROVIDER '{provider_mode}'. Expected 'mock' or 'http'."
        )
