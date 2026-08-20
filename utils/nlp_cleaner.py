"""
Global NLP Preprocessing Layer — Phase 2.5

Runs BEFORE every NLP task (Word Cloud, Topic Model, Sentiment, AI Summary).
Removes WhatsApp export artifacts, file patterns, system messages, numbers,
URLs, and common filler words before any text analysis.
"""

import re
import streamlit as st
from functools import lru_cache

# ── WhatsApp Media Artifact Words ─────────────────────────────────────────────
_MEDIA_ARTIFACTS: set = {
    "attached", "file", "media", "omitted", "image", "video", "audio",
    "document", "sticker", "gif", "jpg", "jpeg", "png", "webp", "heic",
    "mp4", "avi", "mov", "opus", "m4a", "mp3", "ogg", "pdf", "doc",
    "docx", "ppt", "pptx", "vcf", "apk", "csv", "zip", "txt",
    "null", "undefined"
}

# ── WhatsApp System Message Patterns ─────────────────────────────────────────
_SYSTEM_PATTERNS: list = [
    r"messages and calls are end-to-end encrypted",
    r"this message was deleted",
    r"you deleted this message",
    r"security code changed",
    r"group icon changed",
    r"group description changed",
    r"group created",
    r"added .+",
    r"removed .+",
    r"joined using this group.s invite link",
    r"missed voice call",
    r"missed video call",
    r"you.re now an admin",
    r"changed the subject",
    r"changed the group description",
    r"pinned a message",
]
_SYSTEM_RE = re.compile(
    "|".join(_SYSTEM_PATTERNS), flags=re.IGNORECASE
)

# ── File Name Patterns (IMG-..., VID-..., Screenshot_...) ────────────────────
_FILENAME_RE = re.compile(
    r"\b(IMG|VID|AUD|DOC|PTT|PXL|PHOTO|VIDEO|AUDIO|STK|GIF|Screenshot|DSC|DCIM)"
    r"[-_]\d{4,}[-_\w]*\b",
    flags=re.IGNORECASE
)

# ── URL / Phone / Number Patterns ─────────────────────────────────────────────
_URL_RE       = re.compile(r"https?://\S+|www\.\S+")
_PHONE_RE     = re.compile(r"\+?[\d\s\-\(\)]{9,15}")
_NUMERIC_RE   = re.compile(r"\b\d+\b")

# ── Emoji / Special chars ─────────────────────────────────────────────────────
_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)


@st.cache_data(show_spinner=False)
def load_stopwords() -> set:
    """Loads and merges: English sklearn stopwords + Hinglish file."""
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

    base = set(ENGLISH_STOP_WORDS)
    base |= _MEDIA_ARTIFACTS

    try:
        with open("hinglish.txt", "r", encoding="utf-8") as f:
            hinglish = {w.strip().lower() for w in f if w.strip()}
        base |= hinglish
    except FileNotFoundError:
        pass

    return base


def is_system_message(text: str) -> bool:
    """Returns True if the message is a WhatsApp system notification."""
    return bool(_SYSTEM_RE.search(text))


def clean_message(text: str, stopwords: set) -> str:
    """
    Applies the full artifact-removal pipeline to a single message.
    Returns a clean string ready for NLP.
    """
    # 1. Drop URLs
    text = _URL_RE.sub(" ", text)
    # 2. Drop file name patterns
    text = _FILENAME_RE.sub(" ", text)
    # 3. Drop phone numbers
    text = _PHONE_RE.sub(" ", text)
    # 4. Drop remaining numbers
    text = _NUMERIC_RE.sub(" ", text)
    # 5. Lowercase
    text = text.lower()
    # 6. Remove punctuation
    text = _PUNCT_RE.sub(" ", text)
    # 7. Tokenise & remove stopwords / artifacts
    tokens = [t for t in text.split() if t not in stopwords and len(t) > 2]
    return " ".join(tokens)


import pandas as pd

@st.cache_data(show_spinner=False)
def get_clean_corpus(df: pd.DataFrame) -> tuple:
    """
    Applies the full cleaning pipeline to the entire DataFrame.
    Returns:
        clean_texts: list[str]  — one cleaned string per valid message
        joined_text: str        — full corpus joined for Word Cloud
    """
    stopwords = load_stopwords()
    clean_texts = []

    for msg in df["user_messages"].dropna().astype(str):
        if is_system_message(msg):
            continue
        cleaned = clean_message(msg, stopwords)
        if cleaned.strip():
            clean_texts.append(cleaned)

    return clean_texts, " ".join(clean_texts)
