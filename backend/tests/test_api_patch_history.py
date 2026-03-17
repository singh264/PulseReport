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
        "history_description": "Initial short note.",
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


def test_patch_history_updates_history_description():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    pcr_id = _create_pcr(client)

    patch_res = client.patch(
        f"/pcr/{pcr_id}/history",
        json={"history_description": "Patient reports dizziness after standing; no chest pain."},
    )
    assert patch_res.status_code == 200, patch_res.text
    body = patch_res.json()
    assert body["pcr_id"] == pcr_id
    assert body["history_description"] == "Patient reports dizziness after standing; no chest pain."

    # Verify persisted via GET
    get_res = client.get(f"/pcr/{pcr_id}")
    assert get_res.status_code == 200
    assert get_res.json()["history_description"] == "Patient reports dizziness after standing; no chest pain."


def test_patch_history_rejects_blank_history_description():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    pcr_id = _create_pcr(client)

    res = client.patch(f"/pcr/{pcr_id}/history", json={"history_description": "   "})
    assert res.status_code == 400, res.text
