"""The agent's SENSOR: turns a .eml file into a percept.

An .eml file has plain-text headers followed by a body that may be MIME
multipart and encoded (base64, quoted-printable) or even encrypted.  As the
activity states, only parts of type ``text/*`` (including text attachments)
are readable by the agent; everything else is counted as unreadable and
ignored.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import parseaddr
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class EmailPercept:
    """Everything the sensor reports about one email."""

    filename: str
    sender: str                     # e-mail address taken from the From header
    sender_domain: Optional[str]    # lower-case domain, or None if missing
    subject: str
    body_text: str                  # all readable text: body + text attachments
    unreadable_parts: int           # non-text / undecodable MIME parts skipped


class _TextExtractor(HTMLParser):
    """Strip tags from an HTML part, ignoring <script> and <style> blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.chunks.append(data)


def html_to_text(markup: str) -> str:
    parser = _TextExtractor()
    parser.feed(markup)
    parser.close()
    return html.unescape(" ".join(parser.chunks))


def _decode_text_part(part: EmailMessage) -> Optional[str]:
    """Decode a text/* part (transfer encoding + charset). None if impossible."""
    try:
        text = part.get_content()
    except (LookupError, UnicodeError, ValueError, AssertionError):
        raw = part.get_payload(decode=True)
        if raw is None:
            return None
        text = raw.decode("utf-8", errors="replace")
    if not isinstance(text, str):
        return None
    if part.get_content_subtype() == "html":
        text = html_to_text(text)
    return text


def _pick_alternative(children: list[EmailMessage]) -> Optional[EmailMessage]:
    """multipart/alternative holds the SAME content in several formats.
    Read only one of them (prefer text/plain) so words are not double counted."""
    for wanted in ("text/plain", "text/html"):
        for child in children:
            if child.get_content_type() == wanted:
                return child
    return children[-1] if children else None  # RFC 2046: last = preferred


def _collect(part: EmailMessage, texts: list[str], unreadable: list[int]) -> None:
    ctype = part.get_content_type()
    if part.get_content_maintype() == "multipart":
        children = list(part.iter_parts())
        if part.get_content_subtype() == "alternative":
            chosen = _pick_alternative(children)
            if chosen is not None:
                _collect(chosen, texts, unreadable)
        else:
            for child in children:
                _collect(child, texts, unreadable)
    elif ctype == "message/rfc822":
        for inner in part.get_payload():
            _collect(inner, texts, unreadable)
    elif part.get_content_maintype() == "text":
        text = _decode_text_part(part)
        if text is None:
            unreadable[0] += 1
        else:
            texts.append(text)
    else:
        unreadable[0] += 1  # images, PDFs, encrypted blobs, ... are not readable


def sender_domain_of(from_header: str) -> tuple[str, Optional[str]]:
    """Return (address, domain).  The domain is taken from the real address,
    never from the display name, so 'prof@school.ca' <x@evil.com> -> evil.com."""
    _, address = parseaddr(from_header or "")
    address = address.strip()
    if "@" not in address:
        return address, None
    domain = address.rsplit("@", 1)[1].strip().strip(".").lower()
    return address, (domain or None)


def parse_email(raw: bytes, filename: str = "<memory>") -> EmailPercept:
    message = BytesParser(policy=policy.default).parsebytes(raw)
    address, domain = sender_domain_of(str(message.get("From", "")))
    texts: list[str] = []
    unreadable = [0]
    _collect(message, texts, unreadable)
    return EmailPercept(
        filename=filename,
        sender=address,
        sender_domain=domain,
        subject=str(message.get("Subject", "")),
        body_text="\n".join(texts),
        unreadable_parts=unreadable[0],
    )


def read_eml(path: str | Path) -> EmailPercept:
    path = Path(path)
    return parse_email(path.read_bytes(), filename=path.name)
