import re
import pandas as pd
import streamlit as st
from utils.constants import WHATSAPP_PATTERNS

@st.cache_data(show_spinner=False)
def parse_chat_text(chat_text: str) -> pd.DataFrame:
    """
    Parses raw WhatsApp chat text into a Pandas DataFrame.
    Gracefully ignores lines that don't match standard WhatsApp formatting.
    """
    messages = []
    
    # Split by newlines, handling both \r\n and \n
    lines = chat_text.splitlines()
    
    for line in lines:
        match = None
        for pattern in WHATSAPP_PATTERNS:
            match = pattern.match(line)
            if match:
                break
                
        if match:
            date, time, user, message = match.groups()
            messages.append([date, time, user.strip(), message.strip()])
        else:
            # Multi-line message continuation
            if messages:
                # Append to the last message content
                messages[-1][3] += f"\n{line.strip()}"

    # Create base DataFrame
    df = pd.DataFrame(messages, columns=["date", "time", "users", "user_messages"])
    
    # 1-indexed for better display if needed
    df.index = df.index + 1
    
    return df

# Inline self-test blocks for verification
if __name__ == "__main__":
    test_strings = [
        "12/03/24, 15:30 - Alice: Hello there!",
        "12/03/24, 3:30 PM - Bob: Hi PM!",
        "12/03/24, 3:30 pm - Charlie: Hi lowercase pm!",
        "[12/03/24, 15:30:45] David: Bracketed 24h",
        "[12/03/24, 3:30:45 PM] Emma: Bracketed 12h",
        "12-03-2024, 15:30 - Frank: Hyphen date",
    ]
    
    test_corpus = "\n".join(test_strings)
    parsed_df = parse_chat_text.__wrapped__(test_corpus)  # Use __wrapped__ to bypass Streamlit cache during raw script runs
    print("Testing parser robustness:")
    print(parsed_df)
    assert len(parsed_df) == 6, f"Expected 6 rows, got {len(parsed_df)}"
    print("All parser self-tests passed successfully!")
