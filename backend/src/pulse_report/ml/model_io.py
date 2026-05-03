from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class LogRegArtifact:
    model_type: str
    feature_names: list[str]
    weights: np.ndarray
    bias: float
    mean: np.ndarray
    std: np.ndarray


def load_logreg_artifact(path: str) -> LogRegArtifact:
    data = json.loads(Path(path).read_text())

    feature_names = list(data["feature_names"])
    weights = np.asarray(data["weights"], dtype=float)
    mean = np.asarray(data["mean"], dtype=float)
    std = np.asarray(data["std"], dtype=float)

    if len(feature_names) == 0:
        raise ValueError("Artifact feature_names must not be empty.")
    if weights.shape[0] != len(feature_names):
        raise ValueError("Artifact weights length mismatch.")
    if mean.shape[0] != len(feature_names) or std.shape[0] != len(feature_names):
        raise ValueError("Artifact mean/std length mismatch.")
    if np.any(std == 0.0):
        raise ValueError("Artifact std contains zeros.")

    return LogRegArtifact(
        model_type=str(data.get("model_type", "logreg_gd")),
        feature_names=feature_names,
        weights=weights,
        bias=float(data["bias"]),
        mean=mean,
        std=std,
    )
