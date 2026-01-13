from fastapi.testclient import TestClient

from pulse_report.api.app import create_app
from pulse_report.app.repository import InMemoryPcrRepository


def test_get_quality_report_returns_expected_issue_codes():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

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
                "observed_at": "2026-01-02T10:30:00",
                "pulse_bpm": 300,  # implausible but domain-valid
                "resp_per_min": 18,
                "systolic_bp": 124,
                "diastolic_bp": 78,
                "skin": "Warm, dry",
                "loc": "Alert",
                "pain_0_to_10": 2,
                "pupils": {"left_reactive": True, "right_reactive": True},
            },
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
            },
        ],
        "treatments": [],
        "disposition": {
            "discharge_time": "11:00:00",
            "disposition": "Home",
            "accompanied_by": "Self",
            "discharge_instructions": "",
        },
    }

    post_res = client.post("/pcr", json=payload)
    assert post_res.status_code == 201, post_res.text
    pcr_id = post_res.json()["pcr_id"]

    q_res = client.get(f"/pcr/{pcr_id}/quality")
    assert q_res.status_code == 200, q_res.text

    body = q_res.json()
    assert body["pcr_id"] == pcr_id
    codes = {i["code"] for i in body["issues"]}

    assert "DISPOSITION_MISSING_INSTRUCTIONS" in codes
    assert "VITALS_OUT_OF_ORDER" in codes
    assert "VITALS_IMPLAUSIBLE_PULSE" in codes


def test_get_quality_unknown_pcr_returns_404():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    res = client.get("/pcr/not-a-real-id/quality")
    assert res.status_code == 404

