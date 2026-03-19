import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
import time

st.title("Bird Strike Insurance App")

st.subheader("Business Question")
st.write(
    "Which airports have the highest financial risk from bird strikes, "
    "so airlines should prioritize extra insurance coverage or higher coverage limits there?"
)

# Session state
if "chart_type" not in st.session_state:
    st.session_state.chart_type = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "results" not in st.session_state:
    st.session_state.results = []

# Upload dataset
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    # Column selection
    all_columns = df.columns.tolist()
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

    airport_col = st.selectbox("Select airport column:", all_columns)
    cost_col = st.selectbox("Select cost column:", numeric_columns)

    # Prepare data
    data = df[[airport_col, cost_col]].dropna()

    summary = data.groupby(airport_col).agg(
        strike_count=(cost_col, "count"),
        total_cost=(cost_col, "sum")
    ).reset_index()

    summary = summary.sort_values("total_cost", ascending=False).head(10)

    st.subheader("A/B Test")

    if st.button("Show random chart"):
        st.session_state.chart_type = random.choice(["A", "B"])
        st.session_state.start_time = time.time()

    if st.session_state.chart_type is not None:
        fig, ax = plt.subplots(figsize=(10, 6))

        if st.session_state.chart_type == "A":
            st.write("**Chart A: Total financial cost by airport**")
            sns.barplot(data=summary, x="total_cost", y=airport_col, ax=ax)

        else:
            st.write("**Chart B: Number of bird strike incidents by airport**")
            sns.barplot(data=summary, x="strike_count", y=airport_col, ax=ax)

        plt.tight_layout()
        st.pyplot(fig)

        if st.button("Did I answer your question?"):
            response_time = round(time.time() - st.session_state.start_time, 2)

            st.write(f"Chart shown: {st.session_state.chart_type}")
            st.write(f"Time taken: {response_time} seconds")

            st.session_state.results.append({
                "chart": st.session_state.chart_type,
                "time_seconds": response_time
            })

            st.session_state.chart_type = None
            st.session_state.start_time = None

    if len(st.session_state.results) > 0:
        st.subheader("A/B Test Results")
        results_df = pd.DataFrame(st.session_state.results)
        st.dataframe(results_df)

        st.subheader("Average Response Time by Chart")
        avg_df = results_df.groupby("chart", as_index=False)["time_seconds"].mean()
        st.dataframe(avg_df)
