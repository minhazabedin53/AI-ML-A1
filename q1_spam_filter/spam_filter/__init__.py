"""DPS970 Activity 1, Question 1: simple-reflex spam filter agent."""

from .agents import Agent, Environment, Rule, SimpleReflexAgentProgram, rule_match
from .email_percept import EmailPercept, parse_email, read_eml
from .environment import Decision, EmailEnvironment, performance
from .spam_agent import (
    BAD_WORD_THRESHOLD, MOVE_TO_EMAIL, MOVE_TO_SPAM, SPAM_FILTER_RULES,
    SpamFilterAgent, SpamFilterAgentFromConfig, count_bad_words,
    domain_matches, load_list,
)
