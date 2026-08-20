import streamlit as st
import pandas as pd
from media.thumbnail_generator import generate_image_thumbnail

def render_media_gallery(media_df: pd.DataFrame, session_id: str):
    """
    Renders a responsive CSS grid gallery for images.
    """
    if media_df.empty:
        st.info("No images match the current filters.")
        return
        
    # Ensure we only process images
    images_df = media_df[media_df["media_type"] == "Image"]
    if images_df.empty:
        st.info("No images found.")
        return

    # Basic CSS for responsive grid
    st.markdown("""
        <style>
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            padding: 10px 0;
        }
        .gallery-item {
            aspect-ratio: 1;
            overflow: hidden;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            position: relative;
        }
        .gallery-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.2s;
        }
        .gallery-item img:hover {
            transform: scale(1.05);
        }
        .gallery-badge {
            position: absolute;
            bottom: 5px;
            right: 5px;
            background: rgba(0,0,0,0.6);
            color: white;
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # We will use Streamlit columns to render images side by side if HTML isn't enough,
    # but Streamlit's native st.image inside columns is often easier to click and preview.
    
    cols_per_row = 5
    for i in range(0, len(images_df), cols_per_row):
        row_cols = st.columns(cols_per_row)
        for j, col in enumerate(row_cols):
            if i + j < len(images_df):
                row = images_df.iloc[i + j]
                thumb_path = generate_image_thumbnail(session_id, row["relative_path"])
                
                if thumb_path:
                    with col:
                        # Use native st.image which supports native click-to-expand
                        st.image(thumb_path, caption=f"By: {row['sender']}", use_container_width=True)
