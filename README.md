# churn-project

Telco churn prediction with SHAP explainability, plus a causal-inference layer
estimating what actually happens to churn, revenue, and CLTV if a customer
adopts a given product — not just what's correlated with it. Built on a public
Indonesian telco churn dataset (Kaggle). Team project with
[Muhammad Ammar S.](https://github.com/mammarstpc) and
[Perisai Zidane H.](https://github.com/pzidaneh).

## Why the causal layer matters

A churn model tells you *who* is likely to churn. It doesn't tell you what to
*do* about it — pushing more customers onto a product that's merely correlated
with lower churn can easily do nothing, because the correlation may just
reflect that engaged customers use more products, not that the product itself
retains them. This project addresses that by estimating the **average
treatment effect** of product adoption directly.

## Components

- **Churn prediction** (`pages/4_Churn_Prediction_Model.py`, `utilities.py`) —
  XGBoost classifier with SHAP explainability; per-customer churn probability
  plus the top contributing features.
- **Causal inference** (`try_causal.ipynb`, `pages/6_Causal Inference.py`) —
  inverse-probability-of-treatment-weighting (IPTW) estimator with a
  propensity-score model (logistic regression) controlling for customer
  covariates, estimating the effect of adopting Call Center, Video, or MyApp
  on churn, monthly purchase, and CLTV. Bootstrapped confidence intervals
  flag which effects are actually distinguishable from zero.
- **Dashboard** (`Home.py` + `pages/`) — Streamlit app: raw data, EDA, churn
  prediction, causal inference, all interactive.

## Findings

- Call Center adoption causally reduces churn and increases CLTV — a clear
  case for driving more adoption.
- Video and MyApp adoption increase monthly purchase, but the CLTV effect's
  confidence interval spans zero — correlated with revenue, but the causal
  effect on lifetime value isn't distinguishable from no effect. Adoption
  pushes for these need product-quality work first, not just marketing.

## Stack

Python · scikit-learn · XGBoost · SHAP · pandas · Streamlit

## Setup

```bash
poetry install
streamlit run "Telco Churn Solutions/Home.py"
```

---

## Data provenance

`Telco Churn Solutions/Telco_customer_churn_adapted_v2.xlsx` derives from the IBM Telco
Customer Churn sample dataset, which IBM distributes publicly for educational use and which
is also mirrored on Kaggle.

The dataset is **not our work** and we assert no licence over it. It is committed so that
the notebook and dashboard reproduce without a download step. The modelling, the IPTW
causal layer and the Streamlit application are our own work (MIT).
