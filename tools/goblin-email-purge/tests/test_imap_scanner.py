import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from imap_scanner import scan_inbox_for_matches


class FakeIMAP:
    def __init__(self, header_bytes):
        self.header_bytes = header_bytes

    def login(self, username, password):
        return "OK"

    def select(self, mailbox):
        return "OK", []

    def search(self, charset, term):
        return "OK", [b"1"]

    def fetch(self, msgid, spec):
        return "OK", [(b"1 (RFC822.HEADER)", self.header_bytes)]

    def logout(self):
        return "OK"


def test_scan_detects_provider_and_list_unsubscribe(monkeypatch):
    header = b"Subject: Welcome to Tinder\r\nFrom: no-reply@tinder.com\r\nList-Unsubscribe: <mailto:unsubscribe@tinder.com>, <https://tinder.com/unsubscribe>\r\n\r\n"
    fake_imap = FakeIMAP(header)

    def fake_imap_ssl(host, port):
        return fake_imap

    monkeypatch.setattr("imaplib.IMAP4_SSL", fake_imap_ssl)
    cfg = {
        "imap": {
            "host": "imap.example",
            "username": "user",
            "password": "pw",
            "mailbox": "INBOX",
        }
    }
    matches = scan_inbox_for_matches(cfg)
    assert len(matches) == 1
    m = matches[0]
    assert "tinder" in [p.lower() for p in m.get("providers", [])]
    assert "mailto:unsubscribe@tinder.com" in m.get(
        "list_unsubscribe"
    ) or "https://tinder.com/unsubscribe" in "".join(
        m.get("list_unsubscribe")
        if isinstance(m.get("list_unsubscribe"), list)
        else [m.get("list_unsubscribe")]
    )


def test_scan_uses_environment_username_when_config_omits_identity(monkeypatch):
    """Public config must not need a committed personal email address."""
    monkeypatch.setenv("GMAIL_USERNAME", "mailbox@example.invalid")
    header = b"Subject: Welcome to Tinder\r\nFrom: no-reply@tinder.com\r\n\r\n"
    logged_in = []

    class IdentityCheckingIMAP(FakeIMAP):
        def login(self, username, password):
            logged_in.append((username, password))
            return "OK"

    monkeypatch.setattr("imaplib.IMAP4_SSL", lambda host, port: IdentityCheckingIMAP(header))
    matches = scan_inbox_for_matches({
        "imap": {
            "host": "imap.example",
            "username": "",
            "password": "pw",
            "mailbox": "INBOX",
        }
    })
    assert logged_in == [("mailbox@example.invalid", "pw")]
    assert len(matches) == 1


def test_environment_username_overrides_committed_config(monkeypatch):
    monkeypatch.setenv("GMAIL_USERNAME", "current@example.invalid")
    header = b"Subject: Welcome to Tinder\r\nFrom: no-reply@tinder.com\r\n\r\n"
    logged_in = []

    class IdentityCheckingIMAP(FakeIMAP):
        def login(self, username, password):
            logged_in.append(username)
            return "OK"

    monkeypatch.setattr("imaplib.IMAP4_SSL", lambda host, port: IdentityCheckingIMAP(header))
    scan_inbox_for_matches({
        "imap": {"host": "imap.example", "username": "old@example.invalid", "password": "pw"}
    })
    assert logged_in == ["current@example.invalid"]
