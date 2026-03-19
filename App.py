import streamlit as st
import pandas as pd
import plotly.express as px
import random
import time

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(page_title="A/B Testing Analysis Tool", layout="wide")
st.title("A/B Testing Analysis Tool")

# --------------------------------------------------
# Session state
# --------------------------------------------------
if "df" not in st.session_state:
    st.session_state["df"] = None
if "business_question" not in st.session_state:
    st.session_state["business_question"] = ""
if "chart_choice" not in st.session_state:
    st.session_state["chart_choice"] = None
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "ab_log" not in st.session_state:
    st.session_state["ab_log"] = []

# --------------------------------------------------
# Load uploaded CSV
# --------------------------------------------------
@st.cache_data
def load_data(file):
    return pd.read_csv(file)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.header("📁 Data Upload")
    uploaded_file = st.file_uploader("Upload CSV dataset", type=["csv"])

if uploaded_file is None:
    st.info("👈 Upload a CSV dataset in the sidebar to get started.")
    st.stop()

df = load_data(uploaded_file)
st.session_state["df"] = df

# --------------------------------------------------
# Business question logic
# --------------------------------------------------
uploaded_name = uploaded_file.name.lower()

if uploaded_name == "birdstrikes.csv":
    business_question = (
        "Which airports have the highest financial risk from bird strikes, "
        "so airlines should prioritize extra insurance coverage or higher coverage limits there?"
    )
else:
    business_question = st.text_input(
        "Enter your business question:",
        value=st.session_state["business_question"],
        placeholder="Write the business question you want the charts to answer"
    )
    st.session_state["business_question"] = business_question

# --------------------------------------------------
# Dataset preview
# --------------------------------------------------
with st.container():
    st.subheader("Dataset Preview")

    col1, col2 = st.columns(2)

    with col1:
        st.write("First rows:")
        st.dataframe(df.head())

    with col2:
        st.write("Shape:", df.shape)
        st.write("Columns:", list(df.columns))

# --------------------------------------------------
# Show question
# --------------------------------------------------
st.subheader("Business Question")
if business_question.strip():
    st.write(business_question)
else:
    st.warning("Please enter a business question to continue.")
    st.stop()

# --------------------------------------------------
# Variable selection
# --------------------------------------------------
numeric_cols = df.select_dtypes(include="number").columns.tolist()
all_cols = df.columns.tolist()

st.subheader("Select Variables")

col1, col2 = st.columns(2)

with col1:
    category_col = st.selectbox("Select category variable:", all_cols)

with col2:
    value_col = st.selectbox("Select numeric variable:", numeric_cols)

with st.expander("Optional settings"):
    top_n = st.slider("Number of categories to show", min_value=5, max_value=20, value=10)

# --------------------------------------------------
# Prepare aggregated data
# --------------------------------------------------
data = df[[category_col, value_col]].dropna()

summary = data.groupby(category_col).agg(
    total_value=(value_col, "sum"),
    average_value=(value_col, "mean"),
    count_value=(value_col, "count")
).reset_index()

summary = summary.sort_values("total_value", ascending=False).head(top_n)

# --------------------------------------------------
# A/B testing section
# --------------------------------------------------
st.subheader("A/B Testing")

st.write(
    "Click the button below to randomly display one of two charts. "
    "Then click the second button to record whether the chart answered the question."
)

if st.button("Show random chart"):
    st.session_state["chart_choice"] = random.choice(["A", "B"])
    st.session_state["start_time"] = time.time()

# --------------------------------------------------
# Show chart A or B randomly
# --------------------------------------------------
if st.session_state["chart_choice"] is not None:
    if st.session_state["chart_choice"] == "A":
        st.write("### Chart A: Total value by category")

        fig = px.bar(
            summary,
            x="total_value",
            y=category_col,
            orientation="h",
            title=f"Total {value_col} by {category_col}",
            labels={"total_value": f"Total {value_col}", category_col: category_col}
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.write("### Chart B: Average value by category")

        fig = px.bar(
            summary,
            x="average_value",
            y=category_col,
            orientation="h",
            title=f"Average {value_col} by {category_col}",
            labels={"average_value": f"Average {value_col}", category_col: category_col}
        )
        st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------
    # Feedback buttons
    # --------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Did I answer your question?"):
            response_time = round(time.time() - st.session_state["start_time"], 2)

            st.session_state["ab_log"].append({
                "question": business_question,
                "chart": st.session_state["chart_choice"],
                "answered": "Yes",
                "time_seconds": response_time
            })

            st.success(f"Feedback recorded. Response time: {response_time} seconds.")
            st.session_state["chart_choice"] = None
            st.session_state["start_time"] = None

    with col2:
        if st.button("❌ No, this did not answer my question"):
            response_time = round(time.time() - st.session_state["start_time"], 2)

            st.session_state["ab_log"].append({
                "question": business_question,
                "chart": st.session_state["chart_choice"],
                "answered": "No",
                "time_seconds": response_time
            })

            st.info(f"Feedback recorded. Response time: {response_time} seconds.")
            st.session_state["chart_choice"] = None
            st.session_state["start_time"] = None

# --------------------------------------------------
# Results
# --------------------------------------------------
if len(st.session_state["ab_log"]) > 0:
    st.divider()
    st.subheader("A/B Testing Results")

    log_df = pd.DataFrame(st.session_state["ab_log"])
    st.dataframe(log_df, use_container_width=True, hide_index=True)

    summary_results = (
        log_df.groupby("chart")
        .agg(
            responses=("chart", "count"),
            avg_time=("time_seconds", "mean")
        )
        .reset_index()
    )

    st.write("### Average response time by chart")
    st.dataframe(summary_results, use_container_width=True, hide_index=True)

# --------------------------------------------------
# Explanation
# --------------------------------------------------
with st.expander("How this app works"):
    st.write(
        "The app lets the user upload a CSV file and choose variables for analysis. "
        "If the uploaded file is birdstrikes.csv, the app automatically shows the predefined "
        "bird strike business question. Otherwise, the user enters a custom business question. "
        "The app then uses A/B testing: when the user clicks the button, it randomly shows "
        "Chart A or Chart B. After that, the user indicates whether the chart answered the question. "
        "The app records the chart shown and the response time."
    )
