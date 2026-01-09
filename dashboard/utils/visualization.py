"""
Chart generation utilities for dashboard.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict


def create_funnel_chart(variant_data: List[Dict]) -> go.Figure:
    """
    Create funnel chart for variant performance.
    
    Args:
        variant_data: List of variant performance dictionaries
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    for variant in variant_data[:5]:  # Top 5 variants
        fig.add_trace(go.Funnel(
            name=variant.get("variant_code", "Unknown")[:20],
            y=["Sent", "Replied", "Positive", "Booked", "Closed"],
            x=[
                100,
                variant.get("reply_rate", 0),
                variant.get("positive_reply_rate", 0),
                variant.get("booking_rate", 0),
                variant.get("close_rate", 0)
            ],
            textinfo="value+percent initial"
        ))
    
    fig.update_layout(
        title="Conversion Funnel by Variant",
        height=400
    )
    
    return fig


def create_time_series(date_data: pd.DataFrame) -> go.Figure:
    """
    Create time series line chart.
    
    Args:
        date_data: DataFrame with date column and metrics
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    if "reply_rate" in date_data.columns:
        fig.add_trace(go.Scatter(
            x=date_data["date"],
            y=date_data["reply_rate"],
            name="Reply Rate",
            mode="lines+markers"
        ))
    
    if "booking_rate" in date_data.columns:
        fig.add_trace(go.Scatter(
            x=date_data["date"],
            y=date_data["booking_rate"],
            name="Booking Rate",
            mode="lines+markers"
        ))
    
    fig.update_layout(
        title="Performance Over Time",
        xaxis_title="Date",
        yaxis_title="Rate (%)",
        height=300
    )
    
    return fig


def create_performance_bars(niche_data: pd.DataFrame) -> go.Figure:
    """
    Create performance bar chart for niches.
    
    Args:
        niche_data: DataFrame with niche performance metrics
        
    Returns:
        Plotly figure
    """
    fig = px.bar(
        niche_data,
        x="niche",
        y=["reply_rate", "booking_rate", "close_rate"],
        title="Performance by Niche",
        barmode="group",
        height=400
    )
    
    return fig

