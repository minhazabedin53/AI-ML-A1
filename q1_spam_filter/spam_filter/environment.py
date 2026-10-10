"""The task environment: an inbox folder of .eml files plus the two output
folders (email/ and spam/).

* percept(agent)          - SENSOR: read and parse the next unprocessed .eml
* execute_action(agent,a) - ACTUATOR: move (or copy) that file to spam/ or email/

Each email is one episode: the environment hands the agent one email, the
agent acts once, and the next email is unaffected by the previous decision.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .agents import Agent, Environment
from .email_percept import EmailPercept, read_eml
from .spam_agent import ACTIONS, MOVE_TO_SPAM


@dataclass(frozen=True)
class Decision:
    filename: str
    action: str
    rule: Optional[str]
    destination: Path


class EmailEnvironment(Environment):

    def __init__(self, inbox_dir, email_dir, spam_dir, copy: bool = False,
                 sensor: Callable[[Path], EmailPercept] = read_eml):
        super().__init__()
        self.inbox_dir = Path(inbox_dir)
        self.email_dir = Path(email_dir)
        self.spam_dir = Path(spam_dir)
        self.copy = copy
        self.sensor = sensor
        if not self.inbox_dir.is_dir():
            raise FileNotFoundError(f"Inbox folder not found: {self.inbox_dir}")
        self.email_dir.mkdir(parents=True, exist_ok=True)
        self.spam_dir.mkdir(parents=True, exist_ok=True)
        self.pending: list[Path] = sorted(
            p for p in self.inbox_dir.iterdir()
            if p.is_file() and p.suffix.lower() == ".eml")
        self.log: list[Decision] = []

    # ------------------------------------------------------------------ sensor
    def percept(self, agent: Agent) -> EmailPercept:
        return self.sensor(self.pending[0])

    # ---------------------------------------------------------------- actuator
    def execute_action(self, agent: Agent, action: str) -> None:
        if action not in ACTIONS:
            raise ValueError(f"Unknown action {action!r}")
        source = self.pending.pop(0)
        folder = self.spam_dir if action == MOVE_TO_SPAM else self.email_dir
        destination = self._free_name(folder / source.name)
        if self.copy:
            shutil.copy2(source, destination)
        else:
            shutil.move(str(source), str(destination))
        rule = getattr(agent.program, "last_rule", None)
        self.log.append(Decision(source.name, action,
                                 rule.name if rule else None, destination))

    def is_done(self) -> bool:
        return not self.pending

    def run(self, steps: Optional[int] = None) -> list[Decision]:
        super().run(steps if steps is not None else len(self.pending))
        return self.log

    @staticmethod
    def _free_name(path: Path) -> Path:
        """Never overwrite: add -1, -2, ... if the name is taken."""
        candidate, n = path, 1
        while candidate.exists():
            candidate = path.with_name(f"{path.stem}-{n}{path.suffix}")
            n += 1
        return candidate


def performance(log: list[Decision], expected: dict[str, str]) -> float:
    """Performance measure used in the tests: fraction of emails placed in the
    folder required by the rules ('spam' or 'email')."""
    if not log:
        return 0.0
    correct = sum(
        1 for d in log
        if expected.get(d.filename) == ("spam" if d.action == MOVE_TO_SPAM else "email"))
    return correct / len(log)
