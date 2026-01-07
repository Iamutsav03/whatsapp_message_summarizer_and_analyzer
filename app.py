import streamlit as st
import pandas as pd
from preprocessor import preprocess
from analysis import most_active_users, Link_count
import matplotlib.pyplot as plt


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

    st.subheader("Chat Data Preview")
    st.dataframe(df)


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

    # st.subheader("📅 Daily Message Timeline")
    # timeline_df = daily_timeline(filtered_df)
    # fig, ax = plt.subplots()
    # ax.plot(timeline_df["date"], timeline_df["messages"])
    # ax.set_xlabel("Date")
    # ax.set_ylabel("Messages")
    # ax.set_title("Daily Message Trend")

    # st.pyplot(fig)
