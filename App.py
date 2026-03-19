import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import StringIO
import time

# Configure page
st.set_page_config(page_title="Analysis Tool", layout="wide")
st.title("Analysis Tool")
st.write("**Team members:** Julian Harder, Ian Dromundo, Justin, Luuk van den Hoek, Alimzhan Shamshitov")

# Initialize session state
if 'df' not in st.session_state:
    st.session_state['df'] = None
if 'df_imputed' not in st.session_state:
    st.session_state['df_imputed'] = None
if 'question' not in st.session_state:
    st.session_state['question'] = ""
if 'ab_log' not in st.session_state:
    st.session_state['ab_log'] = []
if 'charts_generated' not in st.session_state:
    st.session_state['charts_generated'] = False
if 'chart_generation_time' not in st.session_state:
    st.session_state['chart_generation_time'] = None
if 'analysis_start_time' not in st.session_state:
    st.session_state['analysis_start_time'] = None

# Sidebar: File uploader
st.sidebar.header("📊 Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload CSV dataset", type=['csv'])

if uploaded_file is not None:
    st.session_state['df'] = pd.read_csv(uploaded_file)
    st.sidebar.success(f"✓ Dataset loaded: {st.session_state['df'].shape[0]} rows, {st.session_state['df'].shape[1]} columns")

    # Mean imputation
    st.session_state['df_imputed'] = st.session_state['df'].copy()
    numeric_cols = st.session_state['df_imputed'].select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        if st.session_state['df_imputed'][col].isnull().sum() > 0:
            mean_val = st.session_state['df_imputed'][col].mean()
            st.session_state['df_imputed'][col].fillna(mean_val, inplace=True)

    st.sidebar.info(f"✓ Mean imputation applied to numeric columns")

