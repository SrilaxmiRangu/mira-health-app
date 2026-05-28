"""
MIRA - Medical Intelligence Robotic Automation
Health Prediction Application - Backend (FastAPI + SQLite)
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import sqlite3
import os
import httpx
import json
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()  # Load ANTHROPIC_API_KEY from .env

app = FastAPI(title="MIRA Health Prediction API")

# ── Database Setup ──────────────────────────────────────────────────────────────
DB_PATH = "mira.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name   TEXT    NOT NULL,
                dob         TEXT    NOT NULL,
                email       TEXT    NOT NULL,
                glucose     REAL    NOT NULL,
                haemoglobin REAL    NOT NULL,
                cholesterol REAL    NOT NULL,
                remarks     TEXT,
                created_at  TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

init_db()

# ── Pydantic Models ─────────────────────────────────────────────────────────────
class PatientCreate(BaseModel):
    full_name:   str
    dob:         str          # YYYY-MM-DD
    email:       str
    glucose:     float
    haemoglobin: float
    cholesterol: float

    @field_validator("dob")
    @classmethod
    def dob_not_future(cls, v):
        try:
            d = datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be YYYY-MM-DD format")
        if d >= date.today():
            raise ValueError("Date of birth cannot be a future date")
        return v

    @field_validator("email")
    @classmethod
    def valid_email(cls, v):
        import re
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("glucose", "haemoglobin", "cholesterol")
    @classmethod
    def positive_values(cls, v):
        if v <= 0:
            raise ValueError("Blood test values must be positive numbers")
        return v

class PatientUpdate(PatientCreate):
    pass

class PatientResponse(BaseModel):
    id:          int
    full_name:   str
    dob:         str
    email:       str
    glucose:     float
    haemoglobin: float
    cholesterol: float
    remarks:     Optional[str]
    created_at:  str

# ── AI Health Prediction ────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

async def get_ai_health_prediction(patient: PatientCreate) -> str:
    """Call Anthropic Claude API to generate health prediction remarks."""
    if not ANTHROPIC_API_KEY:
        return generate_rule_based_remarks(patient)

    prompt = f"""You are a medical AI assistant. Based on the following patient blood test results, 
provide a brief health assessment (2-3 sentences max). Be concise and clinically informative.
Do NOT provide a diagnosis — only flag potential risk areas and suggest follow-up.

Patient Details:
- Age: {calculate_age(patient.dob)} years
- Glucose: {patient.glucose} mg/dL (Normal: 70-99 mg/dL fasting)
- Haemoglobin: {patient.haemoglobin} g/dL (Normal: Men 13.8-17.2, Women 12.1-15.1 g/dL)
- Cholesterol: {patient.cholesterol} mg/dL (Normal: <200 mg/dL)

Provide a short clinical risk summary only."""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            data = resp.json()
            if resp.status_code == 200:
                return data["content"][0]["text"].strip()
            else:
                return generate_rule_based_remarks(patient)
    except Exception:
        return generate_rule_based_remarks(patient)


def calculate_age(dob_str: str) -> int:
    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def generate_rule_based_remarks(patient: PatientCreate) -> str:
    """Fallback rule-based health risk assessment."""
    flags = []
    if patient.glucose > 126:
        flags.append("High glucose levels may indicate diabetes risk")
    elif patient.glucose > 100:
        flags.append("Borderline glucose — possible pre-diabetic range")
    if patient.haemoglobin < 12:
        flags.append("Low haemoglobin suggests possible anaemia")
    elif patient.haemoglobin > 17.5:
        flags.append("Elevated haemoglobin — consider further evaluation")
    if patient.cholesterol > 240:
        flags.append("High cholesterol — cardiovascular risk elevated")
    elif patient.cholesterol > 200:
        flags.append("Borderline cholesterol — lifestyle modifications advised")

    if not flags:
        return "All key blood markers appear within normal reference ranges. Continue regular health monitoring."
    return ". ".join(flags) + ". Please consult a qualified healthcare professional for a full evaluation."


# ── CRUD Endpoints ──────────────────────────────────────────────────────────────
@app.post("/api/patients", response_model=PatientResponse, status_code=201)
async def create_patient(patient: PatientCreate):
    remarks = await get_ai_health_prediction(patient)
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO patients (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (patient.full_name, patient.dob, patient.email,
             patient.glucose, patient.haemoglobin, patient.cholesterol, remarks)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


@app.get("/api/patients", response_model=list[PatientResponse])
def list_patients():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM patients ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return dict(row)


@app.put("/api/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: int, patient: PatientUpdate):
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Patient not found")
        remarks = await get_ai_health_prediction(patient)
        conn.execute(
            """UPDATE patients SET full_name=?, dob=?, email=?, glucose=?, haemoglobin=?,
               cholesterol=?, remarks=? WHERE id=?""",
            (patient.full_name, patient.dob, patient.email,
             patient.glucose, patient.haemoglobin, patient.cholesterol, remarks, patient_id)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    return dict(row)


@app.delete("/api/patients/{patient_id}")
def delete_patient(patient_id: int):
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Patient not found")
        conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
    return {"message": "Patient deleted successfully"}


# ── Serve Frontend ──────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")
