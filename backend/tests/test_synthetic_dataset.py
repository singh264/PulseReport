import numpy as np

from pulse_report.ml.synthetic import SyntheticTriageDatasetGenerator


def test_synthetic_dataset_shapes_and_reproducibility():
    gen = SyntheticTriageDatasetGenerator()

    ds1 = gen.generate(n=200, seed=123)
    ds2 = gen.generate(n=200, seed=123)

    assert ds1.X.shape[0] == 200
    assert ds1.y.shape == (200,)
    assert ds1.X.shape[1] == len(ds1.feature_names)

    # deterministic with same seed
    assert np.allclose(ds1.X[0], ds2.X[0])
    assert ds1.y[0] == ds2.y[0]

    # labels are 0/1
    assert set(np.unique(ds1.y)).issubset({0.0, 1.0})
