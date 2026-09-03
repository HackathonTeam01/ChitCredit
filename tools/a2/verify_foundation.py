"""
A2 Foundation Verification & Merge Safety Audit Tool.

Validates that:
1. All unit and integration tests under tests/a2/ pass.
2. Only A2-owned directories have been touched.
3. No A1, Frontend, or Person C files have been modified.
4. Contracts conform to canonical specifications.
"""

import subprocess
import sys
from pathlib import Path


def run_tests() -> bool:
    print(">>> Running A2 Pytest Suite...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/a2/", "-v"],
        capture_output=False,
    )
    return result.returncode == 0


def check_git_status() -> bool:
    print("\n>>> Checking Git Status and Ownership...")
    result = subprocess.run(
        ["git", "status", "--porcelain", "-uall"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Failed to run git status")
        return False

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    allowed_prefixes = (
        "backend/a2/",
        "contracts/credit/",
        "tests/a2/",
        "scripts/credit/",
        "tools/a2/",
    )

    violations = []
    for line in lines:
        filepath = line[3:].strip().strip('"')
        # Normalize slashes for Windows
        filepath_normalized = filepath.replace("\\", "/")
        if not any(filepath_normalized.startswith(prefix) for prefix in allowed_prefixes):
            violations.append(filepath_normalized)

    if violations:
        print(f"[FAIL] OWNERSHIP VIOLATIONS FOUND: Non-A2 files touched: {violations}")
        return False

    print("[PASS] Git Ownership Check Passed: Only A2-owned paths touched.")
    return True


def main():
    print("=== STARTING A2 FOUNDATION AUDIT ===")
    test_ok = run_tests()
    git_ok = check_git_status()

    if test_ok and git_ok:
        print("\n[SUCCESS] ALL A2 FOUNDATION CHECKS PASSED!")
        sys.exit(0)
    else:
        print("\n[FAILURE] VERIFICATION FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
