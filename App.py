import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
import time

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Bird Strike A/B Testing App",
    layout="wide"
)

# --------------------------------------------------
# Session state
# --------------------------------------------------
if "chart_choice" not in st.session_state:
    st.session_state.chart_choice = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "results" not in st.session_state:
    st.session_state.results = []

# --------------------------------------------------
# App title and question
# --------------------------------------------------
st.title("Bird Strike Financial Risk App")

st.header("Business Question")
st.write(
    "Which airports have the highest financial risk from bird strikes, "
    "so airlines should prioritize extra insurance coverage or higher coverage limits there?"
)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

# Stop app until a file is uploaded
if uploaded_file is None:
    st.info("Please upload a CSV file in the sidebar to start the analysis.")
    st.stop()

# --------------------------------------------------
# Load data
# --------------------------------------------------
df = pd.read_csv(uploaded_file)

# --------------------------------------------------
# Dataset preview in a container
# --------------------------------------------------
with st.container():
    st.subheader("Dataset Preview")

    col1, col2 = st.columns(2)

    with col1:
        st.write("First rows of the dataset:")
        st.dataframe(df.head())

    with col2:
        st.write("Dataset shape:")
        st.write(df.shape)
        st.write("Columns:")
        st.write(list(df.columns))

# --------------------------------------------------
# Variable selection
# --------------------------------------------------
st.subheader("Select Variables")

all_columns = df.columns.tolist()
numeric_columns = df.select_dtypes(include="number").columns.tolist()

col1, col2 = st.columns(2)

with col1:
    airport_col = st.selectbox("Select the airport column:", all_columns)

with col2:
    cost_col = st.selectbox("Select the cost column:", numeric_columns)

# --------------------------------------------------
# Optional controls
# --------------------------------------------------
with st.expander("Optional filters"):
    top_n = st.slider("Number of airports to display:", min_value=5, max_value=20, value=10)

# --------------------------------------------------
# Prepare data
# --------------------------------------------------
data = df[[airport_col, cost_col]].dropna()

summary = data.groupby(airport_col).agg(
    strike_count=(cost_col, "count"),
    total_cost=(cost_col, "sum"),
    avg_cost=(cost_col, "mean")
).reset_index()

summary = summary.sort_values("total_cost", ascending=False).head(top_n)

# --------------------------------------------------
# A/B testing section
# --------------------------------------------------
st.subheader("A/B Testing Experiment")
st.write("Click the button below to display one of the two charts at random.")

if st.button("Show random chart"):
    st.session_state.chart_choice = random.choice(["A", "B"])
    st.session_state.start_time = time.time()

# --------------------------------------------------
# Show selected chart
# --------------------------------------------------
if st.session_state.chart_choice is not None:
    fig, ax = plt.subplots(figsize=(10, 6))

    if st.session_state.chart_choice == "A":
        st.write("### Chart A: Total cost by airport")
        sns.barplot(data=summary, x="total_cost", y=airport_col, ax=ax)
        ax.set_xlabel("Total Cost")
        ax.set_ylabel("Airport")

    else:
        st.write("### Chart B: Average cost per strike by airport")
        sns.barplot(data=summary, x="avg_cost", y=airport_col, ax=ax)
        ax.set_xlabel("Average Cost per Strike")
        ax.set_ylabel("Airport")

    plt.tight_layout()
    st.pyplot(fig)

    # --------------------------------------------------
    # Answer button
    # --------------------------------------------------
    if st.button("Did I answer your question?"):
        end_time = time.time()
        response_time = round(end_time - st.session_state.start_time, 2)

        st.success(f"You answered in {response_time} seconds.")

        st.session_state.results.append({
            "chart": st.session_state.chart_choice,
            "time_seconds": response_time
        })

        st.session_state.chart_choice = None
        st.session_state.start_time = None

# --------------------------------------------------
# Results section
# --------------------------------------------------
if len(st.session_state.results) > 0:
    st.subheader("Experiment Results")

    results_df = pd.DataFrame(st.session_state.results)

    col1, col2 = st.columns(2)

    with col1:
        st.write("Recorded responses:")
        st.dataframe(results_df)

    with col2:
        st.write("Average response time by chart:")
        avg_times = results_df.groupby("chart", as_index=False)["time_seconds"].mean()
        st.dataframe(avg_times)

# --------------------------------------------------
# Optional explanation section
# --------------------------------------------------
with st.expander("How this app works"):
    st.write(
        "This app uses A/B testing to compare two chart designs. "
        "When the user clicks 'Show random chart', the app randomly displays Chart A or Chart B. "
        "Then the app measures how long it takes until the user clicks "
        "'Did I answer your question?'. The goal is to compare which chart helps users answer "
        "the business question more effectively."
    )
