#!/usr/bin/env python3
import imaplib2
import os
import sys
import email

# Test IMAP connection
host = "imap.gmail.com"
port = 993
username = os.environ.get("GMAIL_USERNAME")
password = os.environ.get("GMAIL_APP_PW")

if not username or not password:
    print("Set GMAIL_USERNAME and GMAIL_APP_PW in your environment")
    sys.exit(1)

try:
    server = imaplib2.IMAP4_SSL(host, port)
    server.login(username, password)
    print("Login successful")
    server.select("INBOX")
    print("Selected INBOX")
    status, messages = server.search(None, "ALL")
    ids = messages[0].split()
    print(f"Total messages in INBOX: {len(ids)}")
    if ids:
        # Get the last 10 message subjects
        for msgid in ids[-10:]:
            status, data = server.fetch(msgid, "(RFC822.HEADER)")
            if status == "OK":
                m = email.message_from_bytes(data[0][1])
                subject = m.get("Subject", "")
                print(f"Subject: {subject}")
    server.logout()
    print("Test complete")
except Exception as e:
    print(f"Error: {e}")
