from fastapi.testclient import TestClient

from pulse_report.api.app import create_app
from pulse_report.app.repository import InMemoryPcrRepository


def test_post_vitals_appends_entry_and_returns_updated_pcr():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    create_payload = {
        "event_name": "Community Event",
        "report_date": "2026-01-02",
        "report_time": "10:45:00",
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

    post_res = client.post("/pcr", json=create_payload)
    assert post_res.status_code == 201, post_res.text
    pcr_id = post_res.json()["pcr_id"]

    add_vitals_payload = {
        "observed_at": "2026-01-02T10:30:00",
        "pulse_bpm": 88,
        "resp_per_min": 16,
        "systolic_bp": 118,
        "diastolic_bp": 76,
        "skin": "Warm",
        "loc": "Alert",
        "pain_0_to_10": 1,
        "pupils": {"left_reactive": True, "right_reactive": True},
    }

    res = client.post(f"/pcr/{pcr_id}/vitals", json=add_vitals_payload)
    assert res.status_code == 200, res.text
    body = res.json()

    assert body["pcr_id"] == pcr_id
    assert len(body["initial_vitals"]) == 2
    assert body["initial_vitals"][0]["observed_at"] == "2026-01-02T10:15:00"
    assert body["initial_vitals"][1]["observed_at"] == "2026-01-02T10:30:00"


def test_post_vitals_rejects_backdated_timestamp():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    create_payload = {
        "event_name": "Community Event",
        "report_date": "2026-01-02",
        "report_time": "10:45:00",
        "patient": {
            "full_name": "Jane Doe",
            "date_of_birth": "2000-01-15",
            "sex": "Female",
            "phone": "555-123-4567",
        },
        "consent": "Given",
        "history_description": "Test",
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

    post_res = client.post("/pcr", json=create_payload)
    assert post_res.status_code == 201, post_res.text
    pcr_id = post_res.json()["pcr_id"]

    # Back-dated vitals -> should be 400 from domain validation
    backdated = {
        "observed_at": "2026-01-02T10:10:00",
        "pulse_bpm": 90,
        "resp_per_min": 16,
        "systolic_bp": 118,
        "diastolic_bp": 76,
        "skin": "Warm",
        "loc": "Alert",
        "pain_0_to_10": 1,
        "pupils": {"left_reactive": True, "right_reactive": True},
    }

    res = client.post(f"/pcr/{pcr_id}/vitals", json=backdated)
    assert res.status_code == 400, res.text

