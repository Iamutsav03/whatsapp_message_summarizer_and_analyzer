import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import re

# ── Common Plotly layout ───────────────────────────────────────────────────────
def apply_plotly_layout(fig, title: str = "") -> go.Figure:
    """Applies the standard dark-theme layout to any Plotly figure."""
    fig.update_layout(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FFFFFF", family="Inter, sans-serif"),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified",
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.1)")
    )
    fig.update_xaxes(showgrid=False, color="#A0AEC0", linecolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)", color="#A0AEC0")
    return fig


def _anonymize_phone(name: str) -> str:
    """Replaces raw phone numbers with 'Unknown Contact N' labels."""
    # Detects strings that look like phone numbers: +91 83182..., +44 7700...
    if re.match(r"^\+?[\d\s\-\(\)]{9,}$", name.strip()):
        return "Unknown Contact"
    return name


def _clean_sender_labels(series: pd.Series) -> pd.Series:
    """Vectorised phone-number anonymisation for a sender column."""
    counter = {}
    result = []
    for name in series:
        cleaned = _anonymize_phone(str(name))
        if cleaned == "Unknown Contact":
            counter[cleaned] = counter.get(cleaned, 0) + 1
            result.append(f"Unknown Contact {counter[cleaned]}")
        else:
            result.append(cleaned)
    return pd.Series(result, index=series.index)


# ── Chat activity charts ───────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def plot_monthly_activity(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    monthly = (
        df.groupby(["year", "month", "month_name"])
        .size()
        .reset_index(name="count")
        .sort_values(["year", "month"])
    )
    monthly["date_str"] = monthly["month_name"] + " " + monthly["year"].astype(str)
    fig = px.line(
        monthly, x="date_str", y="count", markers=True,
        color_discrete_sequence=["#25D366"],
        labels={"date_str": "Month", "count": "Messages"}
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    return apply_plotly_layout(fig, "Monthly Activity Trend")


@st.cache_data(show_spinner=False)
def plot_daily_activity(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    daily = df.groupby("date_only").size().reset_index(name="count")
    fig = px.area(
        daily, x="date_only", y="count",
        color_discrete_sequence=["#4299E1"],
        labels={"date_only": "Date", "count": "Messages"}
    )
    fig.update_traces(fillcolor="rgba(66,153,225,0.25)", line=dict(width=2))
    return apply_plotly_layout(fig, "Daily Activity Timeline")


@st.cache_data(show_spinner=False)
def plot_day_of_week_activity(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    counts = df["day_name"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["day_name", "count"]
    fig = px.bar(
        counts, x="day_name", y="count",
        color="count", color_continuous_scale="Greens",
        labels={"day_name": "Day", "count": "Messages"}
    )
    return apply_plotly_layout(fig, "Activity by Day of Week")


# ── Sentiment charts ───────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def plot_sentiment_distribution(counts: dict) -> go.Figure:
    labels = list(counts.keys())
    values = list(counts.values())
    color_map = {"Positive": "#25D366", "Neutral": "#A0AEC0", "Negative": "#F56565"}
    colors = [color_map.get(l, "#A0AEC0") for l in labels]
    fig = px.pie(values=values, names=labels, hole=0.6,
                 color_discrete_sequence=colors)
    fig.update_traces(textinfo="percent+label", textfont_color="white")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
    return fig


@st.cache_data(show_spinner=False)
def plot_sentiment_timeline(df: pd.DataFrame) -> go.Figure:
    if df.empty or "sentiment_score" not in df.columns:
        return go.Figure()
    daily = df.groupby("date_only")["sentiment_score"].mean().reset_index()
    fig = px.area(
        daily, x="date_only", y="sentiment_score",
        color_discrete_sequence=["#F6E05E"],
        labels={"date_only": "Date", "sentiment_score": "Avg Sentiment"}
    )
    fig.update_traces(fillcolor="rgba(246,224,94,0.15)", line=dict(width=2))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    return apply_plotly_layout(fig, "Sentiment Over Time")


# ── Media charts (improved, stacked, anonymised) ──────────────────────────────

@st.cache_data(show_spinner=False)
def plot_media_type_pie(media_df: pd.DataFrame) -> go.Figure:
    counts = media_df["media_type"].value_counts().reset_index()
    counts.columns = ["Type", "Count"]
    fig = px.pie(
        counts, values="Count", names="Type", hole=0.5,
        color_discrete_sequence=["#25D366", "#4299E1", "#F56565", "#F6E05E", "#9B59B6"]
    )
    fig.update_traces(textinfo="percent+label", textfont_color="white")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
    return fig


@st.cache_data(show_spinner=False)
def plot_media_stacked_by_sender(media_df: pd.DataFrame, top_n: int = 8) -> go.Figure:
    """Stacked bar chart: media type distribution per sender (phone numbers anonymised)."""
    df = media_df.copy()
    df["sender"] = _clean_sender_labels(df["sender"])

    top_senders = df["sender"].value_counts().head(top_n).index.tolist()
    df = df[df["sender"].isin(top_senders)]

    grouped = df.groupby(["sender", "media_type"]).size().reset_index(name="count")
    fig = px.bar(
        grouped, x="sender", y="count", color="media_type",
        barmode="stack",
        color_discrete_sequence=["#25D366", "#4299E1", "#F56565", "#F6E05E", "#9B59B6"],
        labels={"sender": "Sender", "count": "Files", "media_type": "Type"}
    )
    return apply_plotly_layout(fig, "Media Shared per Sender (by Type)")


@st.cache_data(show_spinner=False)
def plot_media_timeline(media_df: pd.DataFrame) -> go.Figure:
    """Monthly media volume over time."""
    df = media_df.dropna(subset=["timestamp"]).copy()
    if df.empty:
        return go.Figure()
    df["month"] = pd.to_datetime(df["timestamp"]).dt.to_period("M").astype(str)
    monthly = df.groupby(["month", "media_type"]).size().reset_index(name="count")
    fig = px.bar(
        monthly, x="month", y="count", color="media_type",
        barmode="stack",
        color_discrete_sequence=["#25D366", "#4299E1", "#F56565", "#F6E05E", "#9B59B6"],
        labels={"month": "Month", "count": "Files", "media_type": "Type"}
    )
    fig.update_layout(xaxis_tickangle=-45)
    return apply_plotly_layout(fig, "Media Volume Over Time")
