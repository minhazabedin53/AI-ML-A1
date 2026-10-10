"""The spam-filter agent: a SIMPLE REFLEX AGENT (AIMA 4e Figure 2.10).

    percept --INTERPRET-INPUT--> state --RULE-MATCH--> rule --> rule.ACTION

Condition-action rules, checked in this order (first match wins):

    1. sender domain on the ALLOW list          -> MoveToEmail  (regardless of content)
    2. sender domain on the RESTRICT list       -> MoveToSpam   (regardless of content)
    3. more than 5 bad-word hits in the body    -> MoveToSpam
    4. otherwise                                -> MoveToEmail

Rule 1 is placed before rule 2 so that a domain accidentally listed on both
lists is trusted; the activity states allow-listed mail is non-spam
"regardless of its contents", and rule 3 explicitly exempts allow-listed mail.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .agents import Agent, Rule, SimpleReflexAgentProgram
from .email_percept import EmailPercept

MOVE_TO_SPAM = "MoveToSpam"
MOVE_TO_EMAIL = "MoveToEmail"
ACTIONS = (MOVE_TO_SPAM, MOVE_TO_EMAIL)

BAD_WORD_THRESHOLD = 5  # "more than 5" => 6 or more hits is spam

_WORD = re.compile(r"[a-z0-9]+")


# --------------------------------------------------------------------------
# Knowledge the agent has access to (the three lists)
# --------------------------------------------------------------------------
def load_list(path: str | Path) -> frozenset[str]:
    """One entry per line; blank lines and lines starting with # are ignored."""
    entries = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            entries.add(line)
    return frozenset(entries)


def domain_matches(domain: Optional[str], listed: Iterable[str]) -> bool:
    """True if ``domain`` is a listed domain or a sub-domain of one.
    e.g. 'mail.example.com' matches the entry 'example.com'."""
    if not domain:
        return False
    domain = domain.lower().strip(".")
    for entry in listed:
        entry = entry.lower().strip(".")
        if domain == entry or domain.endswith("." + entry):
            return True
    return False


def tokenize(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def count_bad_words(text: str, bad_words: Iterable[str]) -> int:
    """Count every occurrence of a listed word in ``text`` (case-insensitive,
    whole words only).  An entry containing spaces (e.g. 'act now') is a
    phrase and is counted each time the words appear consecutively."""
    tokens = tokenize(text)
    singles = set()
    phrases = []
    for entry in bad_words:
        parts = tokenize(entry)
        if len(parts) == 1:
            singles.add(parts[0])
        elif len(parts) > 1:
            phrases.append(parts)

    hits = sum(1 for token in tokens if token in singles)
    for phrase in phrases:
        n = len(phrase)
        hits += sum(1 for i in range(len(tokens) - n + 1) if tokens[i:i + n] == phrase)
    return hits


# --------------------------------------------------------------------------
# INTERPRET-INPUT: percept -> abstract state description
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class EmailState:
    sender_domain: Optional[str]
    on_allow_list: bool
    on_restrict_list: bool
    bad_word_count: int


def make_interpret_input(allow_list, restrict_list, bad_words):
    allow_list, restrict_list, bad_words = (
        frozenset(allow_list), frozenset(restrict_list), frozenset(bad_words))

    def interpret_input(percept: EmailPercept) -> EmailState:
        return EmailState(
            sender_domain=percept.sender_domain,
            on_allow_list=domain_matches(percept.sender_domain, allow_list),
            on_restrict_list=domain_matches(percept.sender_domain, restrict_list),
            bad_word_count=count_bad_words(percept.body_text, bad_words),
        )

    return interpret_input


# --------------------------------------------------------------------------
# The condition-action rules
# --------------------------------------------------------------------------
SPAM_FILTER_RULES = [
    Rule("sender domain on allow list",
         lambda s: s.on_allow_list, MOVE_TO_EMAIL),
    Rule("sender domain on restrict list",
         lambda s: s.on_restrict_list, MOVE_TO_SPAM),
    Rule(f"more than {BAD_WORD_THRESHOLD} bad words in body",
         lambda s: s.bad_word_count > BAD_WORD_THRESHOLD, MOVE_TO_SPAM),
    Rule("no spam rule matched (default)",
         lambda s: True, MOVE_TO_EMAIL),
]


def SpamFilterAgent(allow_list, restrict_list, bad_words) -> Agent:
    """Build the agent: a body (Agent) holding a simple-reflex program."""
    program = SimpleReflexAgentProgram(
        SPAM_FILTER_RULES,
        make_interpret_input(allow_list, restrict_list, bad_words),
    )
    return Agent(program)


def SpamFilterAgentFromConfig(config_dir: str | Path) -> Agent:
    """Load allow_list.txt, restrict_list.txt and bad_words.txt from a folder."""
    config_dir = Path(config_dir)
    return SpamFilterAgent(
        load_list(config_dir / "allow_list.txt"),
        load_list(config_dir / "restrict_list.txt"),
        load_list(config_dir / "bad_words.txt"),
    )