# Main content
if st.session_state['df_imputed'] is not None:
    df = st.session_state['df_imputed']
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # ===== QUESTION SECTION (TOP) =====
    st.subheader("❓ Step 1: Your Analysis Question")
    st.write("**What question are you trying to answer?**")

    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_area(
            "Enter your analysis question:",
            value=st.session_state['question'],
            placeholder="e.g., Is there a strong relationship between X and Y?",
            height=80,
            label_visibility="collapsed"
        )
        st.session_state['question'] = question

    with col2:
        if st.button("🗑️ Clear Question"):
            st.session_state['question'] = ""
            st.rerun()

    st.divider()

    # ===== VARIABLE SELECTION SECTION =====
    st.subheader("📊 Step 2: Select Variables")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Dependent Variable (Y-axis):**")
        dependent_var = st.selectbox(
            "What do you want to predict/analyze?",
            numeric_cols,
            key="dependent_select",
            label_visibility="collapsed"
        )

    with col2:
        st.write("**Independent Variable (X-axis):**")
        available_independent = [col for col in numeric_cols if col != dependent_var]
        if available_independent:
            independent_var = st.selectbox(
                "What is the explanatory variable?",
                available_independent,
                key="independent_select",
                label_visibility="collapsed"
            )
        else:
            st.warning("Not enough numeric features for comparison")
            independent_var = None

    st.divider()

    # ===== GENERATE CHARTS BUTTON =====
    st.subheader("📈 Step 3: Generate Analysis")

    # Validation
    has_question = st.session_state['question'].strip() != ""
    has_variables = dependent_var is not None and independent_var is not None

    if not has_question:
        st.warning("⚠️ Please enter a question first")
    if not has_variables:
        st.warning("⚠️ Please select both dependent and independent variables")

    if st.button(
        "🔍 Generate Charts",
        disabled=not (has_question and has_variables),
        use_container_width=True,
        type="primary"
    ):
        st.session_state['charts_generated'] = True
        st.session_state['analysis_start_time'] = time.time()
        st.rerun()

    # ===== DISPLAY CHARTS (ONLY AFTER BUTTON CLICK) =====
    if st.session_state['charts_generated'] and dependent_var and independent_var:
        st.divider()
        st.subheader("📊 Analysis Results")
        col1, col2 = st.columns(2)

        # Chart 1: Scatter plot with regression line
        with col1:
            st.write(f"**{dependent_var} vs {independent_var}**")
            # Create scatter plot with trend line
            fig1 = px.scatter(
                df,
                x=independent_var,
                y=dependent_var,
                trendline="ols",
                title=f"Regression Analysis",
                labels={independent_var: independent_var, dependent_var: dependent_var}
            )
            fig1.update_layout(height=500)
            st.plotly_chart(fig1, use_container_width=True)

        # Chart 2: Feature correlation ranking
        with col2:
            st.write(f"**Top Features Correlated with {dependent_var}**")

            # Calculate correlations
            correlations = df[numeric_cols].corr()[dependent_var].drop(dependent_var)
            correlations = correlations.abs().sort_values(ascending=False).head(10)

            # Create bar chart
            fig2 = px.bar(
                x=correlations.values,
                y=correlations.index,
                orientation='h',
                title=f"Feature Importance",
                labels={'x': 'Absolute Correlation', 'y': 'Feature'},
                color=correlations.values,
                color_continuous_scale='Viridis'
            )
            fig2.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        # A/B Testing Section
        st.divider()
        st.subheader("⏱️ Step 4: Feedback")

        # Display elapsed time
        if st.session_state['analysis_start_time'] is not None:
            elapsed_time = time.time() - st.session_state['analysis_start_time']
            st.metric("Time Analyzing Charts", f"{elapsed_time:.1f} seconds")

        # Feedback buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Yes, this answered my question", use_container_width=True, type="primary"):
                analysis_time = time.time() - st.session_state['analysis_start_time']
                session_data = {
                    'question': st.session_state['question'],
                    'dependent_var': dependent_var,
                    'independent_var': independent_var,
                    'answered': True,
                    'analysis_time_seconds': round(analysis_time, 2)
                }
                st.session_state['ab_log'].append(session_data)
                st.success("Thank you! Your feedback has been recorded.")
                st.session_state['charts_generated'] = False
                st.session_state['question'] = ""
                st.session_state['analysis_start_time'] = None
                st.rerun()

        with col2:
            if st.button("❌ No, this didn't answer my question", use_container_width=True):
                analysis_time = time.time() - st.session_state['analysis_start_time']
                session_data = {
                    'question': st.session_state['question'],
                    'dependent_var': dependent_var,
                    'independent_var': independent_var,
                    'answered': False,
                    'analysis_time_seconds': round(analysis_time, 2)
                }
                st.session_state['ab_log'].append(session_data)
                st.info("We'll work on improving the analysis.")
                st.session_state['charts_generated'] = False
                st.session_state['question'] = ""
                st.session_state['analysis_start_time'] = None
                st.rerun()

    # A/B Testing Results Summary (shown all the time if there's data)
    if len(st.session_state['ab_log']) > 0:
        st.divider()
        st.subheader("📊 Feedback Summary")

        log_df = pd.DataFrame(st.session_state['ab_log'])

        # Calculate metrics
        total_feedback = len(log_df)
        answered_yes = (log_df['answered'] == True).sum()
        answered_no = (log_df['answered'] == False).sum()
        success_rate = (answered_yes / total_feedback * 100) if total_feedback > 0 else 0
        avg_time = log_df['analysis_time_seconds'].mean()

        # Display metrics
        metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
        with metric_col1:
            st.metric("Total Feedback", total_feedback)
        with metric_col2:
            st.metric("Questions Answered", answered_yes)
        with metric_col3:
            st.metric("Questions Not Answered", answered_no)
        with metric_col4:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with metric_col5:
            st.metric("Avg Analysis Time", f"{avg_time:.1f}s")

        # Detailed feedback table
        st.write("**Recent Feedback:**")
        display_cols = ['question', 'dependent_var', 'independent_var', 'answered', 'analysis_time_seconds']
        st.dataframe(
            log_df[display_cols].rename(columns={
                'question': 'Question',
                'dependent_var': 'Dependent Variable',
                'independent_var': 'Independent Variable',
                'answered': 'Answered?',
                'analysis_time_seconds': 'Time (sec)'
            }),
            use_container_width=True,
            hide_index=True
        )

        # Visualization of feedback
        feedback_chart = px.pie(
            values=[answered_yes, answered_no],
            names=['✅ Answered', '❌ Not Answered'],
            title='Question Response Rate',
            color_discrete_map={'✅ Answered': '#00CC96', '❌ Not Answered': '#EF553B'}
        )
        st.plotly_chart(feedback_chart, use_container_width=True)

else:
    st.info("👈 Upload a CSV dataset to get started")
    st.write("""
    ### How to use this Analysis Tool:
    1. **Upload Data** - Click the file uploader on the left to upload your CSV file
    2. **Ask a Question** - Enter the question you want to answer with data analysis
    3. **Select Variables** - Choose your dependent and independent variables
    4. **Generate Charts** - Click the button to create regression and importance charts
    5. **View Results** - See the relationship between variables and feature importance
    6. **Provide Feedback** - Let us know if the charts answered your question (time tracked!)
    """)

