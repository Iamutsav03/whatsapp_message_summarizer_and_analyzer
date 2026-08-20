import os
import random
import pandas as pd
import datetime
import streamlit as st
from ai.vision import GeminiVisionProvider, IMAGE_CATEGORIES
from config.media_settings import TEMP_MEDIA_DIR
from config.settings import GEMINI_API_KEY


def _sample_images(media_df: pd.DataFrame, strategy: str, max_count: int, sender_filter: str = None) -> pd.DataFrame:
    """Applies a sampling strategy to select images for AI analysis."""
    images = media_df[media_df["media_type"] == "Image"].copy()
    
    if sender_filter and sender_filter != "All":
        images = images[images["sender"] == sender_filter]
    
    if images.empty:
        return images
    
    if strategy == "Newest First":
        images = images.sort_values("timestamp", ascending=False)
    elif strategy == "Oldest First":
        images = images.sort_values("timestamp", ascending=True)
    elif strategy == "Largest Files":
        images = images.sort_values("size_bytes", ascending=False)
    else:  # Random Sample
        images = images.sample(frac=1, random_state=42)
    
    return images.head(max_count)


def run_ai_media_analysis(
    media_df: pd.DataFrame,
    session_id: str,
    strategy: str,
    max_images: int,
    sender_filter: str,
    enable_ocr: bool
) -> pd.DataFrame:
    """
    Runs Gemini Vision classification on sampled images.
    Results are returned as a DataFrame and should be cached in session_state by the caller.
    """
    vision = GeminiVisionProvider()
    if not vision.is_configured:
        st.error("Gemini API key is missing. Please configure your `.env` file.")
        return pd.DataFrame()
    
    sampled = _sample_images(media_df, strategy, max_images, sender_filter)
    if sampled.empty:
        st.warning("No images found after applying filters.")
        return pd.DataFrame()
    
    session_dir = os.path.join(TEMP_MEDIA_DIR, session_id)
    results = []
    
    progress = st.progress(0, text="Analyzing images with Gemini Vision...")
    total = len(sampled)
    
    for i, (_, row) in enumerate(sampled.iterrows()):
        filepath = os.path.join(session_dir, row["relative_path"])
        
        try:
            with open(filepath, "rb") as f:
                image_bytes = f.read()
            
            classification = vision.classify_image(image_bytes)
            ocr_text = ""
            if enable_ocr:
                ocr_text = vision.extract_text(image_bytes)
            
            results.append({
                "filename": row["filename"],
                "sender": row["sender"],
                "timestamp": row["timestamp"],
                "size_bytes": row["size_bytes"],
                "category": classification.get("category", "Other"),
                "confidence": classification.get("confidence", 0.0),
                "description": classification.get("description", ""),
                "ocr_text": ocr_text,
                "processed_at": datetime.datetime.utcnow().isoformat() + "Z"
            })
        except Exception as e:
            results.append({
                "filename": row["filename"],
                "sender": row["sender"],
                "timestamp": row["timestamp"],
                "size_bytes": row["size_bytes"],
                "category": "Error",
                "confidence": 0.0,
                "description": str(e),
                "ocr_text": "",
                "processed_at": datetime.datetime.utcnow().isoformat() + "Z"
            })
        
        progress.progress((i + 1) / total, text=f"Analyzing {i+1}/{total}: {row['filename']}")
    
    progress.empty()
    return pd.DataFrame(results)
