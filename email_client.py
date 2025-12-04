# email_client.py
"""
Simple synchronous SMTP email sender.

Environment variables (put in .env):
  SMTP_HOST
  SMTP_PORT
  SMTP_USER
  SMTP_PASSWORD
  EMAIL_FROM    (optional; defaults to SMTP_USER)

Usage:
  from email_client import send_email
  res = send_email("recipient@example.com", "Subject", "Body text")
  if res["ok"]:
      # sent
"""

import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

def send_email(recipient: str, subject: str, body: str) -> dict:
    """
    Send an email synchronously.

    Returns:
      { "ok": bool, "error": str|None, "ts": iso-ts-string }
    """
    ts = datetime.utcnow().isoformat()
    if not (SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASSWORD):
        err = "SMTP configuration missing. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in .env"
        print("[EMAIL] " + err)
        return {"ok": False, "error": err, "ts": ts}

    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        print(f"[EMAIL] Sent to {recipient} at {ts}")
        return {"ok": True, "error": None, "ts": ts}
    except Exception as e:
        err = str(e)
        print(f"[EMAIL] Failed to send to {recipient} at {ts}: {err}")
        return {"ok": False, "error": err, "ts": ts}

# quick manual test when running this file directly (won't run automatically on import)
if __name__ == "__main__":
    print("EMAIL CLIENT TEST RUN")
    if not SMTP_USER:
        print("No SMTP configuration found in environment.")
    else:
        to = input("Recipient email: ").strip()
        subj = "Test: Medication Reminder"
        body = "This is a test email from med-reminder system."
        print(send_email(to, subj, body))
