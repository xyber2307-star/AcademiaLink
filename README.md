# AcademiaLINK Backend

Python/FastAPI backend implementing the authoritative AcademiaLINK domain layer.

## Run

```bash
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Development mode uses `X-User-Id` and `X-User-Role` headers. Production must use Firebase ID-token verification by setting `AUTH_MODE=firebase` and configuring credentials.

Firestore is selected with `DATABASE_MODE=firestore`. Business services use repository interfaces, so Firebase can be enabled without moving domain logic into route handlers.

The backend owns assessment scoring, proficiency, gap analysis, evidence verification, permissions, and opportunity matching.
