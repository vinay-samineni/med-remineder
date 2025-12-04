# app.py
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
import html
from datetime import datetime, date
from typing import Optional, Any, Dict

# Local modules
from database import database
from models import patients, create_tables, call_logs
from schemas import PatientCreate
from scheduler import start_scheduler
from email_client import send_email  # email sender


app = FastAPI(title="Medication Reminder (Email Version)")

templates = Jinja2Templates(directory="templates")

# CORS (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# ------------------------------
# STARTUP / SHUTDOWN
# ------------------------------
@app.on_event("startup")
async def startup():
    create_tables()
    await database.connect()
    start_scheduler()
    print("Startup complete — DB connected and scheduler started.")


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    print("Shutdown complete.")


# ------------------------------
# HOME PAGE
# ------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    query = patients.select().order_by(patients.c.id.desc())
    rows = await database.fetch_all(query)
    return templates.TemplateResponse("index.html", {"request": request, "patients": rows})


# ------------------------------
# ADD PATIENT
# ------------------------------
@app.post("/add")
async def add_patient(
    patient_id: str = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    email: Optional[str] = Form(None),
    start_date: str = Form(...),
    end_date: str = Form(...),
    time: str = Form(...),
):

    # Convert dates
    try:
        start_dt: date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt: date = datetime.strptime(end_date, "%Y-%m-%d").date()
        datetime.strptime(time, "%H:%M")  # validate time format
    except Exception as e:
        return JSONResponse({"error": "Invalid date/time format", "detail": str(e)}, status_code=400)

    new_data = {
        "patient_id": patient_id.strip(),
        "name": name.strip(),
        "phone": phone.strip(),
        "email": email.strip() if email else None,
        "start_date": start_dt,
        "end_date": end_dt,
        "time": time.strip(),
    }

    try:
        await database.execute(patients.insert().values(**new_data))
    except Exception as e:
        return JSONResponse({"error": "DB insert failed", "detail": str(e)}, status_code=500)

    return RedirectResponse("/", status_code=303)


# ------------------------------
# DELETE PATIENT
# ------------------------------
@app.post("/delete")
async def delete_patient(row_id: int = Form(...)):
    query = patients.delete().where(patients.c.id == row_id)
    await database.execute(query)
    return RedirectResponse("/", status_code=303)


# ------------------------------
# LEGACY VOICE XML (kept for compatibility)
# ------------------------------
@app.get("/voice", response_class=Response)
async def voice(message: Optional[str] = None):
    msg = message or "Hello. This is a reminder to take your medicine now."
    safe_msg = html.escape(msg)
    xml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Say>{safe_msg}</Say></Response>"
    return Response(content=xml, media_type="application/xml")


# ------------------------------
# MSG91 WEBHOOK (optional logging)
# ------------------------------
@app.post("/webhook/msg91")
async def webhook_msg91(request: Request):
    try:
        data = await request.json()
    except:
        data = dict(await request.form())

    msg91_id = data.get("call_id")
    status = data.get("status") or "unknown"

    try:
        await database.execute(
            call_logs.insert().values(
                msg91_call_id=msg91_id,
                status=status,
                payload=str(data),
                created_at=datetime.utcnow()
            )
        )
    except Exception as e:
        print("Webhook logging error:", e)

    return JSONResponse({"ok": True})


# ------------------------------
# MANUAL TRIGGER FOR TESTING
# ------------------------------
@app.post("/call_now/{row_id}")
async def call_now(row_id: int, background_tasks: BackgroundTasks):
    query = patients.select().where(patients.c.id == row_id)
    row = await database.fetch_one(query)

    if not row:
        return JSONResponse({"error": "not found"}, status_code=404)

    # convert Record -> dict so we can use .get safely
    row = dict(row)

    recipient = row.get("email")
    if not recipient:
        return JSONResponse({"error": "no email stored for this patient"}, status_code=400)

    subject = "Medication Reminder"
    body = f"Hello {row.get('name')},\nThis is a reminder to take your medication now."

    # Schedule email send in background
    background_tasks.add_task(send_email, recipient, subject, body)

    return JSONResponse({"ok": True, "emailed": recipient})
