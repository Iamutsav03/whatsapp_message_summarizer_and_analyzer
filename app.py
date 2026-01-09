import streamlit as st
import pandas as pd
from preprocessor import preprocess , processed_data_for_wordCloud ,  processed_data_for_timeliine
from analysis import (
    most_active_users,
    Link_count,
    generate_word_cloud,
    emoji_analysis,
    prepare_emoji_pie_data,
    most_active_months,
    most_active_dayName,
    most_active_years
    
)
from requirements import year_hbar_chart , month_line_chart ,dayname_bar_chart
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import plotly.express as px


st.set_page_config(page_title="WhatsApp Chat Analyzer", layout="wide")

st.title("📊 WhatsApp Chat Analyzer")

uploaded_file = st.file_uploader(
    "Upload WhatsApp chat file (.txt)",
    type=["txt"]
)

df = None

if uploaded_file is not None:
    bytes_data = uploaded_file.read()
    chat_text = bytes_data.decode("utf-8")

    df = preprocess(chat_text)

    st.success("File processed successfully!")



if df is not None:
    st.sidebar.header("🔍 Analysis Options")

    users_list = sorted(df["users"].unique().tolist())
    users_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox("Select User", users_list)
    
    if selected_user == "Overall":
        filtered_df = df
    else:
        filtered_df = df[df['users'] == selected_user]


if df is not None:
    st.subheader("Chat Data Preview")
    st.dataframe(filtered_df)
    
    st.subheader("📌 Summary")
    col1, col2 , col3 , col4 = st.columns(4)

    with col1:
        st.metric("Total Messages", filtered_df.shape[0])

    with col2:
        st.metric("Total Users", filtered_df['users'].nunique())
    with col3:
        st.metric(
            "Media Shared", filtered_df[filtered_df["user_messages"] == "<Media omitted>"].shape[0],)
    with col4:
        st.metric("Link Shared", Link_count(filtered_df))


if df is not None:
    st.subheader("🔥 Most Active Users")

    if selected_user == "Overall":
        col1 , col2 = st.columns(2)
        with col1 :
            active_df = most_active_users(filtered_df , 10)
            st.dataframe(active_df)
        
        with col2 :
            x = active_df.head(5)
            st.bar_chart(data=x.set_index("User")["Contribution(%)"])
    else:
        user_count = filtered_df.shape[0]
        st.info(f"**{selected_user}** has sent **{user_count} messages**.")

if df is not None:
    st.subheader("TIMELINE ANALYSIS")
    time_df = processed_data_for_timeliine(filtered_df)
    col1 , col2 = st.columns(2)
    with col1:
        ma_dayname = most_active_dayName(time_df)
        ma_year = most_active_years(time_df)
        ma_months = most_active_months(time_df)
        st.altair_chart(month_line_chart(ma_months), use_container_width=True)
        st.altair_chart(year_hbar_chart(ma_year), use_container_width=True)
        st.altair_chart(dayname_bar_chart(ma_dayname), use_container_width=True)
    with col2:
        st.dataframe(ma_months)
        st.dataframe(ma_year)
        st.dataframe(ma_dayname)


if df is not None:
    st.subheader("MOST USED WORDS")
    clean_text, word_freq = processed_data_for_wordCloud(filtered_df)
    fig = generate_word_cloud(clean_text)
    st.pyplot(fig)

    word_freq_df = pd.DataFrame(
        word_freq.items(), columns=["Word", "Count"]
    ).sort_values(by="Count", ascending=False)
    word_freq_df = word_freq_df.head(15)

    fig, ax = plt.subplots(figsize=(8, 4))

    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    ax.barh(word_freq_df["Word"], word_freq_df["Count"], color="#87CEFA")
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    st.pyplot(fig)

    if df is not None:
        st.subheader("Top Emojis")

        col1, col2 = st.columns(2)

        with col1:
            emoji_df = emoji_analysis(filtered_df).head(10)
            st.dataframe(emoji_df)

        with col2:
            pie_df = prepare_emoji_pie_data(emoji_df, top_n=6)

            fig = px.pie(
                pie_df,
                values="COUNT",
                names="EMOJI",
                hole=0.4,  
                color_discrete_sequence=[
                    "#4DA6FF",  
                    "#FF9F43",  
                    "#2ECC71",  
                    "#E74C3C",  
                    "#9B59B6",  
                    "#95A5A6",  
                ],
            )
            fig.update_traces(textinfo="percent", textfont_color="white")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                legend_title_text="Emojis",
            )

            st.plotly_chart(fig, use_container_width=True)
