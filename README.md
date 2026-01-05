# Pulse Report

A lightweight EMS-style electronic Patient Care Record (ePCR) prototype with:
- **Validated PCR domain model** (patient info, vitals, treatments, disposition)
- **Service + repository layer** for creating/retrieving PCRs
- **Plain-text summary exporter**
- **FastAPI API** to create, fetch, and export summaries
- **Pytest + GitHub Actions CI** baseline (TDD-first)

> Scope is intentionally **non-diagnostic** (triage + documentation quality later).

## Tech
- Python 3.11+
- FastAPI + Uvicorn
- Pytest (+ coverage)
- In-memory repository (Postgres repository will come later)

## Repo layout
```
backend/
  pyproject.toml
  src/pulse_report/
    domain/        # entities + invariants
    app/           # service + repository interfaces/impl
    api/           # FastAPI app + request/response schemas
    scripts/       # manual demos
  tests/
.github/workflows/ci.yml
```

## Quickstart (local)
From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -e ".[dev]"
pytest
```

## Run the API
From `backend/`:

```bash
uvicorn pulse_report.api.app:app --reload --port 8000
```

Open:
- Swagger UI: `http://127.0.0.1:8000/docs`

### Endpoints
- `POST /pcr` → create a PCR (returns `{ "pcr_id": "..." }`)
- `GET /pcr/{pcr_id}` → fetch PCR JSON
- `GET /pcr/{pcr_id}/summary` → plain-text summary

### Example (curl)
Create:
```bash
curl -s -X POST http://127.0.0.1:8000/pcr \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Community Event",
    "report_date": "2026-01-02",
    "report_time": "10:30:00",
    "patient": { "full_name": "Jane Doe", "date_of_birth": "2000-01-15", "sex": "Female", "phone": "555-123-4567" },
    "consent": "Given",
    "history_description": "Felt dizzy after standing up quickly.",
    "initial_vitals": [{
      "observed_at": "2026-01-02T10:15:00",
      "pulse_bpm": 92,
      "resp_per_min": 18,
      "systolic_bp": 124,
      "diastolic_bp": 78,
      "skin": "Warm, dry",
      "loc": "Alert",
      "pain_0_to_10": 2,
      "pupils": { "left_reactive": true, "right_reactive": true }
    }],
    "treatments": [],
    "disposition": null
  }'
```

Summary:
```bash
curl -s http://127.0.0.1:8000/pcr/<PASTE_ID_HERE>/summary
```

## Manual demo script
```bash
python -m pulse_report.scripts.demo_create_pcr
```

## Notes
- Input enum values are **string-based** (e.g., `"Given"`, `"Refused"`, `"Alert"`, `"Verbal"`, `"Male"`, `"Female"`, `"Other"`).
- Some invalid inputs are rejected by **request schema validation** (FastAPI returns `422`).
- Domain invariants raise `DomainValidationError` and are mapped to `400` when reached in the service layer.

