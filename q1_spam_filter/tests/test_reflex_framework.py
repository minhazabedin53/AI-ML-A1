"""The generic agent framework (AIMA Figure 2.10) works on its own.

As a sanity check it is exercised with the textbook's REFLEX-VACUUM-AGENT
(Figure 2.8) expressed as condition-action rules."""

import unittest

from spam_filter.agents import Agent, Rule, SimpleReflexAgentProgram, rule_match


def vacuum_program():
    rules = [
        Rule("dirty", lambda s: s[1] == "Dirty", "Suck"),
        Rule("at A", lambda s: s[0] == "A", "Right"),
        Rule("at B", lambda s: s[0] == "B", "Left"),
    ]
    return SimpleReflexAgentProgram(rules, interpret_input=lambda percept: percept)


class TestSimpleReflexFramework(unittest.TestCase):

    def test_reflex_vacuum_agent_from_textbook(self):
        program = vacuum_program()
        self.assertEqual(program(("A", "Dirty")), "Suck")
        self.assertEqual(program(("B", "Dirty")), "Suck")
        self.assertEqual(program(("A", "Clean")), "Right")
        self.assertEqual(program(("B", "Clean")), "Left")

    def test_rule_match_returns_first_matching_rule(self):
        rules = [Rule("first", lambda s: s > 0, "a"), Rule("second", lambda s: s > 0, "b")]
        self.assertEqual(rule_match(5, rules).name, "first")
        self.assertIsNone(rule_match(-1, rules))

    def test_program_raises_if_no_rule_matches(self):
        program = SimpleReflexAgentProgram([Rule("never", lambda s: False, "x")], lambda p: p)
        with self.assertRaises(LookupError):
            program("anything")

    def test_agent_requires_callable_program(self):
        with self.assertRaises(ValueError):
            Agent(None)

    def test_same_percept_always_gives_same_action(self):
        """Simple reflex agents are memoryless: history does not matter."""
        program = vacuum_program()
        first = program(("A", "Clean"))
        for percept in [("B", "Dirty"), ("A", "Dirty"), ("B", "Clean")]:
            program(percept)
        self.assertEqual(program(("A", "Clean")), first)


if __name__ == "__main__":
    unittest.main()
