import streamlit as st
import pandas as pd
import shap
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, precision_score, recall_score, confusion_matrix

from utilities import df_churn
from utilities import churn_model

# preprocessing
df_churn['Internet'] = df_churn['Video Product'].apply(lambda x: 0 if x == 'No internet access' else 1)

# model prediction
X = df_churn[['Tenure Months','Monthly Purchase (Thou. IDR)', 'Device Class', 'Call Center', 'Use MyApp', 'Payment Method', 'Internet',
        'Games Product', 'Music Product', 'Education Product', 'Video Product']]
y = df_churn['Churn Label'].apply(lambda x: 1 if x == 'Yes' else 0)
predictions = churn_model.predict(X)
st.write("The model accuracy is: ",accuracy_score(y, predictions))

# User Input variables
tenure_m_input = st.number_input("Enter the user Tenure months: ")
monthly_p_input = st.number_input("Enter the user Monthly Purchase (in Thousands IDR): ")

# Define a list of options
device_c_options = ['Low End', 'Mid End', 'High End']
device_c_option = st.selectbox("Users Device Class: ", device_c_options)

payment_m_options = ['Pulsa', 'Debit', 'Credit', 'Digital Wallet']
payment_m_option = st.selectbox("Users Payment Method: ", payment_m_options)

# Define a list of options
internet_selected = st.checkbox("Internet")

# Products
products = ['Games Product', 'Music Product', 'Education Product', 'Video Product', 'Call Center', 'MyApp']
selected_products = st.multiselect("Product that the Users subscribe to:", products)

# Define new data observations
new_data = pd.DataFrame({
    'Tenure Months': [tenure_m_input],
    'Monthly Purchase (Thou. IDR)': [monthly_p_input],
    'Device Class': [device_c_option],
    'Call Center': [1 if 'Call Center' in selected_products else 0],
    'Use MyApp': [1 if 'MyApp' in selected_products else 0],
    'Payment Method': [payment_m_option],
    'Internet': [internet_selected],  # Remove square brackets here
    'Games Product': [1 if 'Games Product' in selected_products else 0],
    'Music Product': [1 if 'Music Product' in selected_products else 0],
    'Education Product': [1 if 'Education Product' in selected_products else 0],
    'Video Product': [1 if 'Video Product' in selected_products else 0]
})

st.write("Users characteristics", new_data)
st.write("The probability that the user will churn is: ", churn_model.predict_proba(new_data)[:, 1])

# SHAP
xgb_classifier = churn_model.named_steps['clf_xgbc']
preprocessor = churn_model.named_steps['preprocessing']

transformed_data = preprocessor.transform(X)
preprocessed_df = pd.DataFrame(transformed_data)
transformed_columns = preprocessor.get_feature_names_out(input_features=X.columns).tolist()

explainer = shap.Explainer(xgb_classifier)
shap_values = explainer.shap_values(preprocessed_df)
shap_values_df = pd.DataFrame(shap_values, columns=transformed_columns)

def compile_shap_values(row):
    shap_texts = []
    for col_name, value in zip(transformed_columns, row):
        shap_texts.append(f"{col_name}: {value:.4f}")
    return ', '.join(shap_texts)

feature_name_mapping = {
    'remainder__destination_account_number': 'Frequency of Transactions to the Destination Account',
    'remainder__source_account_number': 'Frequency of Transactions to the Source Account',
    'remainder__transaction_amount': 'Transaction Amount',
    **{column: 'Transaction Time' 
       for column in transformed_columns 
       if column.startswith('onehot__time_')}
}

def get_most_impactful_features(row):
    top_indices = np.argsort(row)[-2:][::-1]

    feature_names = [feature_name_mapping.get(shap_values_df.columns[idx], shap_values_df.columns[idx]) for idx in top_indices]

    sorted_features = sorted(feature_names)  
    if sorted_features[0] == sorted_features[1]:
        return sorted_features[0]  
    else:
        return ' and '.join(sorted_features) 

transformed_columns = [feature_name_mapping.get(name, name) for name in transformed_columns]

df['shap'] = shap_values_df.apply(compile_shap_values, axis=1)
df['rules_desc'] = shap_values_df.apply(get_most_impactful_features, axis=1)
