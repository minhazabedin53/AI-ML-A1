"""Run every test in the submission with one command:

    python run_tests.py

Runs the Question 1 and Question 2 suites (each from its own folder, so their
packages import cleanly) and exits non-zero if anything fails.
Uses only the Python standard library (unittest) - nothing to install.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUITES = [
    ("Question 1 - Spam filter agent", ROOT / "q1_spam_filter"),
    ("Question 2 - Water jugs BFS", ROOT / "q2_water_jugs"),
]


def main() -> int:
    failed = []
    for title, folder in SUITES:
        print(f"\n{'=' * 70}\n{title}\n{'=' * 70}", flush=True)
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-v"], cwd=folder)
        if result.returncode != 0:
            failed.append(title)
    print("\n" + ("ALL TESTS PASSED" if not failed else "FAILED: " + ", ".join(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
