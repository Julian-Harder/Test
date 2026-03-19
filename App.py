import streamlit as st
import pandas as pd

st.title("Assignment Exercise 2: Data Exploration App")

@st.cache_data
def load_data():
    return pd.read_csv("titanic.csv")

df = load_data()

with st.container():
    st.header("Dataset Summary")
    st.write(f"Shape: {df.shape}")
    st.write("Columns:", list(df.columns))
    st.dataframe(df.head())

    selected_sex = st.selectbox("Filter by sex:", ["All"] + list(df["Sex"].dropna().unique()))

    if selected_sex == "All":
        filtered_df = df
    else:
        filtered_df = df[df["Sex"] == selected_sex]

    st.dataframe(filtered_df)

with st.expander("Show detailed statistics"):
    st.write(filtered_df.describe())
    st.write(filtered_df.isnull().sum())


    