from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from pulse_report.ml.logreg import LogisticRegressionGD
from pulse_report.ml.metrics import accuracy
from pulse_report.ml.synthetic import SyntheticTriageDatasetGenerator


def main() -> None:
    gen = SyntheticTriageDatasetGenerator()
    ds = gen.generate(n=5000, seed=42)

    # train/test split
    n = ds.X.shape[0]
    split = int(0.8 * n)
    X_train, X_test = ds.X[:split], ds.X[split:]
    y_train, y_test = ds.y[:split], ds.y[split:]

    model = LogisticRegressionGD(learning_rate=0.3, epochs=300, l2=1e-4, standardize=True)
    model.fit(X_train, y_train)

    train_acc = accuracy(y_train, model.predict(X_train))
    test_acc = accuracy(y_test, model.predict(X_test))

    print(f"Train acc: {train_acc:.3f}")
    print(f"Test  acc: {test_acc:.3f}")
    print(f"Loss start/end: {model.loss_history[0]:.4f} -> {model.loss_history[-1]:.4f}")

    out_dir = Path("models")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "triage_logreg.json"

    payload = {
        "model_type": "logreg_gd",
        "feature_names": ds.feature_names,
        "weights": model.weights.tolist() if model.weights is not None else None,
        "bias": model.bias,
        "mean": model.mean_.tolist() if model.mean_ is not None else None,
        "std": model.std_.tolist() if model.std_ is not None else None,
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
    }

    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Saved model: {out_path}")


if __name__ == "__main__":
    main()
