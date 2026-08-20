import os
import pandas as pd
from media.metadata import extract_file_metadata

def index_media_directory(session_dir: str) -> pd.DataFrame:
    """
    Recursively scans the extracted directory and builds a deterministic
    metadata DataFrame. Does NOT open or process the file contents.
    """
    files_data = []
    
    for root, _, files in os.walk(session_dir):
        for file in files:
            # Skip the chat txt file itself in the media index
            if file.endswith('.txt') and ("chat" in file.lower() or "whatsapp" in file.lower()):
                continue
                
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, session_dir)
            
            metadata = extract_file_metadata(filepath, rel_path)
            files_data.append(metadata)
            
    df = pd.DataFrame(files_data)
    return df

def link_media_to_chat(media_df: pd.DataFrame, chat_df: pd.DataFrame) -> pd.DataFrame:
    """
    Attempts to link extracted media files to their sender and timestamp
    based on the chat history (e.g. matching filenames often found in the text).
    """
    if media_df.empty or chat_df.empty:
        return media_df
        
    # Standard WhatsApp exports often mention the filename in the text: 
    # "IMG-20230101-WA0001.jpg (file attached)" or similar.
    # We will do a fast mapping if the filename exists in the message.
    
    # Create a quick lookup from filename to message metadata
    # (Taking the first occurrence to avoid duplicates)
    chat_media = chat_df[chat_df["user_messages"].str.contains(r"\.\w{3,4}\s", regex=True, na=False)]
    
    for idx, row in media_df.iterrows():
        fname = row["filename"]
        # Find matches in chat
        match = chat_media[chat_media["user_messages"].str.contains(fname, regex=False)]
        if not match.empty:
            media_df.at[idx, "sender"] = match.iloc[0]["users"]
            media_df.at[idx, "timestamp"] = match.iloc[0]["timestamp"]
            
    return media_df
