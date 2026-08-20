import plotly.express as px
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from visualization.charts import apply_plotly_layout

@st.cache_data(show_spinner=False)
def plot_hourly_heatmap(df: pd.DataFrame):
    if df.empty:
        return go.Figure()
        
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = list(range(24))
    
    # Create full matrix
    full_index = pd.MultiIndex.from_product([days, hours], names=["day_name", "hour"])
    
    heatmap_data = (
        df.groupby(["day_name", "hour"])
        .size()
        .reindex(full_index, fill_value=0)
        .reset_index(name="count")
    )
    
    # Pivot for Plotly imshow
    pivot_df = heatmap_data.pivot(index="day_name", columns="hour", values="count").reindex(days)
    
    fig = px.imshow(
        pivot_df, 
        labels=dict(x="Hour of Day", y="Day of Week", color="Messages"),
        x=pivot_df.columns,
        y=pivot_df.index,
        color_continuous_scale="Greens"
    )
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FFFFFF"),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return fig
