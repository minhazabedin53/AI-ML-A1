"""The sensor: reading .eml files, decoding bodies and text attachments."""

import unittest
from pathlib import Path

from spam_filter.email_percept import html_to_text, parse_email, read_eml, sender_domain_of

INBOX = Path(__file__).resolve().parent.parent / "test_data" / "inbox"


class TestSenderDomain(unittest.TestCase):

    def test_display_name_and_address(self):
        self.assertEqual(sender_domain_of("Prof <p@Seneca.CA>"), ("p@Seneca.CA", "seneca.ca"))

    def test_display_name_cannot_spoof_domain(self):
        self.assertEqual(sender_domain_of('"a@school.ca" <x@evil.com>')[1], "evil.com")

    def test_missing_or_malformed(self):
        self.assertIsNone(sender_domain_of("")[1])
        self.assertIsNone(sender_domain_of("not an address")[1])


class TestBodyExtraction(unittest.TestCase):

    def test_plain_body(self):
        p = read_eml(INBOX / "06_clean_personal_email.eml")
        self.assertIn("study group", p.body_text)
        self.assertEqual(p.sender_domain, "gmail.com")

    def test_base64_body_is_decoded(self):
        p = read_eml(INBOX / "07_base64_encoded_body.eml")
        self.assertIn("bitcoin wallet", p.body_text)

    def test_quoted_printable_body_is_decoded(self):
        p = read_eml(INBOX / "08_quoted_printable_body.eml")
        self.assertIn("free drinks", p.body_text)  # was split across a soft line break

    def test_html_tags_and_css_are_stripped(self):
        p = read_eml(INBOX / "09_html_only_body.eml")
        self.assertIn("Click here to claim", p.body_text)
        self.assertNotIn("<b>", p.body_text)
        self.assertNotIn("color", p.body_text)

    def test_text_attachment_is_read(self):
        p = read_eml(INBOX / "10_text_attachment_with_bad_words.eml")
        self.assertIn("Guaranteed cash bonus", p.body_text)

    def test_binary_attachment_is_not_read(self):
        p = read_eml(INBOX / "11_binary_attachment_not_readable.eml")
        self.assertNotIn("lottery", p.body_text)
        self.assertEqual(p.unreadable_parts, 1)

    def test_subject_is_not_part_of_body(self):
        p = read_eml(INBOX / "17_bad_words_in_subject_only.eml")
        self.assertIn("FREE", p.subject)
        self.assertNotIn("FREE", p.body_text)

    def test_multipart_alternative_read_once(self):
        p = read_eml(INBOX / "18_multipart_alternative_not_double_counted.eml")
        self.assertEqual(p.body_text.count("Weekend sale"), 1)

    def test_missing_from_header(self):
        p = read_eml(INBOX / "16_missing_from_header.eml")
        self.assertIsNone(p.sender_domain)

    def test_parse_raw_bytes(self):
        raw = b"From: a@b.com\nSubject: hi\n\nhello world\n"
        p = parse_email(raw)
        self.assertEqual((p.sender_domain, p.body_text.strip()), ("b.com", "hello world"))

    def test_html_to_text_unescapes_entities(self):
        self.assertIn("Tom & Jerry", html_to_text("<p>Tom &amp; Jerry</p>"))


if __name__ == "__main__":
    unittest.main()
