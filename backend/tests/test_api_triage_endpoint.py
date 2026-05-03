import json
from datetime import date

from fastapi.testclient import TestClient

from pulse_report.api.app import create_app
from pulse_report.app.repository import InMemoryPcrRepository


def _write_test_model(path):
    feature_names = [
        "age_years",
        "pulse_bpm",
        "resp_per_min",
        "systolic_bp",
        "diastolic_bp",
        "pain_0_to_10",
        "loc_alert",
        "intervention_oxygen",
        "intervention_iv",
        "chief_respiratory",
        "chief_cardiac",
        "chief_trauma",
        "chief_neuro",
        "chief_other",
    ]

    weights = [0.0] * len(feature_names)
    weights[feature_names.index("pulse_bpm")] = 0.05

    payload = {
        "model_type": "logreg_gd",
        "feature_names": feature_names,
        "weights": weights,
        "bias": -5.0,
        "mean": [0.0] * len(feature_names),
        "std": [1.0] * len(feature_names),
        "train_accuracy": 1.0,
        "test_accuracy": 1.0,
    }
    path.write_text(json.dumps(payload))


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
        "history_description": "Chest pain after exertion.",
        "initial_vitals": [
            {
                "observed_at": "2026-01-02T10:15:00",
                "pulse_bpm": 200,
                "resp_per_min": 18,
                "systolic_bp": 124,
                "diastolic_bp": 78,
                "skin": "Warm, dry",
                "loc": "Alert",
                "pain_0_to_10": 4,
                "pupils": {"left_reactive": True, "right_reactive": True},
            }
        ],
        "treatments": [],
        "disposition": None,
    }
    res = client.post("/pcr", json=payload)
    assert res.status_code == 201, res.text
    return res.json()["pcr_id"]


def test_get_triage_returns_score_label_and_explanation(tmp_path):
    model_path = tmp_path / "triage.json"
    _write_test_model(model_path)

    repo = InMemoryPcrRepository()
    app = create_app(repo=repo, triage_model_path=str(model_path))
    client = TestClient(app)

    pcr_id = _create_pcr(client)

    res = client.get(f"/pcr/{pcr_id}/triage")
    assert res.status_code == 200, res.text

    body = res.json()
    assert body["pcr_id"] == pcr_id
    assert 0.0 <= body["risk_score"] <= 1.0
    assert body["risk_score"] > 0.9
    assert body["label"] in ("Urgent transport", "Not urgent")
    assert isinstance(body["top_contributions"], list) and len(body["top_contributions"]) > 0
    assert any(item["name"] == "pulse_bpm" for item in body["top_contributions"])


def test_get_triage_unknown_pcr_returns_404(tmp_path):
    model_path = tmp_path / "triage.json"
    _write_test_model(model_path)

    repo = InMemoryPcrRepository()
    app = create_app(repo=repo, triage_model_path=str(model_path))
    client = TestClient(app)

    res = client.get("/pcr/not-a-real-id/triage")
    assert res.status_code == 404
