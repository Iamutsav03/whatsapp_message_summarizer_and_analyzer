import json
import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from config.settings import GEMINI_API_KEY, AI_MODEL_NAME

def generate_media_summary(chat_summary: str, ai_results_df: pd.DataFrame) -> str:
    """
    Generates an overarching media summary combining chat analytics
    and Gemini Vision AI classification results.
    """
    if not GEMINI_API_KEY:
        return "[!] Gemini API key required for AI summaries."
    
    if ai_results_df.empty:
        return "No AI classification results available. Run AI media analysis first."
    
    category_dist = ai_results_df["category"].value_counts().to_dict()
    
    context = {
        "total_images_analyzed": len(ai_results_df),
        "category_distribution": category_dist,
        "top_category": max(category_dist, key=category_dist.get) if category_dist else "N/A",
    }
    
    prompt = f"""
You are an expert WhatsApp chat data analyst.
Based on the media analysis results below, write a concise executive summary (3-4 sentences max) describing
the visual nature of this chat. Focus on what types of content are commonly shared. Be insightful, not just descriptive.

Media Analysis Results (JSON):
{json.dumps(context, indent=2)}

Return plain text only. No markdown headers.
"""
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=AI_MODEL_NAME,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"[Error] Media summary failed: {str(e)}"


def render_ai_results_panel(ai_results_df: pd.DataFrame):
    """Renders charts and insights from the AI classification results."""
    if ai_results_df.empty:
        return
    
    st.markdown("#### AI Classification Results")
    
    col1, col2 = st.columns(2)
    with col1:
        # Category distribution
        cat_counts = ai_results_df["category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig = px.pie(cat_counts, values="Count", names="Category", hole=0.5,
                     color_discrete_sequence=px.colors.sequential.Greens_r)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Category bar
        fig = px.bar(cat_counts, x="Category", y="Count",
                     color="Count", color_continuous_scale="Greens")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="white"), margin=dict(l=20, r=20, t=20, b=60))
        st.plotly_chart(fig, use_container_width=True)
    
    # Per-sender breakdown
    if "sender" in ai_results_df.columns:
        st.markdown("#### Category by Sender")
        sender_cat = ai_results_df.groupby(["sender", "category"]).size().reset_index(name="count")
        fig = px.bar(sender_cat, x="sender", y="count", color="category",
                     barmode="stack", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="white"), xaxis_title="Sender", yaxis_title="Count",
                          margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Show results table
    with st.expander("View Raw Classification Data"):
        st.dataframe(ai_results_df[["filename", "sender", "category", "confidence", "description", "ocr_text"]])
