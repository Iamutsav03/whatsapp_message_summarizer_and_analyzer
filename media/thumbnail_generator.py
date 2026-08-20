import os
import hashlib
import re
import streamlit as st
from PIL import Image, UnidentifiedImageError
from config.media_settings import TEMP_MEDIA_DIR, THUMBNAIL_SIZE

def _cleanup_orphaned_thumbnails(thumbs_dir: str):
    """
    Scans the thumbnails directory and removes any legacy files matching 
    the old randomized hash naming scheme (e.g., thumb_123456789.jpg).
    """
    if not os.path.exists(thumbs_dir):
        return
    old_pattern = re.compile(r"^thumb_-?\d+\.jpg$")
    for file in os.listdir(thumbs_dir):
        if old_pattern.match(file):
            try:
                os.remove(os.path.join(thumbs_dir, file))
            except Exception:
                pass

@st.cache_data(show_spinner=False, max_entries=500)
def generate_image_thumbnail(session_id: str, relative_path: str) -> str:
    """
    Generates and returns the path to a thumbnail for a given image.
    Uses aggressive caching to prevent regenerating thumbnails on UI rerenders.
    """
    session_dir = os.path.join(TEMP_MEDIA_DIR, session_id)
    original_path = os.path.join(session_dir, relative_path)
    
    # Create thumbnails directory
    thumbs_dir = os.path.join(session_dir, ".thumbnails")
    
    # Run cleanup when the directory is first accessed/created
    if not os.path.exists(thumbs_dir):
        os.makedirs(thumbs_dir, exist_ok=True)
    else:
        _cleanup_orphaned_thumbnails(thumbs_dir)
        
    thumb_hash = hashlib.md5(relative_path.encode('utf-8')).hexdigest()
    thumb_filename = f"thumb_{thumb_hash}.jpg"
    thumb_path = os.path.join(thumbs_dir, thumb_filename)
    
    # Return existing thumbnail if already generated
    if os.path.exists(thumb_path):
        return thumb_path
        
    try:
        with Image.open(original_path) as img:
            # Convert to RGB (handles RGBA PNGs or CMYK)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(thumb_path, format="JPEG", quality=75)
            
        return thumb_path
    except (UnidentifiedImageError, OSError):
        # Fallback if image is corrupted
        return ""
