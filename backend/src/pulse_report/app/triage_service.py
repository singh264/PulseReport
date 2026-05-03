from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from pulse_report.app.repository import PcrRepository
from pulse_report.domain.pcr import LocLevel
from pulse_report.ml.model_io import load_logreg_artifact
from pulse_report.ml.triage_predictor import TriageLogRegPredictor


@dataclass(frozen=True)
class TriageResult:
    pcr_id: str
    risk_score: float
    label: str
    top_contributions: list[dict]


@dataclass
class TriageService:
    repo: PcrRepository
    predictor: TriageLogRegPredictor

    @classmethod
    def default(cls, repo: PcrRepository, *, model_path: str) -> "TriageService":
        artifact = load_logreg_artifact(model_path)
        return cls(repo=repo, predictor=TriageLogRegPredictor(artifact))

    def predict_for_pcr(self, pcr_id: str, *, top_k: int = 5) -> TriageResult:
        pcr = self.repo.get(pcr_id)
        if pcr is None:
            raise KeyError(f"PCR not found: {pcr_id}")

        features = self._extract_features(pcr)
        p = self.predictor.predict_proba(features)
        label = "Urgent transport" if p >= 0.5 else "Not urgent"
        top = self.predictor.explain(features, top_k=top_k)

        return TriageResult(pcr_id=pcr_id, risk_score=p, label=label, top_contributions=top)

    @staticmethod
    def _extract_features(pcr) -> dict[str, float]:
        # age in years from report_date to avoid timezone issues
        age_years = _age_years(pcr.patient.date_of_birth, pcr.report_date)

        # use latest vitals by timestamp (safe even if list not sorted)
        latest = max(pcr.initial_vitals, key=lambda v: v.observed_at)

        pulse = float(latest.pulse_bpm)
        resp = float(latest.resp_per_min)
        sys = float(latest.systolic_bp)
        dia = float(latest.diastolic_bp)
        pain = float(latest.pain_0_to_10)
        loc_alert = 1.0 if latest.loc == LocLevel.ALERT else 0.0

        # interventions (from treatments list)
        tx_lower = " | ".join(t.intervention.lower() for t in pcr.treatments)
        oxygen = 1.0 if "oxygen" in tx_lower or "o2" in tx_lower else 0.0
        iv = 1.0 if (" iv" in f" {tx_lower}" or "intravenous" in tx_lower) else 0.0

        chief = _chief_from_history(pcr.history_description)

        features = {
            "age_years": age_years,
            "pulse_bpm": pulse,
            "resp_per_min": resp,
            "systolic_bp": sys,
            "diastolic_bp": dia,
            "pain_0_to_10": pain,
            "loc_alert": loc_alert,
            "intervention_oxygen": oxygen,
            "intervention_iv": iv,
            "chief_respiratory": 1.0 if chief == "respiratory" else 0.0,
            "chief_cardiac": 1.0 if chief == "cardiac" else 0.0,
            "chief_trauma": 1.0 if chief == "trauma" else 0.0,
            "chief_neuro": 1.0 if chief == "neuro" else 0.0,
            "chief_other": 1.0 if chief == "other" else 0.0,
        }
        return features


def _age_years(dob: date, on_date: date) -> float:
    days = (on_date - dob).days
    return float(max(0, days) / 365.25)


def _chief_from_history(text: str) -> str:
    t = (text or "").lower()

    respiratory_kw = ["shortness of breath", "sob", "dyspnea", "wheeze", "asthma"]
    cardiac_kw = ["chest pain", "palpitation", "cardiac", "heart"]
    trauma_kw = ["fall", "injury", "ankle", "fracture", "bleed", "laceration", "sprain"]
    neuro_kw = ["seizure", "stroke", "weakness", "confusion", "syncope", "faint"]

    if any(k in t for k in respiratory_kw):
        return "respiratory"
    if any(k in t for k in cardiac_kw):
        return "cardiac"
    if any(k in t for k in trauma_kw):
        return "trauma"
    if any(k in t for k in neuro_kw):
        return "neuro"
    return "other"
