import os
from config.media_settings import (
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_VIDEO_FORMATS,
    SUPPORTED_AUDIO_FORMATS,
    SUPPORTED_DOC_FORMATS
)

def get_media_category(ext: str) -> str:
    """Categorizes a file based on its extension."""
    ext = ext.lower()
    if ext in SUPPORTED_IMAGE_FORMATS:
        return "Image"
    elif ext in SUPPORTED_VIDEO_FORMATS:
        return "Video"
    elif ext in SUPPORTED_AUDIO_FORMATS:
        return "Audio"
    elif ext in SUPPORTED_DOC_FORMATS:
        return "Document"
    return "Unknown"

def extract_file_metadata(filepath: str, relative_path: str) -> dict:
    """Extracts basic OS-level metadata for a file."""
    stat = os.stat(filepath)
    ext = os.path.splitext(filepath)[1].lower()
    
    return {
        "filename": os.path.basename(filepath),
        "relative_path": relative_path,
        "extension": ext,
        "size_bytes": stat.st_size,
        "media_type": get_media_category(ext),
        # These will be enriched by the text parser later if a match is found
        "sender": "Unknown",
        "timestamp": None,
        "ai_labels": [],
        "ocr_text": ""
    }
