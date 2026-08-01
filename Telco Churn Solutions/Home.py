import streamlit as st

st.title("Telco Churn Solutions")
st.write("""
Churn prediction, SHAP-based explainability, and causal inference on product
adoption effects for a telco customer base. Use the sidebar to explore the
raw data, EDA, the churn prediction model, and the causal inference page.
""")

st.write("## Key findings")
st.markdown("""
- Call Center usage causally **reduces** churn and **increases** CLTV — recommend pushing more customers toward it.
- Video and MyApp usage increase monthly purchase but the net effect on CLTV is uncertain (confidence intervals span zero) — needs product-quality investigation before pushing adoption.
""")

