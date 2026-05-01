from __future__ import annotations

from dataclasses import dataclass
from typing import List
import random

import numpy as np


_COMPLAINTS = ["respiratory", "cardiac", "trauma", "neuro", "other"]


@dataclass(frozen=True)
class SyntheticDataset:
    X: np.ndarray
    y: np.ndarray
    feature_names: List[str]


class SyntheticTriageDatasetGenerator:
    """
    Generates structured-only EMS-style records + a simple "urgent transport" label.

    Goals:
    - deterministic with seed
    - non-diagnostic (rule label is just a proxy)
    """

    feature_names: List[str] = [
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

    def generate(self, *, n: int, seed: int = 0) -> SyntheticDataset:
        if n < 1:
            raise ValueError("n must be >= 1")

        rng = random.Random(seed)
        X = np.zeros((n, len(self.feature_names)), dtype=float)
        y = np.zeros((n,), dtype=float)

        for i in range(n):
            age = rng.randint(0, 90)
            complaint = rng.choices(_COMPLAINTS, weights=[0.22, 0.18, 0.22, 0.13, 0.25], k=1)[0]

            # base vitals
            pulse = int(rng.gauss(85, 18))
            resp = int(rng.gauss(16, 4))
            sys = int(rng.gauss(125, 18))
            dia = int(rng.gauss(78, 12))
            pain = int(min(10, max(0, round(rng.gauss(3.5, 2.5)))))

            # complaint adjustments
            if complaint == "respiratory":
                resp += rng.randint(0, 12)
            elif complaint == "cardiac":
                pulse += rng.randint(0, 25)
            elif complaint == "trauma":
                pain += rng.randint(0, 4)
            elif complaint == "neuro":
                # slightly more altered LOC
                pass

            pulse = int(max(30, min(220, pulse)))
            resp = int(max(6, min(60, resp)))
            sys = int(max(70, min(220, sys)))
            dia = int(max(30, min(140, dia)))

            loc_alert = 1.0
            if complaint == "neuro" and rng.random() < 0.18:
                loc_alert = 0.0
            if sys < 90 and rng.random() < 0.25:
                loc_alert = 0.0

            urgent = self._urgent_label(
                pulse=pulse,
                resp=resp,
                sys=sys,
                loc_alert=loc_alert,
                complaint=complaint,
            )

            # interventions (proxy patterns)
            oxygen = 1.0 if (complaint in ("respiratory", "cardiac") and (urgent or resp > 22)) else 0.0
            iv = 1.0 if (urgent and (sys < 95 or complaint == "cardiac")) else 0.0

            # one-hot complaint
            one_hot = {c: 0.0 for c in _COMPLAINTS}
            one_hot[complaint] = 1.0

            row = [
                float(age),
                float(pulse),
                float(resp),
                float(sys),
                float(dia),
                float(pain),
                float(loc_alert),
                float(oxygen),
                float(iv),
                one_hot["respiratory"],
                one_hot["cardiac"],
                one_hot["trauma"],
                one_hot["neuro"],
                one_hot["other"],
            ]

            X[i, :] = np.array(row, dtype=float)
            y[i] = 1.0 if urgent else 0.0

        return SyntheticDataset(X=X, y=y, feature_names=list(self.feature_names))

    @staticmethod
    def _urgent_label(*, pulse: int, resp: int, sys: int, loc_alert: float, complaint: str) -> bool:
        # simple, intentionally non-diagnostic proxy label
        if sys < 90:
            return True
        if pulse > 130 or pulse < 45:
            return True
        if resp > 30 or resp < 8:
            return True
        if loc_alert < 0.5:
            return True
        if complaint == "cardiac" and pulse > 110:
            return True
        return False
