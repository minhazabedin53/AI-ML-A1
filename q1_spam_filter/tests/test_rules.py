"""Condition-action rules, list handling and bad-word counting."""

import tempfile
import unittest
from pathlib import Path

from spam_filter.email_percept import EmailPercept
from spam_filter.spam_agent import (
    BAD_WORD_THRESHOLD, MOVE_TO_EMAIL, MOVE_TO_SPAM, SpamFilterAgent,
    count_bad_words, domain_matches, load_list,
)

ALLOW = {"school.ca"}
RESTRICT = {"spammy.biz"}
BAD = {"free", "cash", "prize", "winner", "claim", "bonus", "act now"}


def percept(domain, body):
    return EmailPercept(filename="t.eml", sender=f"x@{domain}" if domain else "",
                        sender_domain=domain, subject="", body_text=body,
                        unreadable_parts=0)


def decide(domain, body, allow=ALLOW, restrict=RESTRICT, bad=BAD):
    agent = SpamFilterAgent(allow, restrict, bad)
    return agent.program(percept(domain, body)), agent.program.last_rule.name


class TestCountBadWords(unittest.TestCase):

    def test_counts_every_occurrence_case_insensitive(self):
        self.assertEqual(count_bad_words("FREE free Free!", BAD), 3)

    def test_whole_words_only(self):
        self.assertEqual(count_bad_words("freedom cashier prizes claimed", BAD), 0)

    def test_phrases(self):
        self.assertEqual(count_bad_words("Act now. ACT  NOW! act\nnow", BAD), 3)
        self.assertEqual(count_bad_words("act quickly, now", BAD), 0)

    def test_empty_text(self):
        self.assertEqual(count_bad_words("", BAD), 0)


class TestDomainMatching(unittest.TestCase):

    def test_exact_and_subdomain(self):
        self.assertTrue(domain_matches("school.ca", ALLOW))
        self.assertTrue(domain_matches("mail.school.ca", ALLOW))
        self.assertTrue(domain_matches("MAIL.School.CA", ALLOW))

    def test_lookalike_domains_do_not_match(self):
        self.assertFalse(domain_matches("evilschool.ca", ALLOW))
        self.assertFalse(domain_matches("school.ca.evil.com", ALLOW))

    def test_missing_domain(self):
        self.assertFalse(domain_matches(None, ALLOW))
        self.assertFalse(domain_matches("", ALLOW))


class TestLoadList(unittest.TestCase):

    def test_comments_blank_lines_and_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "list.txt"
            path.write_text("# header\n\nFree\n  cash  # trailing comment\nact now\n",
                            encoding="utf-8")
            self.assertEqual(load_list(path), frozenset({"free", "cash", "act now"}))


class TestRules(unittest.TestCase):

    def test_allow_list_wins_regardless_of_content(self):
        action, rule = decide("school.ca", "free cash prize winner claim bonus act now " * 3)
        self.assertEqual(action, MOVE_TO_EMAIL)
        self.assertIn("allow", rule)

    def test_restrict_list_is_spam_regardless_of_content(self):
        action, rule = decide("spammy.biz", "Lunch at noon?")
        self.assertEqual(action, MOVE_TO_SPAM)
        self.assertIn("restrict", rule)

    def test_threshold_is_more_than_five(self):
        self.assertEqual(BAD_WORD_THRESHOLD, 5)
        five = "free cash prize winner claim"
        six = five + " bonus"
        self.assertEqual(decide("other.com", five)[0], MOVE_TO_EMAIL)
        self.assertEqual(decide("other.com", six)[0], MOVE_TO_SPAM)

    def test_clean_mail_from_unknown_sender_is_email(self):
        action, rule = decide("other.com", "See you at the lab.")
        self.assertEqual(action, MOVE_TO_EMAIL)
        self.assertIn("default", rule)

    def test_missing_sender_uses_bad_word_rule(self):
        self.assertEqual(decide(None, "free " * 6)[0], MOVE_TO_SPAM)
        self.assertEqual(decide(None, "hello")[0], MOVE_TO_EMAIL)

    def test_domain_on_both_lists_is_trusted(self):
        """Documented precedence: allow list is checked first."""
        action, _ = decide("both.com", "hi", allow={"both.com"}, restrict={"both.com"})
        self.assertEqual(action, MOVE_TO_EMAIL)


if __name__ == "__main__":
    unittest.main()
