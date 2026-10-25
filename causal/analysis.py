"""Propensity-score causal analysis with the diagnostics a reviewer asks for first.

The dashboard's causal page previously displayed constants copied from a notebook that
used ``CausalModel.est_via_matching``. This module does what the README always claimed:
an inverse-probability-of-treatment-weighted (IPTW) average treatment effect, with

* standardised mean differences before and after weighting, per covariate,
* the effective sample size implied by the weights,
* a positivity check (share of the sample with propensity outside [0.1, 0.9]),
* percentile bootstrap intervals that refit the propensity model in every resample,
* and a propensity-matched ATT as an independent cross-check.

Two estimators that agree are worth more than one estimator with a small p-value. When
they disagree, the report says so instead of picking the friendlier number.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors

OUTCOMES = {
    "churn": "Churn Label_Yes",
    "monthly_purchase": "Monthly Purchase (Thou. IDR)",
    "cltv": "CLTV (Predicted Thou. IDR)",
}
PRODUCTS = ["Call Center_Yes", "Video Product_Yes", "Use MyApp_Yes"]
OTHER_PRODUCTS = {
    "Call Center_Yes": [],
    # Mirroring the notebook: for Video and MyApp the other product flags are excluded
    # from the covariate set. Those adoptions are plausibly post-treatment and including
    # them would adjust away part of the effect. For Call Center the notebook keeps them,
    # which is a modelling choice, not a defensible one -- it is reported as a limitation.
    "Video Product_Yes": ["Call Center_Yes", "Games Product_Yes", "Education Product_Yes", "Music Product_Yes"],
    "Use MyApp_Yes": ["Call Center_Yes", "Games Product_Yes", "Video Product_Yes", "Education Product_Yes", "Music Product_Yes"],
}


def load_user_df(path: Path | str) -> pd.DataFrame:
    """Replicate the notebook's preprocessing: internet users, one-hot encoded."""
    df = pd.read_excel(path)
    df["Internet"] = np.where(df["Games Product"] == "No internet service", 0, 1)
    product_cols = ["Games Product", "Music Product", "Education Product", "Call Center", "Video Product", "Use MyApp"]
    df[product_cols] = df[product_cols].replace({"No internet service": "No"})
    encoded = pd.concat(
        [
            df,
            pd.get_dummies(
                df[
                    [
                        "Device Class",
                        "Payment Method",
                        "Games Product",
                        "Music Product",
                        "Education Product",
                        "Call Center",
                        "Video Product",
                        "Use MyApp",
                        "Churn Label",
                    ]
                ],
                prefix=[
                    "Device_Class",
                    "Payment Method",
                    "Games Product",
                    "Music Product",
                    "Education Product",
                    "Call Center",
                    "Video Product",
                    "Use MyApp",
                    "Churn Label",
                ],
                drop_first=True,
            ),
        ],
        axis=1,
    )
    fin = encoded.drop(
        [
            "Longitude",
            "Latitude",
            "Location",
            "Churn Label",
            "Device Class",
            "Games Product",
            "Payment Method",
            "Music Product",
            "Education Product",
            "Call Center",
            "Video Product",
            "Use MyApp",
        ],
        axis=1,
    )
    return fin[fin["Internet"] == 1].drop("Internet", axis=1).reset_index(drop=True)


def covariates_for(df: pd.DataFrame, treatment: str) -> list[str]:
    """All columns except identifiers, the treatment and every outcome."""
    excluded = {"Customer ID", treatment, *OUTCOMES.values(), *OTHER_PRODUCTS.get(treatment, [])}
    return [c for c in df.columns if c not in excluded]


def fit_propensity(df: pd.DataFrame, treatment: str, covariates: list[str]) -> np.ndarray:
    model = LogisticRegression(C=1e6, max_iter=5000)
    model.fit(df[covariates], df[treatment])
    return model.predict_proba(df[covariates])[:, 1]


def standardized_mean_difference(
    df: pd.DataFrame, treatment: str, covariates: list[str], weights: np.ndarray | None = None
) -> pd.Series:
    """SMD per covariate: difference in means divided by the pooled SD.

    The 0.1 rule of thumb (Austin 2009) is used as the reporting threshold, not as a
    pass/fail gate.
    """
    treated = df[treatment].to_numpy() == 1
    out = {}
    for column in covariates:
        values = df[column].astype(float).to_numpy()
        if weights is None:
            t_mean, c_mean = values[treated].mean(), values[~treated].mean()
            t_var, c_var = values[treated].var(ddof=1), values[~treated].var(ddof=1)
        else:
            w = weights
            t_mean = np.average(values[treated], weights=w[treated])
            c_mean = np.average(values[~treated], weights=w[~treated])
            t_var = np.average((values[treated] - t_mean) ** 2, weights=w[treated])
            c_var = np.average((values[~treated] - c_mean) ** 2, weights=w[~treated])
        pooled = np.sqrt((t_var + c_var) / 2)
        out[column] = 0.0 if pooled == 0 else (t_mean - c_mean) / pooled
    return pd.Series(out, dtype=float)


