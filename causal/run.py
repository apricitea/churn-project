"""Run the IPTW and matching analyses for every treatment x outcome pair.

    python causal/run.py --n-boot 400

Writes ``causal/out/<run_id>/`` with results.json, BALANCE.md and a Love plot.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mpl-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis import (  # noqa: E402
    OUTCOMES,
    PRODUCTS,
    bootstrap,
    covariates_for,
    effective_sample_size,
    fit_propensity,
    iptw_ate,
    load_user_df,
    matched_att,
    positivity,
    stabilized_weights,
    standardized_mean_difference,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Telco Churn Solutions" / "Telco_customer_churn_adapted_v2.xlsx"


def love_plot(rows: list[dict], path: Path, treatment: str) -> Path:
    rows = sorted(rows, key=lambda r: abs(r["smd_after"]), reverse=True)[:12]
    y = np.arange(len(rows))
    before = [abs(r["smd_before"]) for r in rows]
    after = [abs(r["smd_after"]) for r in rows]
    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=160)
    ax.scatter(before, y, color="#a4443a", label="before weighting", s=28, zorder=3)
    ax.scatter(after, y, color="#4a6d8c", label="after IPTW", s=28, zorder=3)
    for i, (b, a) in enumerate(zip(before, after)):
        ax.plot([b, a], [i, i], color="#dcd8cf", linewidth=1.2, zorder=1)
    ax.axvline(0.1, linestyle="--", color="#8a8579", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels([r["covariate"] for r in rows], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("|standardised mean difference|")
    ax.set_title(f"Covariate balance, {treatment} (dashed line = 0.1 rule of thumb)", fontsize=9.5, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "causal" / "out")
    parser.add_argument("--n-boot", type=int, default=400)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = args.out_dir / run_id
    out.mkdir(parents=True, exist_ok=True)

    df = load_user_df(args.data)
    results: dict = {
        "run_id": run_id,
        "dataset_rows": int(len(df)),
        "treatments": {},
        "method": {
            "propensity_model": "logistic regression, C=1e6, no regularisation",
            "iptw": "stabilised weights P(T=t)/P(T=t|X); ATE = weighted mean difference",
            "matching": "1-nearest-neighbour on logit(propensity), with replacement; ATT",
            "intervals": f"percentile bootstrap, {args.n_boot} resamples, propensity refit in each",
        },
    }

    balance_rows_all: list[dict] = []
    for treatment in PRODUCTS:
        covariates = covariates_for(df, treatment)
        ps = fit_propensity(df, treatment, covariates)
        weights = stabilized_weights(df[treatment], ps)
        smd_before = standardized_mean_difference(df, treatment, covariates)
        smd_after = standardized_mean_difference(df, treatment, covariates, weights=weights)
        positivity_stats = positivity(ps)

        treatment_block = {
            "n": int(len(df)),
            "n_treated": int(df[treatment].sum()),
            "n_control": int((1 - df[treatment]).sum()),
            "prevalence": float(df[treatment].mean()),
            "positivity": positivity_stats,
            "effective_sample_size": effective_sample_size(weights),
            "max_abs_smd_before": float(smd_before.abs().max()),
            "max_abs_smd_after": float(smd_after.abs().max()),
            "n_covariates_unbalanced_before": int((smd_before.abs() > 0.1).sum()),
            "n_covariates_unbalanced_after": int((smd_after.abs() > 0.1).sum()),
            "outcomes": {},
            "balance": [
                {
                    "covariate": c,
                    "smd_before": float(smd_before[c]),
                    "smd_after": float(smd_after[c]),
                }
                for c in covariates
            ],
        }

        for outcome_name, outcome_col in OUTCOMES.items():
            iptw_point = iptw_ate(df, treatment, outcome_col, covariates)
            match_point = matched_att(df, treatment, outcome_col, covariates)
            iptw_ci = bootstrap(df, treatment, outcome_col, covariates, "iptw_ate", args.n_boot, args.seed)
            match_ci = bootstrap(df, treatment, outcome_col, covariates, "matched_att", args.n_boot, args.seed)
            treatment_block["outcomes"][outcome_name] = {
                "iptw_ate": {**iptw_point.as_dict(), "ci": iptw_ci},
                "matched_att": {**match_point.as_dict(), "ci": match_ci},
                "estimators_agree_in_sign": bool(
                    np.sign(iptw_ci["point"]) == np.sign(match_ci["point"])
                ),
            }

        results["treatments"][treatment] = treatment_block
        balance_rows_all.extend(
            {"treatment": treatment, **row} for row in treatment_block["balance"]
        )
        love_plot(treatment_block["balance"], out / f"love_{treatment.split()[0].lower()}.png", treatment)

    (out / "results.json").write_text(json.dumps(results, indent=2))
    pd.DataFrame(balance_rows_all).to_csv(out / "balance.csv", index=False)

    lines = [
        f"# Covariate balance and causal estimates ({run_id})",
        "",
        f"Rows: {len(df)} internet-subscribing customers. Weights: stabilised IPTW.",
        "",
        "## Balance summary",
        "",
        "| Treatment | Treated | Max |SMD| before | Max |SMD| after | Unbalanced before | after | ESS |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, block in results["treatments"].items():
        lines.append(
            f"| {name} | {block['n_treated']} | {block['max_abs_smd_before']:.3f} | "
            f"{block['max_abs_smd_after']:.3f} | {block['n_covariates_unbalanced_before']} | "
            f"{block['n_covariates_unbalanced_after']} | {block['effective_sample_size']:.0f} |"
        )
    lines += [
        "",
        "The 0.1 rule of thumb is a reporting convention (Austin 2009), not a pass/fail test.",
        "Max |SMD| after weighting above 0.1 means the weighted comparison is not exchangeable on",
        "that covariate, whatever the interval says.",
        "",
        "## Estimates",
        "",
        "| Treatment | Outcome | IPTW ATE [95% CI] | Matched ATT [95% CI] | Signs agree |",
        "|---|---|---|---|---|",
    ]
    for name, block in results["treatments"].items():
        for outcome, values in block["outcomes"].items():
            iptw, match = values["iptw_ate"], values["matched_att"]
            agree = "yes" if values["estimators_agree_in_sign"] else "**no**"
            lines.append(
                f"| {name} | {outcome} | {iptw['ci']['point']:+.3f} "
                f"[{iptw['ci']['low']:+.3f}, {iptw['ci']['high']:+.3f}] | "
                f"{match['ci']['point']:+.3f} [{match['ci']['low']:+.3f}, {match['ci']['high']:+.3f}] | "
                f"{agree} |"
            )
    lines += [
        "",
        "## What these numbers do and do not support",
        "",
        "- A CI that excludes zero is evidence of an association under the exchangeability",
        "  assumption, not proof of an intervention effect. Unmeasured confounding (price,",
        "  contract type, service quality) is not addressed by any weighting scheme.",
        "- Where the two estimators disagree in sign, the honest reading is that the data do not",
        "  pin the effect down, and the dashboard should not present a single number as if it did.",
        "- For Call Center the covariate set includes other product adoptions, which are plausibly",
        "  post-treatment. That is inherited from the original notebook and is a limitation, not a",
        "  design choice to defend.",
        "",
    ]
    (out / "BALANCE.md").write_text("\n".join(lines))

    print(f"wrote {out}")
    for name, block in results["treatments"].items():
        print(
            f"{name:18s} max|SMD| {block['max_abs_smd_before']:.2f} -> {block['max_abs_smd_after']:.2f}  "
            f"ESS {block['effective_sample_size']:.0f}/{block['n']}"
        )
        for outcome, values in block["outcomes"].items():
            ci = values["iptw_ate"]["ci"]
            print(f"    {outcome:16s} IPTW {ci['point']:+.3f} [{ci['low']:+.3f}, {ci['high']:+.3f}]")


if __name__ == "__main__":
    main()
