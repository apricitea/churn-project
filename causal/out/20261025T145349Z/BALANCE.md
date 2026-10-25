# Covariate balance and causal estimates (20261025T145349Z)

Rows: 5517 internet-subscribing customers. Weights: stabilised IPTW.

## Balance summary

| Treatment | Treated | Max |SMD| before | Max |SMD| after | Unbalanced before | after | ESS |
|---|---|---|---|---|---|---|---|
| Call Center_Yes | 2044 | 0.829 | 0.053 | 9 | 0 | 4040 |
| Video Product_Yes | 2707 | 0.966 | 0.027 | 5 | 0 | 3985 |
| Use MyApp_Yes | 2732 | 0.711 | 0.008 | 4 | 0 | 4586 |

The 0.1 rule of thumb is a reporting convention (Austin 2009), not a pass/fail test.
Max |SMD| after weighting above 0.1 means the weighted comparison is not exchangeable on
that covariate, whatever the interval says.

## Estimates

| Treatment | Outcome | IPTW ATE [95% CI] | Matched ATT [95% CI] | Signs agree |
|---|---|---|---|---|
| Call Center_Yes | churn | -0.098 [-0.125, -0.066] | -0.060 [-0.093, -0.030] | yes |
| Call Center_Yes | monthly_purchase | +7.370 [+6.781, +7.972] | +6.534 [+3.966, +8.108] | yes |
| Call Center_Yes | cltv | +20.515 [-70.635, +117.708] | -1.264 [-120.926, +147.288] | **no** |
| Video Product_Yes | churn | +0.028 [+0.001, +0.052] | +0.046 [+0.003, +0.086] | yes |
| Video Product_Yes | monthly_purchase | +14.694 [+13.970, +15.523] | +12.704 [+11.740, +14.949] | yes |
| Video Product_Yes | cltv | -55.236 [-139.067, +30.164] | +17.315 [-199.668, +119.018] | **no** |
| Use MyApp_Yes | churn | +0.041 [+0.016, +0.061] | -0.038 [-0.005, +0.080] | **no** |
| Use MyApp_Yes | monthly_purchase | +18.730 [+17.879, +19.456] | +17.110 [+16.501, +19.859] | yes |
| Use MyApp_Yes | cltv | -30.933 [-115.737, +50.338] | -116.970 [-152.357, +167.333] | yes |

## What these numbers do and do not support

- A CI that excludes zero is evidence of an association under the exchangeability
  assumption, not proof of an intervention effect. Unmeasured confounding (price,
  contract type, service quality) is not addressed by any weighting scheme.
- Where the two estimators disagree in sign, the honest reading is that the data do not
  pin the effect down, and the dashboard should not present a single number as if it did.
- For Call Center the covariate set includes other product adoptions, which are plausibly
  post-treatment. That is inherited from the original notebook and is a limitation, not a
  design choice to defend.
