"""Read the latest causal run so the dashboard cannot drift from the analysis.

The page used to print constants copied out of a notebook. Anything copied by hand
eventually disagrees with the model that produced it, and a reader has no way to tell
which number is live. This module reads ``causal/out/<run_id>/results.json`` instead,
and the page says plainly when no run exists.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / "causal" / "out"

PRODUCT_KEYS = {
    "Call Center": "Call Center_Yes",
    "Video": "Video Product_Yes",
    "MyApp": "Use MyApp_Yes",
}

OUTCOME_UNITS = {
    "churn": ("percentage points", 100.0),
    "monthly_purchase": ("thousand IDR", 1.0),
    "cltv": ("thousand IDR", 1.0),
}


def load_latest() -> dict | None:
    """Newest run by directory name (run ids are UTC timestamps), or None."""
    if not RUNS_DIR.exists():
        return None
    runs = sorted((p for p in RUNS_DIR.iterdir() if (p / "results.json").exists()), reverse=True)
    if not runs:
        return None
    return json.loads((runs[0] / "results.json").read_text())


def effect(run: dict, product: str, outcome: str) -> dict:
    """IPTW and matched estimates for one product x outcome, with intervals."""
    block = run["treatments"][PRODUCT_KEYS[product]]["outcomes"][outcome]
    return {
        "iptw": block["iptw_ate"]["ci"],
        "matched": block["matched_att"]["ci"],
        "agree": block["estimators_agree_in_sign"],
    }


def excludes_zero(interval: dict) -> bool:
    return interval["low"] > 0 or interval["high"] < 0


def format_effect(product: str, outcome: str, value: dict) -> str:
    label, scale = OUTCOME_UNITS[outcome]
    point = value["point"] * scale
    low = value["low"] * scale
    high = value["high"] * scale
    direction = "increase" if point > 0 else "decrease"
    return (
        f"{abs(point):.2f} {label} {direction} "
        f"(IPTW 95% CI {low:+.2f} to {high:+.2f})"
    )
