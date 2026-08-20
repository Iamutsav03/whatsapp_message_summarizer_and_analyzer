import json
import pandas as pd
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config.settings import SENTIMENT_THRESHOLD_POS, SENTIMENT_THRESHOLD_NEG, GEMINI_API_KEY, AI_MODEL_NAME

@st.cache_resource(show_spinner=False)
def get_vader_analyzer():
    return SentimentIntensityAnalyzer()


@st.cache_data(show_spinner=False)
def analyze_sentiment(df: pd.DataFrame) -> dict:
    """
    Classifies every message as Positive / Neutral / Negative using VADER.
    Returns enriched df + summary dict.
    """
    if df.empty:
        return {"summary": {}, "df": df}

    analyzer = get_vader_analyzer()

    df = df.copy()
    df["sentiment_score"] = df["user_messages"].apply(
        lambda x: analyzer.polarity_scores(str(x))["compound"] if pd.notnull(x) else 0
    )

    def categorize(score):
        if score >= SENTIMENT_THRESHOLD_POS:
            return "Positive"
        elif score <= SENTIMENT_THRESHOLD_NEG:
            return "Negative"
        return "Neutral"

    df["sentiment_label"] = df["sentiment_score"].apply(categorize)

    total = len(df)
    counts = df["sentiment_label"].value_counts().to_dict()
    avg_score = float(df["sentiment_score"].mean())

    if avg_score > 0.15:
        overall_mood = "Highly Positive"
    elif avg_score > 0.05:
        overall_mood = "Positive"
    elif avg_score < -0.15:
        overall_mood = "Highly Negative"
    elif avg_score < -0.05:
        overall_mood = "Negative"
    else:
        overall_mood = "Neutral"

    summary = {
        "overall_mood": overall_mood,
        "average_score": avg_score,
        "distribution": {
            "Positive": float(counts.get("Positive", 0) / total * 100),
            "Neutral":  float(counts.get("Neutral", 0)  / total * 100),
            "Negative": float(counts.get("Negative", 0) / total * 100),
        }
    }

    return {"summary": summary, "df": df}


# ── Daily Sentiment Drill-Down ────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def explain_daily_sentiment(df_day: pd.DataFrame, date_label: str) -> str:
    """
    Sends only the top representative messages from a single day to Gemini
    and asks for a concise reason for the observed sentiment.
    Never sends the full chat.
    """
    if not GEMINI_API_KEY:
        return "[!] Gemini API key required."

    from google import genai
    from utils.nlp_cleaner import is_system_message

    # Grab up to 30 actual messages from that day (not system messages)
    sample = [
        m for m in df_day["user_messages"].dropna().astype(str)
        if not is_system_message(m) and m != "<Media omitted>"
    ][:30]

    if not sample:
        return "No meaningful messages found for this day."

    avg_score = float(df_day["sentiment_score"].mean()) if "sentiment_score" in df_day.columns else 0
    mood = "positive" if avg_score > 0.05 else "negative" if avg_score < -0.05 else "neutral"

    prompt = f"""
You are a WhatsApp conversation analyst. Below is a sample of messages from {date_label}.
The overall sentiment computed for this day is: **{mood}** (score: {avg_score:.2f}).

Messages (sample):
{chr(10).join(f'- {m}' for m in sample)}

In 2-3 sentences, explain WHY the mood was {mood} that day. 
Focus on topics or events visible in the messages. Be specific, concise, and insightful.
Never say "the messages show" — just explain directly.
"""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        resp = client.models.generate_content(
            model=AI_MODEL_NAME,
            contents=prompt
        )
        return resp.text.strip()
    except Exception as e:
        return f"Could not generate explanation: {e}"
