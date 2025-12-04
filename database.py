# database.py
from databases import Database
from sqlalchemy import MetaData, create_engine

# SQLite file path (relative to project root)
DATABASE_URL = "sqlite:///./med_reminder.db"

# Async database object used by `databases` library
database = Database(DATABASE_URL)

# SQLAlchemy metadata object (tables will attach to this)
metadata = MetaData()

# Sync engine used for table creation (connect_args needed for SQLite)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
