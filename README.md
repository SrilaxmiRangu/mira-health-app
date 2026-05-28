# MIRA — Medical Intelligence Robotic Automation
### Health Prediction Application · Task 1 Submission

A full-stack health prediction web application built with **FastAPI** (Python) + **HTML/CSS/JS** frontend + **SQLite** database, integrated with the **Anthropic Claude AI API** for intelligent patient health risk assessment.

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| **Backend** | FastAPI (Python) | Fast, modern REST API framework with automatic docs; ideal for AI/ML integration |
| **Frontend** | Vanilla HTML/CSS/JS | Zero build-step, fully responsive, clean clinical UI with no framework overhead |
| **Database** | SQLite (via `sqlite3`) | Lightweight persistent storage, zero-config, file-based — perfect for this scope |
| **AI/ML API** | Anthropic Claude API | State-of-the-art LLM for contextual health risk summarisation from blood markers |
| **Validation** | Pydantic v2 | Schema-level validation on the backend; mirrored on the frontend for UX |

---

## Features

- ✅ **Full CRUD** — Create, Read, Update, Delete patient records
- ✅ **AI Health Prediction** — Claude API analyses Glucose, Haemoglobin & Cholesterol values and generates a plain-English clinical risk summary in the **Remarks** field
- ✅ **Rule-based Fallback** — If the API key is absent, a deterministic rule-based engine generates remarks based on clinical reference ranges (no silent failures)
- ✅ **Data Validation** — Email format, DOB cannot be future, blood values must be positive numerics — enforced on both frontend and backend
- ✅ **Persistent SQLite Storage** — Auto-created `mira.db` on first run
- ✅ **Risk Stratification** — Records auto-tagged HIGH RISK / MODERATE / NORMAL based on reference ranges
- ✅ **Live Search** — Filter patient table by name or email instantly

---

## Setup & Run

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/mira-health-app.git
cd mira-health-app
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Open .env and add your Anthropic API key
```

Get a free API key at: https://console.anthropic.com

> **Note:** The app works without an API key using its built-in rule-based health engine.

### 5. Run the server
```bash
uvicorn main:app --reload
```

Open your browser at: **http://localhost:8000**

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/patients` | List all patient records |
| `POST` | `/api/patients` | Create new patient + AI remarks |
| `GET` | `/api/patients/{id}` | Get single patient |
| `PUT` | `/api/patients/{id}` | Update patient + regenerate AI remarks |
| `DELETE` | `/api/patients/{id}` | Delete patient record |

Interactive API docs available at: **http://localhost:8000/docs**

---

## Blood Test Reference Ranges

| Marker | Normal Range | Source |
|---|---|---|
| Glucose | 70 – 99 mg/dL (fasting) | ADA Guidelines |
| Haemoglobin | 12.1–15.1 g/dL (F), 13.8–17.2 g/dL (M) | WHO |
| Cholesterol | < 200 mg/dL | ACC/AHA |

---

## Project Structure

```
mira-health-app/
├── main.py              # FastAPI backend — routes, DB, AI integration
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template (no secrets)
├── .gitignore
├── README.md
└── static/
    └── index.html       # Single-page frontend (HTML/CSS/JS)
```

---

## Challenges & Design Decisions

1. **AI Fallback Strategy** — The app needed to function even without an API key. A clinically-informed rule-based engine mirrors the AI's decision logic, ensuring the app is never broken.

2. **Single-file Frontend** — Keeping HTML, CSS, and JS in one file removes build complexity while keeping the code readable and easy to demo.

3. **Async AI Calls** — Used `async/await` with `httpx` so the FastAPI server never blocks while waiting for the AI API response.

4. **Security** — API keys are loaded from environment variables; `.env` is gitignored; `.env.example` is the only file committed.

---

## Disclaimer

This application is a **technical demonstration only** and is **not a medical device**. AI-generated remarks are for educational/assessment purposes and must not be used for clinical decision-making. Always consult a qualified healthcare professional.