def stabilized_weights(treatment: pd.Series, ps: np.ndarray) -> np.ndarray:
    """Stabilised IPTW: P(T=t) / P(T=t | X). Stabilising keeps the weights near 1."""
    t = treatment.to_numpy().astype(int)
    prevalence = t.mean()
    return np.where(t == 1, prevalence / np.clip(ps, 1e-6, 1 - 1e-6), (1 - prevalence) / np.clip(1 - ps, 1e-6, 1 - 1e-6))


def effective_sample_size(weights: np.ndarray) -> float:
    return float(weights.sum() ** 2 / np.sum(weights**2))


@dataclass(frozen=True)
class Effect:
    estimate: float
    estimator: str
    n_treated: int
    n_control: int

    def as_dict(self) -> dict:
        return {"estimate": self.estimate, "estimator": self.estimator, "n_treated": self.n_treated, "n_control": self.n_control}


def iptw_ate(df: pd.DataFrame, treatment: str, outcome: str, covariates: list[str]) -> Effect:
    ps = fit_propensity(df, treatment, covariates)
    weights = stabilized_weights(df[treatment], ps)
    t = df[treatment].to_numpy().astype(int)
    y = df[outcome].astype(float).to_numpy()
    treated_mean = np.average(y[t == 1], weights=weights[t == 1])
    control_mean = np.average(y[t == 0], weights=weights[t == 0])
    return Effect(float(treated_mean - control_mean), "iptw_ate", int(t.sum()), int((1 - t).sum()))


def matched_att(df: pd.DataFrame, treatment: str, outcome: str, covariates: list[str], k: int = 1) -> Effect:
    """Nearest-neighbour propensity matching on the logit scale, with replacement."""
    ps = np.clip(fit_propensity(df, treatment, covariates), 1e-6, 1 - 1e-6)
    logit = np.log(ps / (1 - ps)).reshape(-1, 1)
    t = df[treatment].to_numpy().astype(int)
    y = df[outcome].astype(float).to_numpy()
    treated_idx = np.flatnonzero(t == 1)
    control_idx = np.flatnonzero(t == 0)
    if len(control_idx) == 0 or len(treated_idx) == 0:
        return Effect(float("nan"), "matched_att", len(treated_idx), len(control_idx))
    neighbours = NearestNeighbors(n_neighbors=min(k, len(control_idx))).fit(logit[control_idx])
    _, idx = neighbours.kneighbors(logit[treated_idx])
    matched_controls = control_idx[idx.reshape(-1)]
    return Effect(
        float(y[treated_idx].mean() - y[matched_controls].mean()),
        "matched_att",
        len(treated_idx),
        len(matched_controls),
    )


def bootstrap(
    df: pd.DataFrame,
    treatment: str,
    outcome: str,
    covariates: list[str],
    estimator: str,
    n_boot: int = 400,
    seed: int = 0,
) -> dict:
    """Percentile bootstrap that refits the propensity model in every resample."""
    rng = np.random.default_rng(seed)
    point = (iptw_ate if estimator == "iptw_ate" else matched_att)(df, treatment, outcome, covariates).estimate
    draws = np.empty(n_boot)
    n = len(df)
    for i in range(n_boot):
        sample = df.iloc[rng.integers(0, n, n)]
        try:
            draws[i] = (iptw_ate if estimator == "iptw_ate" else matched_att)(sample, treatment, outcome, covariates).estimate
        except Exception:  # noqa: BLE001 - a degenerate resample should not kill the run
            draws[i] = np.nan
    draws = draws[~np.isnan(draws)]
    return {
        "point": float(point),
        "low": float(np.quantile(draws, 0.025)) if len(draws) else float("nan"),
        "high": float(np.quantile(draws, 0.975)) if len(draws) else float("nan"),
        "n_boot": int(len(draws)),
    }


def positivity(ps: np.ndarray) -> dict:
    return {
        "share_below_0.1": float(np.mean(ps < 0.1)),
        "share_above_0.9": float(np.mean(ps > 0.9)),
        "min": float(ps.min()),
        "max": float(ps.max()),
    }
