"""Tests for the propensity-score layer, against data with a known answer.

The headline numbers in the README are only as good as this module, and a weighting bug
silently produces a plausible-looking effect. Each test therefore checks a property the
maths guarantees, not a number copied from a run.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analysis import (
    effective_sample_size,
    fit_propensity,
    iptw_ate,
    matched_att,
    positivity,
    stabilized_weights,
    standardized_mean_difference,
)


def confounded_sample(n: int = 4000, seed: int = 0) -> pd.DataFrame:
    """x confounds: it raises the chance of treatment and the outcome.

    True ATE of T on y is exactly 2.0. The naive difference in means is biased upward,
    which is what makes this a useful correctness check.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n)
    ps = 1 / (1 + np.exp(-(0.9 * x)))
    t = rng.binomial(1, ps)
    y = 2.0 * t + 1.5 * x + rng.normal(0, 0.5, n)
    return pd.DataFrame({"x": x, "T": t, "y": y})


def test_smd_is_one_for_a_one_sd_shift_and_zero_for_identical_arms():
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {
            "T": np.r_[np.ones(500), np.zeros(500)],
            "x": np.r_[rng.normal(1, 1, 500), rng.normal(0, 1, 500)],  # one SD apart
        }
    )
    assert abs(standardized_mean_difference(df, "T", ["x"])["x"] - 1.0) < 0.1

    same = pd.DataFrame(
        {
            "T": np.r_[np.ones(4000), np.zeros(4000)],
            "x": np.r_[rng.normal(0, 1, 4000), rng.normal(0, 1, 4000)],
        }
    )
    assert abs(standardized_mean_difference(same, "T", ["x"])["x"]) < 0.1


def test_weighting_removes_the_imbalance_it_is_meant_to_remove():
    df = confounded_sample()
    before = standardized_mean_difference(df, "T", ["x"])["x"]
    ps = fit_propensity(df, "T", ["x"])
    weights = stabilized_weights(df["T"], ps)
    after = standardized_mean_difference(df, "T", ["x"], weights=weights)["x"]
    assert abs(before) > 0.5, before
    assert abs(after) < 0.05, after


def test_stabilised_weights_are_near_one_when_treatment_is_random():
    rng = np.random.default_rng(1)
    t = pd.Series(rng.binomial(1, 0.3, 5000))
    # A model that knows only the empirical prevalence must produce weights of exactly 1.
    prevalence = float(t.mean())
    weights = stabilized_weights(t, np.full(len(t), prevalence))
    assert np.allclose(weights, 1.0, atol=1e-9)


def test_effective_sample_size_bounds():
    equal = np.ones(100)
    assert effective_sample_size(equal) == pytest.approx(100.0)
    concentrated = np.zeros(100)
    concentrated[0] = 100.0
    assert effective_sample_size(concentrated) == pytest.approx(1.0)


def test_iptw_recovers_the_true_effect_where_the_naive_difference_does_not():
    df = confounded_sample()
    naive = df.loc[df["T"] == 1, "y"].mean() - df.loc[df["T"] == 0, "y"].mean()
    estimate = iptw_ate(df, "T", "y", ["x"])
    assert naive > 3.0, naive                     # confounding inflates the crude estimate
    assert abs(estimate.estimate - 2.0) < 0.15, estimate.estimate  # weighting recovers it


def test_matched_att_is_finite_and_near_the_truth():
    df = confounded_sample()
    estimate = matched_att(df, "T", "y", ["x"])
    assert np.isfinite(estimate.estimate)
    assert abs(estimate.estimate - 2.0) < 0.5, estimate.estimate
    assert estimate.n_treated > 0 and estimate.n_control > 0


def test_positivity_reports_shares():
    ps = np.array([0.01, 0.5, 0.95, 0.99])
    out = positivity(ps)
    assert out["share_below_0.1"] == pytest.approx(0.25)
    assert out["share_above_0.9"] == pytest.approx(0.5)
    assert out["min"] == pytest.approx(0.01)
