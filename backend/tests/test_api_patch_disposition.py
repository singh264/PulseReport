from fastapi.testclient import TestClient

from pulse_report.api.app import create_app
from pulse_report.app.repository import InMemoryPcrRepository


def test_patch_disposition_updates_instructions_and_clears_quality_flag():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    # Create PCR with disposition but missing instructions (should trigger quality issue)
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
        "disposition": {
            "discharge_time": "11:00:00",
            "disposition": "Home",
            "accompanied_by": "Self",
            "discharge_instructions": "",
        },
    }

    post_res = client.post("/pcr", json=create_payload)
    assert post_res.status_code == 201, post_res.text
    pcr_id = post_res.json()["pcr_id"]

    # Confirm quality currently flags missing instructions
    q1 = client.get(f"/pcr/{pcr_id}/quality")
    assert q1.status_code == 200, q1.text
    codes1 = {i["code"] for i in q1.json()["issues"]}
    assert "DISPOSITION_MISSING_INSTRUCTIONS" in codes1

    # Patch discharge instructions
    patch_res = client.patch(
        f"/pcr/{pcr_id}/disposition",
        json={"discharge_instructions": "Hydrate, rest, return if symptoms worsen."},
    )
    assert patch_res.status_code == 200, patch_res.text
    body = patch_res.json()
    assert body["pcr_id"] == pcr_id
    assert body["disposition"]["discharge_instructions"] == "Hydrate, rest, return if symptoms worsen."

    # Quality should no longer flag missing instructions
    q2 = client.get(f"/pcr/{pcr_id}/quality")
    assert q2.status_code == 200, q2.text
    codes2 = {i["code"] for i in q2.json()["issues"]}
    assert "DISPOSITION_MISSING_INSTRUCTIONS" not in codes2


def test_patch_disposition_requires_core_fields_if_disposition_missing():
    repo = InMemoryPcrRepository()
    app = create_app(repo=repo)
    client = TestClient(app)

    # Create PCR with NO disposition
    create_payload = {
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

    post_res = client.post("/pcr", json=create_payload)
    assert post_res.status_code == 201, post_res.text
    pcr_id = post_res.json()["pcr_id"]

    # Trying to patch only instructions when no disposition exists -> 400
    patch_res = client.patch(
        f"/pcr/{pcr_id}/disposition",
        json={"discharge_instructions": "Rest and follow up if worse."},
    )
    assert patch_res.status_code == 400, patch_res.text

