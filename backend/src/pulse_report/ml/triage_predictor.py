from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from pulse_report.ml.model_io import LogRegArtifact


def _sigmoid(z: float) -> float:
    z = float(np.clip(z, -30.0, 30.0))
    return float(1.0 / (1.0 + np.exp(-z)))


@dataclass(frozen=True)
class TriageLogRegPredictor:
    artifact: LogRegArtifact

    def predict_proba(self, features: dict[str, float]) -> float:
        x_raw = self._vectorize(features)
        x_std = (x_raw - self.artifact.mean) / self.artifact.std
        logit = float(x_std @ self.artifact.weights + self.artifact.bias)
        return _sigmoid(logit)

    def explain(self, features: dict[str, float], top_k: int = 5) -> list[dict[str, Any]]:
        x_raw = self._vectorize(features)
        x_std = (x_raw - self.artifact.mean) / self.artifact.std

        contrib = x_std * self.artifact.weights
        order = np.argsort(np.abs(contrib))[::-1]

        out: list[dict[str, Any]] = []
        for idx in order[: max(1, top_k)]:
            out.append(
                {
                    "name": self.artifact.feature_names[int(idx)],
                    "raw_value": float(x_raw[int(idx)]),
                    "standardized_value": float(x_std[int(idx)]),
                    "weight": float(self.artifact.weights[int(idx)]),
                    "contribution": float(contrib[int(idx)]),
                }
            )
        return out

    def _vectorize(self, features: dict[str, float]) -> np.ndarray:
        vals = [float(features.get(name, 0.0)) for name in self.artifact.feature_names]
        return np.asarray(vals, dtype=float)
