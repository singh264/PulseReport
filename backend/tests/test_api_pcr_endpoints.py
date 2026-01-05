from datetime import date, datetime, time

from fastapi.testclient import TestClient

from pulse_report.api.app import create_app
from pulse_report.app.repository import InMemoryPcrRepository


def test_post_pcr_returns_id_and_can_get_it_back():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    payload = {
        "event_name": "Community Event",
        "report_date": "2026-01-02",
        "report_time": "10:30:00",
        "patient": {
            "full_name": "Jane Doe",
            "date_of_birth": "2000-01-15",
            "sex": "Female",
            "phone": "555-123-4567",
        },
        "consent": "Given",
        "history_description": "Felt dizzy after standing up quickly.",
        "initial_vitals": [
            {
                "observed_at": "2026-01-02T10:15:00",
                "pulse_bpm": 92,
                "resp_per_min": 18,
                "systolic_bp": 124,
                "diastolic_bp": 78,
                "skin": "Warm, dry",
                "loc": "Alert",
                "pain_0_to_10": 2,
                "pupils": {"left_reactive": True, "right_reactive": True},
            }
        ],
        "treatments": [],
        "disposition": None,
    }

    post_res = client.post("/pcr", json=payload)
    assert post_res.status_code == 201, post_res.text
    pcr_id = post_res.json()["pcr_id"]
    assert isinstance(pcr_id, str) and len(pcr_id) > 0

    get_res = client.get(f"/pcr/{pcr_id}")
    assert get_res.status_code == 200, get_res.text
    body = get_res.json()
    assert body["pcr_id"] == pcr_id
    assert body["patient"]["full_name"] == "Jane Doe"
    assert body["event_name"] == "Community Event"


def test_get_summary_returns_text_plain():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    payload = {
        "event_name": "Watch Party",
        "report_date": "2026-01-02",
        "report_time": "09:20:00",
        "patient": {
            "full_name": "John Smith",
            "date_of_birth": "1995-06-01",
            "sex": "Male",
            "phone": "555-000-0000",
        },
        "consent": "Refused",
        "history_description": "Twisted ankle; swelling present.",
        "initial_vitals": [
            {
                "observed_at": "2026-01-02T09:05:00",
                "pulse_bpm": 110,
                "resp_per_min": 22,
                "systolic_bp": 140,
                "diastolic_bp": 90,
                "skin": "Pale",
                "loc": "Verbal",
                "pain_0_to_10": 6,
                "pupils": {"left_reactive": True, "right_reactive": False},
            }
        ],
        "treatments": [],
        "disposition": None,
    }

    post_res = client.post("/pcr", json=payload)
    pcr_id = post_res.json()["pcr_id"]

    sum_res = client.get(f"/pcr/{pcr_id}/summary")
    assert sum_res.status_code == 200
    assert sum_res.headers["content-type"].startswith("text/plain")
    assert "Event:" in sum_res.text
    assert "Initial Vitals:" in sum_res.text
    assert "Disposition:" in sum_res.text


def test_post_pcr_domain_validation_error_returns_422():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    bad_payload = {
        "event_name": "Test",
        "report_date": "2026-01-02",
        "report_time": "12:05:00",
        "patient": {
            "full_name": "Invalid Pain",
            "date_of_birth": "2001-01-01",
            "sex": "Other",
            "phone": "555",
        },
        "consent": "Given",
        "history_description": "N/A",
        "initial_vitals": [
            {
                "observed_at": "2026-01-02T12:00:00",
                "pulse_bpm": 80,
                "resp_per_min": 16,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "skin": "Normal",
                "loc": "Alert",
                "pain_0_to_10": 11,  # invalid
                "pupils": {"left_reactive": True, "right_reactive": True},
            }
        ],
        "treatments": [],
        "disposition": None,
    }

    res = client.post("/pcr", json=bad_payload)
    assert res.status_code == 422
    detail = res.json()["detail"]
    assert isinstance(detail, list)
    
    # Each item is like: {"loc": [...], "msg": "...", "type": "..."}
    assert any(
        "pain_0_to_10" in [str(x) for x in err.get("loc", [])]
        for err in detail
    )

