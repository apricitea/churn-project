import streamlit as st

import matplotlib.pyplot as plt
from utilities import df_churn, series_nan

varOptions = [None] + df_churn.columns.to_list()

varX = st.selectbox("X Variable", varOptions, label_visibility="visible")
varY = st.selectbox("Y Variable", varOptions, label_visibility="visible")
varGroup = st.selectbox("Group by", varOptions, label_visibility="visible")
#varFilter = st.selectbox("Filter by", varOptions, label_visibility="visible")  # to show/hide certain category/value range only


def takeSeries(data, column_name):
	if column_name is None:
		return series_nan
	else:
		return df_churn[column_name]


X = takeSeries(df_churn, varX)
Y = takeSeries(df_churn, varY)
Group = takeSeries(df_churn, varGroup)
#Filter = takeSeries(df_churn, varFilter)

chartOption = ["bar", "scatter"]
chartType = st.selectbox("Chart", chartOption, label_visibility="visible")


def labelEncoder(series):
	unique_labels = series.unique()
	label_map = {label: idx for idx, label in enumerate(unique_labels)}
	encoded_series = series.map(label_map)
	return encoded_series


def groupedScatter(X, Y, Group, ax):
	groups = Group.unique()
	for idx, label in enumerate(groups):
		ax.scatter(X[Group == label], Y[Group == label], color="black", label=label, alpha=.8)
		return ax


fig, ax = plt.subplots()
#ax.scatter(X, Y, c=labelEncoder(Group), alpha=.8)
#ax.legend(handle=[idx for idx, label in enumerate(Group.unique())], label=Group.unique())
ax = groupedScatter(X, Y, Group, ax)
ax.legend()
ax.set_xlabel(varX)
ax.set_ylabel(varY)

st.pyplot(fig)
