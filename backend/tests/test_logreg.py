import numpy as np

from pulse_report.ml.logreg import LogisticRegressionGD
from pulse_report.ml.metrics import accuracy


def test_logreg_fit_decreases_loss_and_learns_linearly_separable_boundary():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(600, 2))
    y = (X[:, 0] + X[:, 1] > 0).astype(float)

    model = LogisticRegressionGD(learning_rate=0.5, epochs=200, l2=0.0, standardize=True)
    model.fit(X, y)

    assert model.loss_history[0] > model.loss_history[-1]

    preds = model.predict(X)
    assert accuracy(y, preds) > 0.90


def test_predict_proba_in_range():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(50, 3))
    y = (X[:, 0] > 0).astype(float)

    model = LogisticRegressionGD(learning_rate=0.3, epochs=50, l2=0.0, standardize=True).fit(X, y)
    p = model.predict_proba(X)

    assert np.all(p >= 0.0)
    assert np.all(p <= 1.0)
