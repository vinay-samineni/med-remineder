# models.py
from sqlalchemy import Table, Column, Integer, String, Date, DateTime, Text
from datetime import datetime
from database import metadata, engine

# Patients table (updated: added email column)
patients = Table(
    "patients",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("patient_id", String, unique=True, nullable=False),
    Column("name", String, nullable=False),
    Column("phone", String, nullable=False),
    Column("email", String, nullable=True),  # <-- NEW FIELD
    Column("start_date", Date, nullable=False),
    Column("end_date", Date, nullable=False),
    Column("time", String, nullable=False),  # "HH:MM"
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Logs table — used for webhook logs and email logs
call_logs = Table(
    "call_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("msg91_call_id", String, nullable=True),  # kept for compatibility
    Column("status", String, nullable=True),
    Column("payload", Text, nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow),
)

def create_tables():
    """
    Creates tables if not exist.
    SQLite makes migrations difficult, so on dev:
      - delete med_reminder.db
      - restart server (tables will be recreated)
    """
    metadata.create_all(engine)
