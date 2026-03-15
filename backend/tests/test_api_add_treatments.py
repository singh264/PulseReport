from fastapi.testclient import TestClient

from pulse_report.api.app import create_app
from pulse_report.app.repository import InMemoryPcrRepository


def _create_pcr(client: TestClient) -> str:
    payload = {
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
    res = client.post("/pcr", json=payload)
    assert res.status_code == 201, res.text
    return res.json()["pcr_id"]


def test_post_treatments_appends_entry_and_returns_updated_pcr():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    pcr_id = _create_pcr(client)

    treatment_payload = {
        "performed_at": "2026-01-02T10:20:00",
        "intervention": "Oxygen",
        "results_notes": "Improved symptoms subjectively",
    }

    res = client.post(f"/pcr/{pcr_id}/treatments", json=treatment_payload)
    assert res.status_code == 200, res.text
    body = res.json()

    assert body["pcr_id"] == pcr_id
    assert len(body["treatments"]) == 1
    assert body["treatments"][0]["performed_at"] == "2026-01-02T10:20:00"
    assert body["treatments"][0]["intervention"] == "Oxygen"


def test_post_treatments_rejects_empty_intervention():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    pcr_id = _create_pcr(client)

    bad_payload = {
        "performed_at": "2026-01-02T10:20:00",
        "intervention": "   ",
        "results_notes": "",
    }

    res = client.post(f"/pcr/{pcr_id}/treatments", json=bad_payload)
    assert res.status_code == 400, res.text
