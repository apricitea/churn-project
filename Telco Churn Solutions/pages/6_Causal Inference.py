"""Product performance page, driven by the committed causal run rather than constants."""

import streamlit as st

from causal_results import effect, excludes_zero, format_effect, load_latest

st.write("## Product performance evaluation")

run = load_latest()
if run is None:
    st.error(
        "No causal run found. Generate one with `python causal/run.py --n-boot 400` "
        "from the repository root; the page reads `causal/out/<run_id>/results.json`."
    )
    st.stop()

assert run is not None  # st.stop() halts the script; this narrows the type for readers

product_options = ["Video", "MyApp", "Call Center"]
product_option = st.selectbox("Product to evaluate:", product_options)

segment = ""
if product_option == "Call Center":
    if st.checkbox("Evaluate for video and MyApp users"):
        segment = " (video and MyApp users only — the committed run does not yet split this segment)"

churn = effect(run, product_option, "churn")
purchase = effect(run, product_option, "monthly_purchase")
cltv = effect(run, product_option, "cltv")

st.markdown(f"### Estimates for **{product_option}**{segment}")
st.markdown(
    f"""
- Churn: **{format_effect(product_option, 'churn', churn['iptw'])}**
- Monthly purchase: **{format_effect(product_option, 'monthly_purchase', purchase['iptw'])}**
- CLTV: **{format_effect(product_option, 'cltv', cltv['iptw'])}**
"""
)

st.caption(
    f"Run {run['run_id']}: {run['dataset_rows']} internet-subscribing customers. "
    "Inverse-probability-of-treatment weighting with stabilised weights; intervals are "
    "percentile bootstraps that refit the propensity model in every resample."
)

block = run["treatments"][
    {"Call Center": "Call Center_Yes", "Video": "Video Product_Yes", "MyApp": "Use MyApp_Yes"}[
        product_option
    ]
]
st.markdown("#### Covariate balance")
left, middle, right = st.columns(3)
left.metric("Max |SMD| before weighting", f"{block['max_abs_smd_before']:.2f}")
middle.metric("Max |SMD| after weighting", f"{block['max_abs_smd_after']:.2f}")
right.metric("Effective sample size", f"{block['effective_sample_size']:.0f} / {block['n']}")
st.caption(
    "The 0.1 rule of thumb is a reporting convention, not a pass/fail test. "
    f"{block['n_covariates_unbalanced_before']} covariates exceeded it before weighting; "
    f"{block['n_covariates_unbalanced_after']} do after."
)

st.markdown("#### Recommendations")
if not excludes_zero(churn["iptw"]):
    st.write(
        f"The churn effect of {product_option} is **not distinguishable from zero** at this "
        "sample size, so no adoption push is justified on churn grounds alone."
    )
elif churn["iptw"]["point"] < 0:
    if excludes_zero(cltv["iptw"]) and cltv["iptw"]["point"] > 0:
        st.write(
            f"{product_option} **reduces churn and raises CLTV**, with both intervals excluding "
            "zero. Pushing adoption is supported by the data."
        )
    else:
        st.write(
            f"{product_option} **reduces churn**, but the CLTV interval includes zero — the "
            "retention benefit is real while the lifetime-value benefit is not established. "
            "Treat it as a retention play, not a revenue one."
        )
else:
    if excludes_zero(purchase["iptw"]) and purchase["iptw"]["point"] > 0:
        st.write(
            f"{product_option} **raises churn** while raising monthly purchase: a revenue/"
            "retention trade-off. Before scaling it, check whether the product has a defect "
            "or a segment where CLTV rises."
        )
    else:
        st.write(f"{product_option} raises churn without a established revenue benefit.")

st.caption(
    "Exchangeability is assumed: no unmeasured confounder (price, contract type, service "
    "quality) is adjusted for. These are association-under-assumption estimates, not "
    "guaranteed intervention effects."
)
