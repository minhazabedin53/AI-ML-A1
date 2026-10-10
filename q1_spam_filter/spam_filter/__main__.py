"""Command-line entry point.

    python -m spam_filter --inbox test_data/inbox --out output --copy

Sorts every .eml file in --inbox into <out>/email and <out>/spam.
Without --copy the files are moved, as the activity specifies.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from .environment import EmailEnvironment
from .spam_agent import MOVE_TO_SPAM, SpamFilterAgentFromConfig

HERE = Path(__file__).resolve().parent.parent


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Simple-reflex spam filter agent")
    parser.add_argument("--inbox", required=True, help="folder containing .eml files")
    parser.add_argument("--out", default="output",
                        help="output folder; email/ and spam/ are created inside it")
    parser.add_argument("--config", default=str(HERE / "config"),
                        help="folder with allow_list.txt, restrict_list.txt, bad_words.txt")
    parser.add_argument("--copy", action="store_true",
                        help="copy instead of move (keeps the inbox intact)")
    args = parser.parse_args(argv)

    out = Path(args.out)
    env = EmailEnvironment(args.inbox, out / "email", out / "spam", copy=args.copy)
    env.add_agent(SpamFilterAgentFromConfig(args.config))
    log = env.run()

    width = max((len(d.filename) for d in log), default=10)
    print(f"{'EMAIL FILE'.ljust(width)}  {'FOLDER':6}  RULE THAT FIRED")
    print(f"{'-' * width}  {'-' * 6}  {'-' * 34}")
    for d in log:
        folder = "spam" if d.action == MOVE_TO_SPAM else "email"
        print(f"{d.filename.ljust(width)}  {folder:6}  {d.rule}")
    counts = Counter("spam" if d.action == MOVE_TO_SPAM else "email" for d in log)
    print(f"\n{len(log)} emails processed: {counts['email']} to {out / 'email'}, "
          f"{counts['spam']} to {out / 'spam'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
