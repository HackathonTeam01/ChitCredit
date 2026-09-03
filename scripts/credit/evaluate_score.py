"""
Command-line utility to evaluate Chit Credit Score and Credit Offer for any member or custom parameters.

Usage:
  python scripts/credit/evaluate_score.py --member CHT-009
  python scripts/credit/evaluate_score.py --on-time 92 --streak 7 --tenure 5 --missed 0
  python scripts/credit/evaluate_score.py --all-mock
"""

import argparse
import json
import sys
from pathlib import Path

# Add workspace root to sys.path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.a2.scoring.service import default_score_service, ScoreService
from backend.a2.offers.service import default_offer_service
from backend.a2.integration.data_provider import MockDataProvider


def main():
    parser = argparse.ArgumentParser(description="Chit Credit Score & Offer Evaluator")
    parser.add_argument("--member", type=str, help="Member ID to evaluate (e.g. CHT-009)")
    parser.add_argument("--on-time", type=float, help="On-time payment percentage (0-100)")
    parser.add_argument("--streak", type=int, default=0, help="Consecutive on-time payments count")
    parser.add_argument("--tenure", type=int, default=0, help="Completed chit cycles count")
    parser.add_argument("--missed", type=int, default=0, help="Missed payments count")
    parser.add_argument("--all-mock", action="store_true", help="Evaluate all 18 mock members")

    args = parser.parse_args()

    if args.all_mock:
        provider = MockDataProvider()
        service = ScoreService(data_provider=provider)
        print("=== 18-MEMBER CHIT CREDIT SCORE & OFFER AUDIT ===")
        print(f"{'Member ID':<10} {'Name':<15} {'Score':<7} {'Band':<18} {'Eligible Limit':<15} {'Rate'}")
        print("-" * 75)
        for mid in provider.list_all_member_ids():
            member = provider.get_member(mid)
            score_res = service.get_score_for_member(mid)
            offer_res = default_offer_service.get_offer_for_member(mid)
            print(
                f"{mid:<10} {member['name']:<15} {score_res.score_value:<7} "
                f"{score_res.score_band:<18} INR {offer_res.eligible_amount:<10,.0f} {offer_res.interest_rate}%"
            )
        return

    if args.member:
        score_res = default_score_service.get_score_for_member(args.member)
        offer_res = default_offer_service.get_offer_for_member(args.member)
        output = {
            "score": score_res.to_dict(),
            "credit_offer": offer_res.to_dict(),
        }
        print(json.dumps(output, indent=2))
        return

    if args.on_time is not None:
        score_res = default_score_service.calculate_custom_score(
            on_time_pct=args.on_time,
            streak_count=args.streak,
            tenure_cycles=args.tenure,
            missed_payment_count=args.missed,
            member_id="custom-user",
        )
        offer_res = default_offer_service.get_offer_for_band(score_res.score_band, member_id="custom-user")
        output = {
            "score": score_res.to_dict(),
            "credit_offer": offer_res.to_dict(),
        }
        print(json.dumps(output, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
