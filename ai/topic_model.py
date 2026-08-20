import json
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
from utils.nlp_cleaner import get_clean_corpus, load_stopwords

# ── Gemini Topic Naming ───────────────────────────────────────────────────────

def _name_topic_with_gemini(keywords: list) -> str:
    """
    Sends only the top keywords to Gemini and asks for a 2-3 word topic label.
    Never sends the full chat.
    """
    from config.settings import GEMINI_API_KEY, AI_MODEL_NAME
    from google import genai

    if not GEMINI_API_KEY:
        return ", ".join(keywords[:3]).title()

    prompt = f"""
Given these keywords extracted from a WhatsApp conversation, produce a short, human-readable topic label (2-4 words maximum). 
Return ONLY the label — no explanation, no punctuation.

Keywords: {", ".join(keywords)}
"""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        resp = client.models.generate_content(
            model=AI_MODEL_NAME,
            contents=prompt
        )
        return resp.text.strip()
    except Exception:
        return ", ".join(keywords[:2]).title()


# ── Core Topic Extraction ─────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def extract_topics(df: pd.DataFrame, n_topics: int = 5, n_top_words: int = 8) -> list:
    """
    Full artifact-free topic extraction pipeline:
      Clean → TF-IDF → NMF → Gemini Topic Naming
    """
    if df.empty:
        return []

    clean_texts, _ = get_clean_corpus(df)

    if len(clean_texts) < max(10, n_topics):
        return []

    try:
        stopwords = load_stopwords()
        tfidf = TfidfVectorizer(
            max_df=0.90,
            min_df=3,
            stop_words=list(stopwords),
            ngram_range=(1, 2),        # capture bigrams like "job interview"
            max_features=5000
        )
        matrix = tfidf.fit_transform(clean_texts)
        feature_names = tfidf.get_feature_names_out()

        nmf = NMF(n_components=n_topics, random_state=42, init="nndsvda", max_iter=500)
        nmf.fit(matrix)

        topics = []
        for idx, component in enumerate(nmf.components_):
            top_indices = component.argsort()[:-n_top_words - 1:-1]
            keywords = [feature_names[i] for i in top_indices]

            # Use Gemini only for labeling — not analysis
            label = _name_topic_with_gemini(keywords)

            topics.append({
                "topic_id": idx + 1,
                "name": label,
                "keywords": keywords,
            })

        return topics

    except Exception as e:
        print(f"Topic extraction failed: {e}")
        return []


# ── Monthly Topic Breakdown ───────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def extract_monthly_topics(df: pd.DataFrame, n_topics: int = 3) -> list:
    """
    Extracts the dominant topics PER MONTH.
    Returns a list of dicts: {month_label, topics[]}
    """
    if df.empty or "month_name" not in df.columns:
        return []

    results = []
    grouped = df.groupby(["year", "month"])

    for (year, month), group in grouped:
        if len(group) < 30:          # skip sparse months
            continue
        month_name = group["month_name"].iloc[0]
        topics = extract_topics(group, n_topics=n_topics, n_top_words=5)
        if topics:
            results.append({
                "period": f"{month_name} {year}",
                "year": int(year),
                "month": int(month),
                "topics": topics,
            })

    return sorted(results, key=lambda x: (x["year"], x["month"]))
