"""End-to-end: the agent sorts the test inbox into email/ and spam/ folders."""

import contextlib
import csv
import io
import random
import shutil
import tempfile
import unittest
from pathlib import Path

from spam_filter.__main__ import main as cli_main
from spam_filter.email_percept import read_eml
from spam_filter.environment import EmailEnvironment, performance
from spam_filter.spam_agent import MOVE_TO_SPAM, SpamFilterAgentFromConfig

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "test_data" / "inbox"
CONFIG = ROOT / "config"


def expected_labels():
    with open(ROOT / "test_data" / "expected_labels.csv", newline="", encoding="utf-8") as f:
        return {row["filename"]: row["expected_folder"] for row in csv.DictReader(f)}


class TestEmailEnvironment(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.inbox = self.tmp / "inbox"
        shutil.copytree(INBOX, self.inbox)
        self.expected = expected_labels()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def make_env(self, copy=False):
        env = EmailEnvironment(self.inbox, self.tmp / "email", self.tmp / "spam", copy=copy)
        env.add_agent(SpamFilterAgentFromConfig(CONFIG))
        return env

    def test_every_test_email_has_an_expected_label(self):
        self.assertEqual(set(self.expected), {p.name for p in INBOX.glob("*.eml")})

    def test_all_emails_land_in_the_correct_folder(self):
        log = self.make_env().run()
        for name, folder in self.expected.items():
            with self.subTest(email=name):
                self.assertTrue((self.tmp / folder / name).exists(),
                                f"{name} should be in {folder}/")
        self.assertEqual(performance(log, self.expected), 1.0)

    def test_files_are_moved_not_lost_or_duplicated(self):
        self.make_env().run()
        self.assertEqual(list(self.inbox.glob("*.eml")), [])
        placed = list((self.tmp / "email").iterdir()) + list((self.tmp / "spam").iterdir())
        self.assertEqual(sorted(p.name for p in placed), sorted(self.expected))

    def test_copy_mode_keeps_inbox(self):
        self.make_env(copy=True).run()
        self.assertEqual(len(list(self.inbox.glob("*.eml"))), len(self.expected))

    def test_order_of_emails_does_not_matter(self):
        """Episodic environment + memoryless agent: shuffling the order of the
        percepts never changes any decision."""
        agent = SpamFilterAgentFromConfig(CONFIG)
        percepts = [read_eml(p) for p in sorted(INBOX.glob("*.eml"))]
        baseline = {p.filename: agent.program(p) for p in percepts}
        for seed in range(5):
            random.Random(seed).shuffle(percepts)
            self.assertEqual({p.filename: agent.program(p) for p in percepts}, baseline)

    def test_log_records_rule_that_fired(self):
        log = {d.filename: d for d in self.make_env().run()}
        self.assertIn("allow", log["01_allow_list_with_bad_words.eml"].rule)
        self.assertIn("restrict", log["02_restrict_list_clean_body.eml"].rule)
        self.assertIn("bad words", log["05_six_bad_words.eml"].rule)
        self.assertEqual(log["05_six_bad_words.eml"].action, MOVE_TO_SPAM)

    def test_existing_file_is_never_overwritten(self):
        (self.tmp / "spam").mkdir()
        (self.tmp / "spam" / "02_restrict_list_clean_body.eml").write_text("old")
        self.make_env().run()
        self.assertEqual((self.tmp / "spam" / "02_restrict_list_clean_body.eml").read_text(), "old")
        self.assertTrue((self.tmp / "spam" / "02_restrict_list_clean_body-1.eml").exists())

    def test_non_eml_files_are_ignored(self):
        (self.inbox / "notes.txt").write_text("free cash prize winner claim bonus")
        self.make_env().run()
        self.assertTrue((self.inbox / "notes.txt").exists())

    def test_missing_inbox_raises(self):
        with self.assertRaises(FileNotFoundError):
            EmailEnvironment(self.tmp / "nope", self.tmp / "e", self.tmp / "s")

    def test_command_line_interface(self):
        out = self.tmp / "cli_out"
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            code = cli_main(["--inbox", str(self.inbox), "--out", str(out), "--copy"])
        self.assertEqual(code, 0)
        self.assertIn("19 emails processed", printed.getvalue())
        spam = {p.name for p in (out / "spam").iterdir()}
        self.assertEqual(spam, {n for n, f in self.expected.items() if f == "spam"})


if __name__ == "__main__":
    unittest.main()
