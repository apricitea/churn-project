import streamlit as st

from utilities import df_churn

def select(data, by, condition, exactMatchBool):
	refColumn = df_churn[by].astype(str)
	if exactMatchBool:
		mask = (refColumn == condition)
	else:
		mask = refColumn.str.contains(condition)  # (r'\d+')

	return df_churn.loc[mask]

st.write("## Original Data")
searchColumn = st.selectbox("Search by:", df_churn.columns)

if len(df_churn[searchColumn].unique()) <= 5:
	searchCondition = st.selectbox("Search Condition:", df_churn[searchColumn].unique(), label_visibility="collapsed")
else:
	searchCondition = st.text_input("Search Condition:", value="", placeholder="Type your search conditions here", label_visibility="collapsed")

st.checkbox("Exact Match", key="exactMatch")

#st.write(df_churn[searchColumn].unique())

if searchCondition == "" :
	st.dataframe(df_churn)
else:
	df_churn_selected = select(data=df_churn, by=searchColumn, condition=searchCondition, exactMatchBool=st.session_state.exactMatch)
	st.dataframe(df_churn_selected)
