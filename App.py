import streamlit as st
import pandas as pd
import plotly.express as px
import random
import time
from io import StringIO

# Configure page
st.set_page_config(page_title="Bird Strike Financial Risk", layout="wide")

# Initialize session state
if 'group' not in st.session_state:
    st.session_state['group'] = random.choice(['A', 'B'])
    st.session_state['chart_render_time'] = 0
    st.session_state['interactions'] = 0
    st.session_state['rating'] = None
    st.session_state['ab_log'] = []

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('birdstrikes (1).csv')
    return df

df = load_data()

# Sidebar
st.sidebar.markdown("## Bird Strike Financial Risk Analysis")
st.sidebar.info(
    "**Business Question:** Which airports have the highest financial risk from bird strikes, "
    "so airlines should prioritize extra insurance coverage or higher coverage limits there?"
)

# File uploader for additional data
uploaded_file = st.sidebar.file_uploader("Upload additional CSV dataset", type=['csv'])
if uploaded_file is not None:
    additional_df = pd.read_csv(uploaded_file)
    df = pd.concat([df, additional_df], ignore_index=True)

# Cost threshold slider
min_cost = st.sidebar.slider(
    "Minimum Total Cost ($)",
    min_value=0,
    max_value=int(df['Cost Total $'].max()),
    value=0,
    step=1000
)

# Insurance classification toggle
show_insurance = st.sidebar.checkbox("Show Insurance Classification", value=False)

# Number of airports to display
num_airports = st.sidebar.slider(
    "Number of Airports to Display",
    min_value=5,
    max_value=min(30, len(df.groupby('Airport Name'))),
    value=15
)

# Filter data
df_filtered = df[df['Cost Total $'] >= min_cost].copy()

# Fill NaN damage values with "None"
df_filtered['Effect Amount of damage'] = df_filtered['Effect Amount of damage'].fillna('None')

# Main area
st.title("Bird Strike Financial Risk by Airport")
st.info(
    "**Business Question:** Which airports have the highest financial risk from bird strikes, "
    "so airlines should prioritize extra insurance coverage or higher coverage limits there?"
)

# Show A/B group
col1, col2, col3 = st.columns([2, 1, 1])
with col2:
    st.caption(f"📊 You are in **Group {st.session_state['group']}**")

# Prepare data for charts
start_time = time.time()

# Group A: Total Cost Bar Chart
if st.session_state['group'] == 'A':
    # Aggregate by airport
    airport_cost = df_filtered.groupby('Airport Name')['Cost Total $'].sum().sort_values(ascending=False).head(num_airports)

    # Determine insurance threshold
    insurance_threshold = df_filtered.groupby('Airport Name')['Cost Total $'].sum().median()

    # Create color mapping
    if show_insurance:
        colors = ['green' if cost >= insurance_threshold else 'red' for cost in airport_cost.values]
    else:
        colors = 'lightblue'

    # Create chart
    fig = px.bar(
        x=airport_cost.values,
        y=airport_cost.index,
        orientation='h',
        title='Total Cost by Airport (Group A)',
        labels={'x': 'Total Cost ($)', 'y': 'Airport'},
        color=colors if show_insurance else None
    )

    if show_insurance:
        fig.update_traces(marker_color=colors)
    else:
        fig.update_traces(marker_color='lightblue')

    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Group B: Incident Type Stacked Bar Chart
else:
    # Aggregate by airport and damage type
    airport_damage = df_filtered.groupby(['Airport Name', 'Effect Amount of damage']).size().unstack(fill_value=0)

    # Get top N airports by total incidents
    top_airports = df_filtered.groupby('Airport Name').size().sort_values(ascending=False).head(num_airports).index
    airport_damage = airport_damage.loc[top_airports]

    # Prepare data for stacked bar
    chart_data = airport_damage.reset_index()
    chart_data = chart_data.melt(id_vars='Airport Name', var_name='Damage Level', value_name='Count')

    # Create chart
    color_map = {
        'None': '#90EE90',
        'Minor': '#FFD700',
        'Medium': '#FFA500',
        'Substantial': '#FF4500',
        'B': '#4169E1',
        'C': '#6A5ACD'
    }

    fig = px.bar(
        chart_data,
        y='Airport Name',
        x='Count',
        color='Damage Level',
        orientation='h',
        barmode='stack',
        title='Incident Count by Damage Severity (Group B)',
        labels={'Count': 'Number of Incidents', 'Airport Name': 'Airport'},
        color_discrete_map=color_map
    )

    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

# Track chart render time
chart_render_time = time.time() - start_time
st.session_state['chart_render_time'] = chart_render_time

# Interaction buttons
st.divider()
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("👍 Useful"):
        st.session_state['rating'] = 'useful'
        st.session_state['interactions'] += 1
        st.success("Thank you for your feedback!")

with col2:
    if st.button("👎 Not Useful"):
        st.session_state['rating'] = 'not_useful'
        st.session_state['interactions'] += 1
        st.info("We'll improve this visualization!")

with col3:
    if st.button("⭐ Clear Rating"):
        st.session_state['rating'] = None

# A/B Testing Results
st.divider()
st.subheader("A/B Testing Results")

# Log current session when rating is submitted
if st.session_state['rating'] is not None:
    session_log = {
        'group': st.session_state['group'],
        'rating': st.session_state['rating'],
        'interactions': st.session_state['interactions'],
        'chart_render_time': round(chart_render_time, 3)
    }

    # Add to log if not already present
    if session_log not in st.session_state['ab_log']:
        st.session_state['ab_log'].append(session_log)

# Calculate metrics for each group
if len(st.session_state['ab_log']) > 0:
    log_df = pd.DataFrame(st.session_state['ab_log'])

    # Group metrics
    metrics_by_group = []
    for group in ['A', 'B']:
        group_data = log_df[log_df['group'] == group]
        if len(group_data) > 0:
            useful_count = (group_data['rating'] == 'useful').sum()
            not_useful_count = (group_data['rating'] == 'not_useful').sum()
            total_ratings = useful_count + not_useful_count

            metrics_by_group.append({
                'Group': f'Group {group}',
                'Sessions': len(group_data),
                'Useful': useful_count,
                'Not Useful': not_useful_count,
                'Usefulness Rate': f"{(useful_count / total_ratings * 100):.1f}%" if total_ratings > 0 else "N/A",
                'Avg Interactions': f"{group_data['interactions'].mean():.1f}",
                'Avg Render Time (s)': f"{group_data['chart_render_time'].mean():.3f}"
            })

    if metrics_by_group:
        metrics_df = pd.DataFrame(metrics_by_group)
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
else:
    st.caption("No ratings yet. Rate a visualization above to start A/B testing.")

# Debug info (collapsible)
with st.expander("📋 Debug Info"):
    st.write(f"**Your Group:** {st.session_state['group']}")
    st.write(f"**Interactions:** {st.session_state['interactions']}")
    st.write(f"**Current Rating:** {st.session_state['rating']}")
    st.write(f"**Chart Render Time:** {chart_render_time:.3f}s")
    st.write(f"**Log Size:** {len(st.session_state['ab_log'])} sessions")
