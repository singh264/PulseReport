import numpy as np

from pulse_report.ml.model_io import LogRegArtifact
from pulse_report.ml.triage_predictor import TriageLogRegPredictor


def test_triage_predictor_probability_and_explanation():
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

    # Make pulse drive risk strongly
    weights = np.zeros(len(feature_names), dtype=float)
    weights[feature_names.index("pulse_bpm")] = 0.05
    artifact = LogRegArtifact(
        model_type="logreg_gd",
        feature_names=feature_names,
        weights=weights,
        bias=-5.0,
        mean=np.zeros(len(feature_names), dtype=float),
        std=np.ones(len(feature_names), dtype=float),
    )

    predictor = TriageLogRegPredictor(artifact)

    features = {name: 0.0 for name in feature_names}
    features["pulse_bpm"] = 200.0

    p = predictor.predict_proba(features)
    assert 0.0 <= p <= 1.0
    assert p > 0.9

    exp = predictor.explain(features, top_k=3)
    assert len(exp) == 3
    assert exp[0]["name"] == "pulse_bpm"
