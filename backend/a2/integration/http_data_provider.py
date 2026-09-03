"""
HTTP DataProvider adapter for Person A1 Data & Ledger integration.

Consumes Person A1's REST endpoints over HTTP:
  - GET {A1_API_BASE_URL}/member/{member_id}
  - GET {A1_API_BASE_URL}/member/{member_id}/history

Derives the canonical ScoreInput metrics deterministically without importing
any private A1 code or database models.
"""

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
import httpx

from backend.a2.integration.data_provider import DataProvider
from backend.a2.validation.models import ScoreInput


class HttpDataProvider(DataProvider):
    """
    HTTP-based DataProvider communicating with Person A1's live ledger service.
    Configured dynamically via A1_API_BASE_URL.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 5.0,
        client: Optional[httpx.Client] = None,
    ):
        raw_url = base_url or os.environ.get("A1_API_BASE_URL", "")
        self._base_url = raw_url.rstrip("/") if raw_url else ""
        self._timeout = timeout
        self._client = client or httpx.Client(timeout=self._timeout)

    @property
    def base_url(self) -> str:
        return self._base_url

    def _ensure_base_url(self) -> str:
        if not self._base_url:
            env_url = os.environ.get("A1_API_BASE_URL", "").strip()
            if env_url:
                self._base_url = env_url.rstrip("/")
            else:
                raise ValueError(
                    "A1_API_BASE_URL is not configured. Please set the A1_API_BASE_URL "
                    "environment variable (e.g. 'http://10.28.73.240:5000')."
                )
        return self._base_url

    def get_member(self, member_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch member demographic/profile details from A1.
        Endpoint: GET {A1_API_BASE_URL}/member/{member_id}
        Returns the inner 'member' dictionary or None if member not found (404).
        """
        base = self._ensure_base_url()
        url = f"{base}/member/{member_id}"

        try:
            response = self._client.get(url)
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Failed to connect to A1 backend at '{url}': {str(exc)}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"Request to A1 backend timed out at '{url}': {str(exc)}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"HTTP request to A1 backend failed at '{url}': {str(exc)}"
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code != 200:
            raise RuntimeError(
                f"A1 backend returned unexpected status {response.status_code} "
                f"for URL '{url}': {response.text}"
            )

        try:
            payload = response.json()
        except Exception as exc:
            raise ValueError(
                f"Invalid JSON payload returned from A1 backend at '{url}': {response.text}"
            ) from exc

        if isinstance(payload, dict) and "member" in payload:
            return payload["member"]

        # Fallback if A1 returns the member dict directly
        if isinstance(payload, dict):
            return payload

        return None

    def get_member_contributions(self, member_id: str) -> List[Dict[str, Any]]:
        """
        Fetch contribution history from A1.
        Endpoint: GET {A1_API_BASE_URL}/member/{member_id}/history
        Returns a list of contribution records.
        """
        base = self._ensure_base_url()
        url = f"{base}/member/{member_id}/history"

        try:
            response = self._client.get(url)
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Failed to connect to A1 backend at '{url}': {str(exc)}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"Request to A1 backend timed out at '{url}': {str(exc)}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"HTTP request to A1 backend failed at '{url}': {str(exc)}"
            ) from exc

        if response.status_code == 404:
            return []

        if response.status_code != 200:
            raise RuntimeError(
                f"A1 backend returned unexpected status {response.status_code} "
                f"for URL '{url}': {response.text}"
            )

        try:
            payload = response.json()
        except Exception as exc:
            raise ValueError(
                f"Invalid JSON payload returned from A1 backend at '{url}': {response.text}"
            ) from exc

        if isinstance(payload, dict) and "history" in payload:
            history_data = payload["history"]
            if isinstance(history_data, list):
                return history_data

        if isinstance(payload, list):
            return payload

        return []

    def get_member_score_inputs(self, member_id: str) -> ScoreInput:
        """
        Derives the canonical scoring metrics from A1 member and contribution records.
        Metrics:
          - on_time_pct: Percentage of contributions paid on time (0.0 to 100.0)
          - streak_count: Current consecutive on-time contribution streak from latest record backwards
          - tenure_cycles: Total completed payment cycles recorded
          - missed_payment_count: Total count of missed or late payments (paid_on_time=False)
        """
        member = self.get_member(member_id)
        if not member:
            raise KeyError(f"Member with ID '{member_id}' not found in A1 DataProvider.")

        contributions = self.get_member_contributions(member_id)

        if not contributions:
            return ScoreInput(
                member_id=str(member.get("member_id", member_id)),
                on_time_pct=0.0,
                streak_count=0,
                tenure_cycles=0,
                missed_payment_count=0,
            )

        # Sort chronologically by due_date and ID
        sorted_history = sorted(
            contributions,
            key=lambda x: (str(x.get("due_date", "")), int(x.get("id", 0) or 0)),
        )

        total_records = len(sorted_history)
        on_time_count = 0
        missed_count = 0

        for rec in sorted_history:
            if rec.get("paid_on_time") is True:
                on_time_count += 1
            else:
                missed_count += 1

        on_time_pct = (on_time_count / total_records) * 100.0 if total_records > 0 else 0.0

        # Calculate current consecutive streak backwards from the most recent record
        current_streak = 0
        for rec in reversed(sorted_history):
            if rec.get("paid_on_time") is True:
                current_streak += 1
            else:
                break

        tenure_cycles = total_records

        return ScoreInput(
            member_id=str(member.get("member_id", member_id)),
            on_time_pct=round(on_time_pct, 2),
            streak_count=current_streak,
            tenure_cycles=tenure_cycles,
            missed_payment_count=missed_count,
        )
