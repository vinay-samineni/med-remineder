# schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import date

class PatientCreate(BaseModel):
    patient_id: str
    name: str
    phone: str
    email: Optional[str] = None
    start_date: date
    end_date: date
    time: str   # "HH:MM"
