import pandas as pd
import streamlit as st
from urlextract import URLExtract
from utils.constants import OMITTED_MEDIA_MSG

extractor = URLExtract()

@st.cache_data(show_spinner=False)
def get_basic_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
        
    total_messages = len(df)
    total_users = df["users"].nunique()
    total_media = df[df["is_media"]].shape[0]
    
    # Count URLs
    total_links = df["user_messages"].apply(lambda x: len(extractor.find_urls(str(x))) > 0).sum()
    
    # Days active
    days_active = df["date_only"].nunique()
    avg_msg_per_day = total_messages / days_active if days_active > 0 else 0
    
    return {
        "total_messages": int(total_messages),
        "total_users": int(total_users),
        "total_media": int(total_media),
        "total_links": int(total_links),
        "avg_messages_per_day": float(avg_msg_per_day)
    }

@st.cache_data(show_spinner=False)
def calculate_response_times(df: pd.DataFrame) -> dict:
    if df.empty or "timestamp" not in df.columns:
        return {}
        
    df_sorted = df.sort_values(by="timestamp").reset_index(drop=True)
    
    # Shift users to detect reply
    df_sorted["prev_user"] = df_sorted["users"].shift(1)
    df_sorted["time_diff"] = df_sorted["timestamp"].diff().dt.total_seconds()
    
    # A valid reply is when the user is different from the previous user
    # and the time gap is reasonable (e.g., less than 1 hour to exclude disjointed messages)
    replies = df_sorted[(df_sorted["users"] != df_sorted["prev_user"]) & (df_sorted["time_diff"] < 3600)].dropna()
    
    if replies.empty:
        return {}
        
    avg_response_time = replies["time_diff"].mean()
    fastest_response = replies["time_diff"].min()
    slowest_response = replies["time_diff"].max()
    
    # Per user average response time
    user_response_times = replies.groupby("users")["time_diff"].mean().to_dict()
    
    return {
        "avg_response_seconds": float(avg_response_time),
        "fastest_response_seconds": float(fastest_response),
        "slowest_response_seconds": float(slowest_response),
        "user_avg_response_seconds": user_response_times
    }

@st.cache_data(show_spinner=False)
def get_peak_session(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
        
    df = df.copy()
    # Group by Day Name and 2-hour windows (just integer divide by 2)
    # E.g. 20 -> 20:00 - 21:59
    df["2h_window"] = (df["hour"] // 2) * 2
    
    grouped = df.groupby(["day_name", "2h_window"]).size().reset_index(name="count")
    if grouped.empty:
        return {}
        
    peak_row = grouped.loc[grouped["count"].idxmax()]
    
    day = peak_row["day_name"]
    start_hr = peak_row["2h_window"]
    end_hr = start_hr + 2
    
    start_str = f"{start_hr}:00" if start_hr >= 10 else f"0{start_hr}:00"
    end_str = f"{end_hr}:00" if end_hr < 24 else "23:59"
    
    return {
        "day": str(day),
        "start_time": start_str,
        "end_time": end_str,
        "message_count": int(peak_row["count"]),
        "display_string": f"{day} {start_str} - {end_str}"
    }
