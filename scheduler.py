# scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, date
import anyio
from typing import Any, Dict

from database import database
from models import patients, call_logs
from email_client import send_email   # synchronous email sender

scheduler = AsyncIOScheduler()

async def _safe_fetch_all(query):
    """
    Safely fetch rows from DB; if DB not connected yet, return empty list.
    """
    try:
        return await database.fetch_all(query)
    except Exception as e:
        print("[SCHEDULER] DB fetch failed (maybe not connected yet):", e)
        return []

async def check_and_trigger_calls():
    """
    Runs every minute:
      - Fetch all patients
      - If today is within start_date..end_date
      - If stored time equals current HH:MM, trigger email send (in a thread)
      - Record send metadata in call_logs table
    """
    now = datetime.now()  # local server time
    today = now.date()
    current_time = now.strftime("%H:%M")

    query = patients.select()
    rows = await _safe_fetch_all(query)

    if not rows:
        return

    for row in rows:
        try:
            # Convert Record -> dict so .get() works and access is consistent
            row = dict(row)

            # Normalize start_date / end_date to date objects if they are strings
            start = row.get("start_date")
            end = row.get("end_date")

            if isinstance(start, str):
                try:
                    start = datetime.strptime(start, "%Y-%m-%d").date()
                except Exception:
                    print(f"[SCHEDULER] Skipping row id={row.get('id')}: invalid start_date format {row.get('start_date')}")
                    continue

            if isinstance(end, str):
                try:
                    end = datetime.strptime(end, "%Y-%m-%d").date()
                except Exception:
                    print(f"[SCHEDULER] Skipping row id={row.get('id')}: invalid end_date format {row.get('end_date')}")
                    continue

            # Ensure start/end are date objects
            if not (isinstance(start, date) and isinstance(end, date)):
                print(f"[SCHEDULER] Skipping row id={row.get('id')}: start/end not valid dates")
                continue

            # Check date range
            if not (start <= today <= end):
                continue

            # Check time match
            scheduled_time = row.get("time")
            if isinstance(scheduled_time, str):
                scheduled_time = scheduled_time.strip()
            else:
                scheduled_time = str(scheduled_time)

            if scheduled_time != current_time:
                continue

            # Ready to send email
            name = row.get("name") or "Patient"
            recipient = row.get("email")
            phone = row.get("phone") or ""

            if not recipient:
                print(f"[SCHEDULER] No email for id={row.get('id')} (phone={phone}). Skipping.")
                continue

            subject = "Medication Reminder"
            body = f"Hello {name},\n\nThis is a reminder to take your medicine now.\n\nRegards,\nHospital"

            print(f"[SCHEDULER] Sending email to {recipient} for id={row.get('id')} at {current_time}")

            # Execute synchronous send_email in a thread so scheduler doesn't block
            try:
                result: Dict[str, Any] = await anyio.to_thread.run_sync(send_email, recipient, subject, body)
            except Exception as e:
                print(f"[SCHEDULER] Error sending email for id={row.get('id')}: {e}")
                result = {"ok": False, "error": str(e)}

            status_text = "sent" if result.get("ok") else "failed"

            # Log send result in call_logs table
            try:
                ins = call_logs.insert().values(
                    msg91_call_id=None,
                    status=status_text,
                    payload=str(result),
                    created_at=datetime.utcnow()
                )
                await database.execute(ins)
                print(f"[SCHEDULER] Logged email for id={row.get('id')} status={status_text}")
            except Exception as e:
                print(f"[SCHEDULER] Failed to write call_log for id={row.get('id')}: {e}")

        except Exception as e:
            # Use row.get safely here because row was converted to dict earlier
            try:
                rid = row.get("id")
            except Exception:
                rid = "<unknown>"
            print(f"[SCHEDULER] Unexpected error processing row id={rid}: {e}")


def start_scheduler():
    """
    Start the APScheduler job if not already started.
    """
    try:
        if not scheduler.get_jobs():
            scheduler.add_job(check_and_trigger_calls, "interval", seconds=60, id="med_reminder_check")
            scheduler.start()
            print("[SCHEDULER] Started and checking every 60 seconds.")
        else:
            print("[SCHEDULER] Scheduler already running with jobs.")
    except Exception as e:
        print("[SCHEDULER ERROR]", e)
