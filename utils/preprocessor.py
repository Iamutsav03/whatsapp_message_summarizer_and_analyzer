import pandas as pd
import streamlit as st
from utils.constants import OMITTED_MEDIA_MSG

@st.cache_data(show_spinner=False)
def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and enhances the raw DataFrame with datetime features.
    """
    if df.empty:
        return df
        
    df_clean = df.copy()
    
    # Combine date and time for robust datetime parsing
    df_clean["datetime_str"] = df_clean["date"] + " " + df_clean["time"]
    
    # Parse to datetime (handling different formats gracefully)
    df_clean["timestamp"] = pd.to_datetime(
        df_clean["datetime_str"], 
        format="%d/%m/%y %H:%M",
        errors='coerce' # Fallback if format is different
    )
    
    # Fill any NaNs by attempting a fallback generic parser
    mask = df_clean["timestamp"].isna()
    if mask.any():
        df_clean.loc[mask, "timestamp"] = pd.to_datetime(
            df_clean.loc[mask, "datetime_str"],
            dayfirst=True,
            errors='coerce'
        )

    # Drop the temporary string column
    df_clean.drop(columns=["datetime_str"], inplace=True)
    
    # Extract rich time features
    df_clean["date_only"] = df_clean["timestamp"].dt.date
    df_clean["year"] = df_clean["timestamp"].dt.year
    df_clean["month"] = df_clean["timestamp"].dt.month
    df_clean["month_name"] = df_clean["timestamp"].dt.month_name()
    df_clean["day"] = df_clean["timestamp"].dt.day
    df_clean["day_name"] = df_clean["timestamp"].dt.day_name()
    df_clean["hour"] = df_clean["timestamp"].dt.hour
    df_clean["minute"] = df_clean["timestamp"].dt.minute
    
    # Add a flag for media messages
    df_clean["is_media"] = df_clean["user_messages"] == OMITTED_MEDIA_MSG
    
    # Sort chronologically just in case
    df_clean = df_clean.sort_values(by="timestamp").reset_index(drop=True)
    df_clean.index = df_clean.index + 1
    
    return df_clean
