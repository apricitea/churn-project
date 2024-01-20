import pandas as pd
import numpy as np

df_churn = pd.read_excel("Telco_customer_churn_adapted_v2.xlsx")
print(df_churn.apply(lambda x: len(x.unique())))

series_nan = pd.Series([np.nan]).repeat(df_churn.shape[0])
