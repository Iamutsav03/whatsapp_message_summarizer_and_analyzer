import streamlit as st
import base64
from typing import Dict, Any

def get_base64_of_bin_file(bin_file: str) -> str:
    """
    Reads a binary file and returns its base64 string.
    Useful for embedding images in custom CSS or HTML.
    """
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def format_number(num: int) -> str:
    """
    Formats large numbers nicely. e.g. 1500 -> 1.5K
    """
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    if num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

def build_structured_context(df, stats: Dict[str, Any], topics: list, sentiment: Dict[str, Any], conversations: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds the structured context object to be sent to Gemini.
    """
    chat_type = "personal" if stats["total_users"] == 2 else "group"
    
    # Strip non-serializable objects from conversations
    clean_conversations = {k: v for k, v in conversations.items() if k != "raw_conversations_df"}
    
    return {
        "chat_type": chat_type,
        "metrics": {
            "total_messages": stats.get("total_messages", 0),
            "total_users": stats.get("total_users", 0),
            "total_media": stats.get("total_media", 0),
            "total_links": stats.get("total_links", 0),
        },
        "conversations": clean_conversations,
        "topics": topics,
        "sentiment": sentiment,
        "peak_activity": stats.get("peak_session", "Unknown")
    }
