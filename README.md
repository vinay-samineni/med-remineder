📞💊 Medication Reminder System
A lightweight FastAPI-based reminder system for hospitals to notify patients via email (and future voice calls).

🚀 Overview
The Medication Reminder System is a minimal, fast, hospital-facing web tool that allows healthcare staff to:

Add patient details

Store medication schedule

Automatically trigger reminders

Notify patients via email (current prototype)

Notify via voice calls (future implementation — using MSG91 or other providers)

This prototype is fully functional with email reminders and serves as the foundation for a full production-ready system.

🏥 Why This Project?

Hospitals need reliable, automated ways to remind patients about their medication schedule.
This project provides:

Zero-auth, quick data entry (hospitals only)

🗣️ Voice Reminder Service (Planned)

Upcoming features include:

Integrating MSG91 voice API

Automated IVR calls to patient phone numbers

Webhook callback handling

Call status tracking

Error + retry logic

Logs for every call attempt

This README highlights the planned voice feature for future extension.

📂 Project Structure

med/
 ├── app.py              # FastAPI main app (routes, pages)
 
 ├── scheduler.py        # Background APScheduler jobs
 
 ├── email_client.py     # SMTP email sending utility
 
 ├── database.py         # DB connection (SQLite)
 
 ├── models.py           # SQLAlchemy table definitions
 
 ├── schemas.py          # Pydantic schemas
 
 ├── templates/
 │    └── index.html     # Frontend UI
 
 ├── requirements.txt    # Python dependencies
 
 ├── .env.example        # Template for environment variables
 
 └── README.md           # Project documentation

🔧 Installation & Setup

1. Clone the repo
   git clone https://github.com/your-username/med-reminder.git
   cd med-reminder
2. Create virtual environment
   python -m venv venv
   venv\Scripts\activate
3. Install dependencies
   pip install -r requirements.txt
4. Fill your details in .env

Run application
uvicorn app:app --reload --host 0.0.0.0 --port 8000

Test manual
Invoke-WebRequest -Uri "http://127.0.0.1:8000/call_now/1" -Method POST -Body ""

📞 Voice Call Integration (Future)

Planned feature:

Integrate MSG91 Voice API

Use hospital caller ID

Automated IVR message: “This is your medication reminder.”

Status callbacks handled by /webhook/msg91

Full call log tracking

Robust retry system

This will transform the prototype into a full hospital→patient communication platform.

🛠️ Tech Stack

FastAPI (backend + templating)

SQLite (lightweight DB)

APScheduler (cron-like scheduling)

Jinja2 (frontend templates)

SMTP (email sending)

MSG91 API (planned voice calls)

