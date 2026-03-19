import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
import time

st.title("Bird Strike Insurance App")

st.subheader("Business Question")
st.write("Which airports have the highest financial risk from bird strikes, so should airlines should prioritize extra insurance coverage or higher coverage limits there?")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Dataset Preview")
    st.write(df.head())

    st.subheader("Choose Variables")
    airport_col = st.selectbox("Airport column", df.columns)
    cost_col = st.selectbox("Cost column", df.columns)

    if "chart_type" not in st.session_state:
        st.session_state.chart_type = None

    if "start_time" not in st.session_state:
        st.session_state.start_time = None

    if "results" not in st.session_state:
        st.session_state.results = []

    st.subheader("Show a Random Chart")

    if st.button("Show chart"):
        st.session_state.chart_type = random.choice(["A", "B"])
        st.session_state.start_time = time.time()

    if st.session_state.chart_type is not None:
        data = df[[airport_col, cost_col]].dropna()

        summary = data.groupby(airport_col).agg(
            strike_count=(cost_col, "count"),
            total_cost=(cost_col, "sum")
        ).reset_index()

        summary["risk_score"] = summary["strike_count"] * (summary["total_cost"] / summary["strike_count"])
        summary = summary.sort_values("risk_score", ascending=False).head(10)

        fig, ax = plt.subplots()

        if st.session_state.chart_type == "A":
            st.subheader("Chart A")
            st.write("Total cost by airport")
            sns.barplot(data=summary, x="total_cost", y=airport_col, ax=ax)

        else:
            st.subheader("Chart B")
            st.write("Strike count by airport")
            sns.barplot(data=summary, x="strike_count", y=airport_col, ax=ax)

        st.pyplot(fig)

        if st.button("Did I answer your question?"):
            end_time = time.time()
            response_time = end_time - st.session_state.start_time

            st.write("Chart shown:", st.session_state.chart_type)
            st.write("Time taken:", round(response_time, 2), "seconds")

            st.session_state.results.append({
                "chart": st.session_state.chart_type,
                "time_seconds": round(response_time, 2)
            })

            st.session_state.chart_type = None
            st.session_state.start_time = None

    if len(st.session_state.results) > 0:
        st.subheader("A/B Test Results")
        results_df = pd.DataFrame(st.session_state.results)
        st.write(results_df)

        st.subheader("Average Time by Chart")
        st.write(results_df.groupby("chart")["time_seconds"].mean().reset_index())

