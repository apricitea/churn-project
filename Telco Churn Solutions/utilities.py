import pandas as pd
import numpy as np
import joblib

df_churn = pd.read_excel("Telco_customer_churn_adapted_v2.xlsx")
series_nan = pd.Series([np.nan]).repeat(df_churn.shape[0])

churn_model = joblib.load("churn_model.joblib")