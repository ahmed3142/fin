"""Analysis math tests: the numpy OLS/HC3 helper and Spearman."""
import numpy as np

from src.analysis import _ols, _spearman


def test_ols_recovers_known_slope():
    rng = np.random.RandomState(0)
    x = np.linspace(0, 1, 200)
    y = 3.0 + 2.0 * x + rng.normal(0, 0.01, size=x.size)
    fit = _ols(x, y)
    assert abs(fit["slope"] - 2.0) < 0.05
    assert fit["r2"] > 0.99
    assert fit["se"] > 0


def test_spearman_monotonic_is_one():
    a = np.arange(20.0)
    b = a ** 2  # monotonic transform -> rank correlation 1
    assert abs(_spearman(a, b) - 1.0) < 1e-9


def test_spearman_reversed_is_minus_one():
    a = np.arange(20.0)
    assert abs(_spearman(a, a[::-1]) + 1.0) < 1e-9
