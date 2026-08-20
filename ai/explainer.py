"""
AI Explainer Module — Phase 2.5

Receives ONLY pre-computed structured statistics.
Never calculates. Only explains, contextualizes, and generates insights.
"""
import json
import streamlit as st
from config.settings import GEMINI_API_KEY, AI_MODEL_NAME


def _call_gemini(prompt: str) -> str:
    """Low-level Gemini call with graceful fallback."""
    if not GEMINI_API_KEY:
        return "[!] Gemini API key required to generate this explanation."
    from google import genai
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=AI_MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"[Error] Explanation failed: {e}"


# ── Chart Explainers ──────────────────────────────────────────────────────────

def explain_sentiment(sentiment_summary: dict) -> str:
    """Explains sentiment distribution in natural language."""
    prompt = f"""
You are a WhatsApp chat analyst. Explain the sentiment data below to a non-technical user in 2-3 sentences.
Answer: What is the overall mood? Why might that be the case? Is there anything interesting or notable?

Data:
{json.dumps(sentiment_summary, indent=2)}

Be direct. Do not use jargon. Do not repeat the numbers verbatim.
"""
    return _call_gemini(prompt)


def explain_activity_pattern(peak_session: dict, day_activity: dict) -> str:
    """Explains activity patterns — when the chat is most active and why."""
    prompt = f"""
You are a WhatsApp chat analyst. Explain the activity pattern below to a user in 2-3 sentences.
Focus on: When is the chat most active? What does this reveal about the group/person?

Peak session: {json.dumps(peak_session, indent=2)}
Day of week counts: {json.dumps(day_activity, indent=2)}

Be specific and insightful. Avoid restating numbers literally.
"""
    return _call_gemini(prompt)


def explain_topics(topics: list) -> str:
    """Explains what the main topics reveal about the conversation."""
    topic_names = [t["name"] for t in topics[:7]]
    prompt = f"""
You are a WhatsApp conversation analyst. The following topics were automatically detected.

Topics: {", ".join(topic_names)}

In 2-3 sentences, describe what these topics reveal about the nature of this chat — 
the interests, activities, or life events of the participants.
Be engaging and insightful, not robotic.
"""
    return _call_gemini(prompt)


def explain_conversation_stats(conv_stats: dict) -> str:
    """Explains conversation structure — depth, frequency, engagement."""
    clean = {k: v for k, v in conv_stats.items() if k != "raw_conversations_df"}
    prompt = f"""
You are a conversation analyst. Below are statistics about how conversations flow in this WhatsApp chat.

Data:
{json.dumps(clean, indent=2)}

In 2-3 sentences, interpret this data. Answer:
- How engaged are participants overall?
- Are conversations short bursts or deep discussions?
- Is there a dominant conversation starter?

Be warm and human. Do not list numbers.
"""
    return _call_gemini(prompt)


def generate_insight_cards(context: dict) -> list:
    """
    Generates 8-12 bullet-point insight cards from structured statistics.
    Returns a list of plain-text strings.
    """
    clean_ctx = {k: v for k, v in context.items()
                 if not isinstance(v, dict) or "raw_conversations_df" not in str(v)}

    prompt = f"""
You are an expert WhatsApp chat analyst generating smart, concise insights.

Structured analytics data (JSON):
{json.dumps(clean_ctx, indent=2)}

Generate exactly 10 insightful bullet points. Each must:
- Be a single sentence (max 15 words)
- Reveal something non-obvious or behavioural
- Avoid restating raw numbers verbatim
- Cover variety: activity patterns, sentiment, topics, response times, participation

Return ONLY a JSON array of strings. No markdown, no numbering.
Example format: ["Insight one.", "Insight two."]
"""
    result = _call_gemini(prompt)
    try:
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        return json.loads(result.strip())
    except Exception:
        # Fallback: split by newline
        return [l.strip("- •*1234567890. ") for l in result.splitlines() if l.strip()]
