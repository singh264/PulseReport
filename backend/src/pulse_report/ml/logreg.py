from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


def _sigmoid(z: np.ndarray) -> np.ndarray:
    # numerically stable sigmoid
    z = np.clip(z, -30, 30)
    return 1.0 / (1.0 + np.exp(-z))


@dataclass
class LogisticRegressionGD:
    learning_rate: float = 0.3
    epochs: int = 200
    l2: float = 0.0
    standardize: bool = True

    weights: Optional[np.ndarray] = None
    bias: float = 0.0
    mean_: Optional[np.ndarray] = None
    std_: Optional[np.ndarray] = None
    loss_history: list[float] = field(default_factory=list)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticRegressionGD":
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)

        if X.ndim != 2:
            raise ValueError("X must be 2D")
        if y.ndim != 1 or y.shape[0] != X.shape[0]:
            raise ValueError("y must be 1D with same number of rows as X")

        Xs = self._standardize_fit_transform(X) if self.standardize else X

        n, d = Xs.shape
        self.weights = np.zeros(d, dtype=float)
        self.bias = 0.0
        self.loss_history = []

        eps = 1e-12

        for _ in range(self.epochs):
            z = Xs @ self.weights + self.bias
            p = _sigmoid(z)

            # gradients
            err = (p - y)
            grad_w = (Xs.T @ err) / n + self.l2 * self.weights
            grad_b = float(err.mean())

            # step
            self.weights -= self.learning_rate * grad_w
            self.bias -= self.learning_rate * grad_b

            # loss
            ce = -np.mean(y * np.log(p + eps) + (1.0 - y) * np.log(1.0 - p + eps))
            reg = 0.5 * self.l2 * float(np.sum(self.weights * self.weights))
            self.loss_history.append(float(ce + reg))

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self._require_fitted()
        X = np.asarray(X, dtype=float)
        Xs = self._standardize_transform(X) if self.standardize else X
        return _sigmoid(Xs @ self.weights + self.bias)

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        p = self.predict_proba(X)
        return (p >= threshold).astype(float)

    def _require_fitted(self) -> None:
        if self.weights is None:
            raise ValueError("Model is not fitted yet.")

    def _standardize_fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0)
        self.std_ = np.where(self.std_ == 0.0, 1.0, self.std_)
        return (X - self.mean_) / self.std_

    def _standardize_transform(self, X: np.ndarray) -> np.ndarray:
        if self.mean_ is None or self.std_ is None:
            raise ValueError("Standardization parameters not set.")
        return (X - self.mean_) / self.std_
