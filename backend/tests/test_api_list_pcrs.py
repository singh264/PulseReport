from fastapi.testclient import TestClient

from pulse_report.api.app import create_app
from pulse_report.app.repository import InMemoryPcrRepository


def _create_pcr(client: TestClient, *, event_name: str, report_time: str) -> str:
    payload = {
        "event_name": event_name,
        "report_date": "2026-01-02",
        "report_time": report_time,
        "patient": {
            "full_name": "Jane Doe",
            "date_of_birth": "2000-01-15",
            "sex": "Female",
            "phone": "555-123-4567",
        },
        "consent": "Given",
        "history_description": "Test history",
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


def test_list_pcrs_returns_items_sorted_newest_first():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    id_old = _create_pcr(client, event_name="Older Event", report_time="09:00:00")
    id_new = _create_pcr(client, event_name="Newer Event", report_time="11:00:00")

    res = client.get("/pcr")
    assert res.status_code == 200, res.text

    body = res.json()
    assert "items" in body
    assert len(body["items"]) >= 2

    # newest first (11:00 before 09:00)
    assert body["items"][0]["pcr_id"] == id_new
    assert body["items"][1]["pcr_id"] == id_old

    first = body["items"][0]
    assert first["event_name"] == "Newer Event"
    assert first["patient_full_name"] == "Jane Doe"
    assert first["has_disposition"] is False


def test_list_pcrs_applies_limit_and_offset():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    _create_pcr(client, event_name="E1", report_time="08:00:00")
    id2 = _create_pcr(client, event_name="E2", report_time="09:00:00")
    id3 = _create_pcr(client, event_name="E3", report_time="10:00:00")

    # Sorted newest first: E3, E2, E1
    res = client.get("/pcr?limit=1&offset=0")
    assert res.status_code == 200
    assert res.json()["items"][0]["pcr_id"] == id3

    res = client.get("/pcr?limit=1&offset=1")
    assert res.status_code == 200
    assert res.json()["items"][0]["pcr_id"] == id2

