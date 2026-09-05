"""
Optional Live Smoke Test Script for Person A2 against Person A1 backend.

Usage:
  python tools/a2/smoke_test_a1_connection.py
  python tools/a2/smoke_test_a1_connection.py --base-url http://10.28.73.240:5000 --member 1
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.a2.integration.http_data_provider import HttpDataProvider
from backend.a2.scoring.service import ScoreService
from backend.a2.offers.service import OfferService


def main():
    parser = argparse.ArgumentParser(description="Live Smoke Test A1 Backend Connection")
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.environ.get("A1_API_BASE_URL", "http://10.28.73.240:5000"),
        help="Base URL for A1 backend (defaults to $A1_API_BASE_URL or http://10.28.73.240:5000)",
    )
    parser.add_argument(
        "--member",
        type=str,
        default="1",
        help="Member ID to test (default: 1)",
    )
    args = parser.parse_args()

    print(f"=== A1 LIVE SMOKE TEST ===")
    print(f"Target A1 Base URL: {args.base_url}")
    print(f"Testing Member ID: {args.member}")

    provider = HttpDataProvider(base_url=args.base_url)
    score_service = ScoreService(data_provider=provider)
    offer_service = OfferService(score_service=score_service, data_provider=provider)

    try:
        member = provider.get_member(args.member)
        print(f"\n[OK] Member Record: {json.dumps(member, indent=2)}")

        contributions = provider.get_member_contributions(args.member)
        print(f"[OK] History Records ({len(contributions)} entries): {json.dumps(contributions, indent=2)}")

        score = score_service.get_score_for_member(args.member)
        print(f"\n[OK] Calculated Score Result:")
        print(json.dumps(score.to_dict(), indent=2))

        offer = offer_service.get_offer_for_member(args.member)
        print(f"\n[OK] Tailored Credit Offer:")
        print(json.dumps(offer.to_dict(), indent=2))

        print("\n[SUCCESS] Live A1 connection and end-to-end scoring smoke test PASSED!")

    except Exception as exc:
        print(f"\n[ERROR] Smoke test failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
