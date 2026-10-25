# churn-project

Telco churn prediction with SHAP explainability, plus a propensity-score causal layer that
estimates what product adoption actually does to churn, monthly purchase and CLTV — with the
balance diagnostics and cross-estimator check that a causal claim needs. Built on a public
telco churn dataset. Team project with
[Muhammad Ammar S.](https://github.com/mammarstpc) and
[Perisai Zidane H.](https://github.com/pzidaneh).

## Why the causal layer matters

A churn model tells you *who* is likely to churn. It does not tell you what to *do*: pushing
customers onto a product that is merely correlated with lower churn can easily do nothing,
because the correlation may reflect that engaged customers buy more products, not that the
product retains them. This project estimates the **average treatment effect** of adoption
instead of reading a coefficient off a predictive model.

## What the estimates say

Inverse-probability-of-treatment weighting, stabilised weights, 5,517 internet-subscribing
customers, percentile bootstrap intervals that refit the propensity model in every resample
(committed run `causal/out/20261025T145349Z`, 300 bootstrap resamples). Point estimates are percentage points for churn
and thousand IDR for purchase and CLTV.

| Product | Churn | Monthly purchase | CLTV |
|---|---|---|---|
| Call Center | **−9.8 pp** [−12.5, −6.6] | **+7.4** [+6.8, +8.0] | +20.5 [−70.6, +117.7] |
| Video | +2.8 pp [+0.1, +5.2] | **+14.7** [+14.0, +15.5] | −55.2 [−139.1, +30.2] |
| MyApp | +4.1 pp [+1.6, +6.1] | **+18.7** [+17.9, +19.5] | −30.9 [−115.7, +50.3] |

Read against what the project previously claimed:

- **Call Center reduces churn and lifts monthly purchase, both with intervals excluding zero.
  Its CLTV effect is not established** — the interval runs from a 71k loss to a 118k gain, and
  the propensity-matched ATT disagrees in sign. The earlier README called this "a clear case
  for driving more adoption"; the retention case survives, the lifetime-value case does not.
- **Video raises churn** (+2.8 pp, interval starting at +0.1 pp — a weak but non-zero signal) while
  raising monthly purchase: a genuine revenue/retention trade-off, not a free win.
- **MyApp's churn effect is not identified**: IPTW says +4.1 pp, matching says −3.8 pp. When two
  estimators disagree in sign, the honest statement is that this dataset does not pin the
  direction down.

Covariate balance after weighting: max |standardised mean difference| falls from 0.83 / 0.97 /
0.71 to 0.053 / 0.027 / 0.008 across the three treatments; effective sample size is 3,985–4,586
of 5,517. Full tables, per-covariate SMDs and Love plots are in `causal/out/<run>/BALANCE.md`.

## Method

- **Propensity model**: logistic regression on customer covariates, unregularised (C = 1e6),
  mirroring the original notebook.
- **Estimator**: stabilised IPTW, `P(T=t)/P(T=t|X)`; ATE is the weighted difference in means.
- **Cross-check**: 1-nearest-neighbour matching on `logit(propensity)`, with replacement (ATT).
  Two estimators with different failure modes; when they disagree the report says so.
- **Uncertainty**: percentile bootstrap, propensity refit in every resample.
- **Diagnostics**: standardised mean differences before and after weighting, effective sample
  size, propensity overlap, and the share of the sample outside [0.1, 0.9].

## Components

| Path | Contents |
|---|---|
| `causal/analysis.py` | propensity model, SMDs, IPTW, matching, bootstrap, positivity |
| `causal/run.py` | runs every product × outcome, writes `results.json`, `BALANCE.md`, Love plots |
| `Telco Churn Solutions/causal_results.py` | reads the latest run so the dashboard cannot drift from it |
| `Telco Churn Solutions/pages/6_Causal Inference.py` | causal page, now driven by the committed run instead of constants |
| `Telco Churn Solutions/pages/4_Churn_Prediction_Model.py` | XGBoost churn model with SHAP attributions |
| `Telco Churn Solutions/try_causal.ipynb` | the original notebook, kept so the correction is legible |

## Reproduce

```bash
uv venv .venv && VIRTUAL_ENV=.venv uv pip install pandas scikit-learn matplotlib openpyxl
.venv/bin/python causal/run.py --n-boot 60        # ~1 minute; raise n-boot for tighter intervals
streamlit run "Telco Churn Solutions/Home.py"
```

## Limitations

- **Exchangeability is assumed.** No unmeasured confounder — price, contract type, service
  quality — is adjusted for. These are association-under-assumption estimates, not guaranteed
  intervention effects.
- **The Call Center covariate set includes other product adoptions**, which are plausibly
  post-treatment. That is inherited from the original notebook and biases the estimate toward
  zero; it is a defect, not a design choice.
- **Single dataset, single time slice.** The IBM/Kaggle telco sample is not a randomised trial
  and its collection process is undocumented.
- Churn is measured as a label in the dataset, not as an observed event with a timestamp, so
  the estimand is "adoption is associated with the recorded label under the model", no more.

## Stack

Python · scikit-learn · XGBoost · SHAP · pandas · SciPy · Streamlit

---

## Data provenance

`Telco Churn Solutions/Telco_customer_churn_adapted_v2.xlsx` derives from the IBM Telco
Customer Churn sample dataset, which IBM distributes publicly for educational use and which is
also mirrored on Kaggle.

The dataset is **not our work** and we assert no licence over it. It is committed so that the
analysis and dashboard reproduce without a download step. The modelling, the causal layer and
the Streamlit application are our own work (MIT).
