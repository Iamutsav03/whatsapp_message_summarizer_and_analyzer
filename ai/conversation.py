"""
Conversation / Session detection and enrichment — Phase 2.5

Detection logic is UNCHANGED (30-minute inactivity threshold).
This module adds rich per-session metadata: sentiment, keywords,
longest gap, and helper functions for AI titling/summaries.
"""

import json
import pandas as pd
import streamlit as st
from config.settings import CONVERSATION_GAP_MINUTES, GEMINI_API_KEY, AI_MODEL_NAME


# ── Detection (unchanged algorithm) ──────────────────────────────────────────

@st.cache_data(show_spinner=False)
def detect_conversations(df: pd.DataFrame) -> dict:
    """
    Splits the chat into distinct sessions based on a 30-minute inactivity threshold.
    Returns per-session metadata DataFrame + aggregate summary metrics.
    Detection algorithm is NOT modified — only metadata richness is added.
    """
    if df.empty or "timestamp" not in df.columns:
        return {}

    df = df.sort_values(by="timestamp").reset_index(drop=True)
    df["time_diff"] = df["timestamp"].diff()

    threshold = pd.Timedelta(minutes=CONVERSATION_GAP_MINUTES)
    is_new = (df["time_diff"] > threshold) | (df["time_diff"].isna())
    df["conv_id"] = is_new.cumsum()

    conversations = []

    for conv_id, group in df.groupby("conv_id"):
        start_time  = group["timestamp"].iloc[0]
        end_time    = group["timestamp"].iloc[-1]
        duration    = (end_time - start_time).total_seconds()
        starter     = group["users"].iloc[0]
        participants = group["users"].unique().tolist()
        msg_count   = len(group)

        # Per-session sentiment (avg VADER compound if already scored)
        avg_sentiment = float(group["sentiment_score"].mean()) \
            if "sentiment_score" in group.columns else 0.0

        # Representative message sample (for AI, up to 20 msgs, skip media/system)
        sample_msgs = [
            m for m in group["user_messages"].dropna().astype(str)
            if m != "<Media omitted>" and "This message was deleted" not in m
        ][:20]

        conversations.append({
            "conv_id":          int(conv_id),
            "start_time":       start_time,
            "end_time":         end_time,
            "duration_seconds": duration,
            "starter":          starter,
            "participants":     participants,
            "message_count":    msg_count,
            "avg_sentiment":    avg_sentiment,
            "sample_messages":  sample_msgs,
            # AI-generated fields — populated lazily
            "ai_title":         None,
            "ai_summary":       None,
        })

    conv_df = pd.DataFrame(conversations)
    total   = len(conv_df)

    # ── Silent gaps between sessions ─────────────────────────────────────────
    if total > 1:
        conv_df = conv_df.sort_values("start_time").reset_index(drop=True)
        conv_df["gap_before_seconds"] = (
            conv_df["start_time"] - conv_df["end_time"].shift(1)
        ).dt.total_seconds().fillna(0)
        longest_gap_row = conv_df.loc[conv_df["gap_before_seconds"].idxmax()]
        longest_gap_minutes = float(longest_gap_row["gap_before_seconds"] / 60)
        longest_gap_before  = str(longest_gap_row["start_time"].date())
    else:
        longest_gap_minutes = 0.0
        longest_gap_before  = "—"

    # ── Aggregate summary ─────────────────────────────────────────────────────
    avg_duration  = float(conv_df["duration_seconds"].mean() / 60) if total else 0
    avg_msgs      = float(conv_df["message_count"].mean()) if total else 0
    longest       = conv_df.loc[conv_df["duration_seconds"].idxmax()] if total else None
    shortest      = conv_df.loc[conv_df["duration_seconds"].idxmin()] if total else None
    most_active   = conv_df.loc[conv_df["message_count"].idxmax()] if total else None
    most_positive = conv_df.loc[conv_df["avg_sentiment"].idxmax()] if total else None
    most_negative = conv_df.loc[conv_df["avg_sentiment"].idxmin()] if total else None
    starters_dist = conv_df["starter"].value_counts(normalize=True).to_dict() if total else {}

    return {
        "total_conversations":    int(total),
        "avg_duration_minutes":   avg_duration,
        "avg_messages_per_conv":  avg_msgs,
        "longest_duration_minutes": float(longest["duration_seconds"] / 60) if longest is not None else 0,
        "longest_conv_messages":  int(longest["message_count"]) if longest is not None else 0,
        "shortest_duration_minutes": float(shortest["duration_seconds"] / 60) if shortest is not None else 0,
        "longest_gap_minutes":    longest_gap_minutes,
        "longest_gap_before":     longest_gap_before,
        "most_active_conv_id":    int(most_active["conv_id"]) if most_active is not None else None,
        "most_positive_conv_id":  int(most_positive["conv_id"]) if most_positive is not None else None,
        "most_negative_conv_id":  int(most_negative["conv_id"]) if most_negative is not None else None,
        "starters_distribution":  starters_dist,
        "raw_conversations_df":   conv_df,   # kept for timeline UI
    }


# ── AI per-session enrichment (lazy, cached in session_state) ────────────────

def _gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return ""
    from google import genai
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=AI_MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"


def generate_session_title(sample_messages: list, stats: dict) -> str:
    """
    Generates a short (2-4 word) human-readable title for a chat session.
    Sends ONLY sample messages and basic stats — never the full chat.
    """
    if not sample_messages:
        return "Chat Session"
    prompt = f"""
You are labelling a WhatsApp chat session. Given the sample messages below,
produce a short, human-readable title (2-4 words maximum).
Examples: "Placement Discussion", "Trip Planning", "Movie Night", "Coding Help"

Stats: duration={stats.get('duration_minutes', 0):.0f}min, messages={stats.get('message_count', 0)}
Sample messages:
{chr(10).join(f"- {m}" for m in sample_messages[:15])}

Return ONLY the title. No explanation. No quotes.
"""
    return _gemini(prompt) or "Chat Session"


def generate_session_summary(sample_messages: list, stats: dict) -> str:
    """
    Generates a 2-sentence summary of a single chat session.
    Sends ONLY that session's sample messages — never the full chat.
    """
    if not sample_messages:
        return "No summary available."
    mood = "positive" if stats.get("avg_sentiment", 0) > 0.05 else \
           "negative" if stats.get("avg_sentiment", 0) < -0.05 else "neutral"
    prompt = f"""
You are summarising a single WhatsApp chat session.

Stats:
- Duration: {stats.get('duration_minutes', 0):.0f} minutes
- Messages: {stats.get('message_count', 0)}
- Overall mood: {mood}

Sample messages from this session:
{chr(10).join(f"- {m}" for m in sample_messages[:20])}

Write a 2-sentence summary describing what this conversation was about and the general tone.
Be specific. Do not use generic phrases like "the conversation covered". Start directly with the topic.
"""
    return _gemini(prompt) or "No summary available."
