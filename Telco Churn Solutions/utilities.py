import pandas as pd
import numpy as np
import joblib

df_churn = pd.read_excel("Telco_customer_churn_adapted_v2.xlsx")
df_churn['Internet'] = df_churn['Video Product'].apply(lambda x: 0 if x == 'No internet access' else 1)
series_nan = pd.Series([np.nan]).repeat(df_churn.shape[0])

churn_model = joblib.load("churn_model.joblib")
