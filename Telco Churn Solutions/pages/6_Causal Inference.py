import streamlit as st
from PIL import Image

st.write("## Product performance evaluation")

product_options = ['Video', 'MyApp', 'Call Center']
product_option = st.selectbox("Product to evalaute: ", product_options)

segment = ""

# If call center, option to evaluate for video and MyApp Users.
if product_option == "Call Center":
    video_users = st.checkbox("Evaluate for video and MyApp Users")
    if video_users:
        segment = " for video and MyApp Users"

def effectdirection(value):
    if value > 0:
        return "increase"
    else:
        return "decrease"

churn_effects = {'Call Center': -0.108, 'Video': 0.060, 'MyApp' : 0.083}
abs_churn_effect = {key: abs(val)*100 for key, val in churn_effects.items()}
direction_churn_effect = {key: effectdirection(val) for key, val in churn_effects.items()}

income_effects = {'Call Center': 6.079, 'Video' : 13.923, 'MyApp' : 19.449}
abs_income_effect = {key: abs(val) for key, val in income_effects.items()}
direction_income_effect = {key: effectdirection(val) for key, val in income_effects.items()}

cltv_effects = {'Call Center': 36.321, 'Video' : -72.680, 'MyApp' : -82.828}
abs_cltv_effect = {key: abs(val) for key, val in cltv_effects.items()}
direction_cltv_effect = {key: effectdirection(val) for key, val in cltv_effects.items()}

certainty = {'Call Center' : '', 'Video': '**However, we are uncertain about this.**', 'MyApp' : '**However, we are uncertain about this.**'}

image_dict = {
    "Video": "Telco Churn Solutions/images/video_cltv.jpg",
    "MyApp": "Telco Churn Solutions/images/myapp_cltv.jpg"
}

confint_abs_start = {
    "Video" : 105.27111976998874,
    "MyApp" : 127.38443608519567 
}

confint_abs_end = {
    "Video" : 146.6804542353386,
    "MyApp" : 80.01620595755293 
}

st.markdown(
f"""
Here's what we know about the performance of **{product_option}{segment}**:
- If a non-user switches to using {product_option}, we can expect a **{abs_churn_effect[product_option]}% {direction_churn_effect[product_option]} in churn** on average.
- If a non-user switches to using {product_option}, we can expect a **Rp{abs_income_effect[product_option]:.3f},00 {direction_income_effect[product_option]} in monthly purchase** on average.
- If a non-user switches to using {product_option}, we can expect a **Rp{abs_cltv_effect[product_option]:.3f},00 {direction_cltv_effect[product_option]} in CLTV** on average. {certainty[product_option]}
"""
)

if product_option == "Video" or product_option == "MyApp":
    show_uncertainty = st.checkbox("Visualise uncertainty in the CLTV effect")
    if show_uncertainty:
        st.write("### Effect uncertainty")
        st.write(f"Here is the interval of estimates for the effect of {product_option} on CLTV:")
        confint = Image.open(image_dict[product_option])
        st.image(confint, caption=f"Effect estimate interval for {product_option}")
        st.markdown(f"""The estimated effect of {product_option} on CLTV ranges from a **Rp{confint_abs_start[product_option]:.3f},00 decrease** to a **Rp{confint_abs_end[product_option]:.3f},00 increase**. There are estimates that show a decrease in CLTV, no effect, and an increase in CLTV. **Thus, we are not certain of {product_option}'s effect on CLTV**.""")

st.write("### Recommendations")
if product_option == "Call Center":
    st.write(f"{product_option} both reduces churn and increases monthly purchases. It has an overall positive effect on CLTV. **More customers should be pushed into using it**.")
else:
    st.markdown(
    f"""
    {product_option} has a trade-off: it increases monthly purchases, but at the cost of increased churn. We are not sure how these two components affect CLTV overall. We should:
    1. Investigate if there are any bugs in the product.
    2. Conduct discussions with users to see if they have a positive experience using that product
    3. If the product as it stands doesn't increase CLTV for all customers, find a segment where it does it increase CLTV.
    """
    )
