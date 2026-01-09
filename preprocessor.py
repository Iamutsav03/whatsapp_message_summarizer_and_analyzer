from nltk.corpus import stopwords
import pandas as pd
import re
import numpy as np
from collections import Counter


with open('hinglish.txt' , 'r') as f:
    hinglish_words = set(word.strip().lower() for word in f if word.strip())

def preprocess(chat_text):
    messages = []

    pattern = r"(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s-\s([^:]+):\s(.*)"

    for line in chat_text.split("\n"):
        match = re.match(pattern, line)
        if match:
            date, time, user, message = match.groups()
            messages.append([date, time, user.strip(), message.strip()])

    df = pd.DataFrame(messages, columns=["date", "time", "users", "user_messages"])

    # date-time processing
    df["date"] = pd.to_datetime(df["date"], dayfirst=True).dt.date
    # df["hour"] = df["time"].str.split(":").str[0].astype(int)
    df.index = df.index + 1

    return df

from nltk.corpus import stopwords


def processed_data_for_wordCloud(df):
    temp = df.copy()
    word_freq = []
    temp = temp[~temp["user_messages"].str.startswith("<", na=False)]
    temp = temp[~(temp["user_messages"] == "This message was deleted")]
    stop_words = set(stopwords.words("english"))

    words = []

    for msg in temp["user_messages"]:
        msg = re.sub(r"[^\w\s]", "", msg.lower())  
        for word in msg.split():
            if word not in stop_words and word not in hinglish_words:
                words.append(word)
    word_freq = Counter(words)
    return " ".join(words)  , word_freq

def processed_data_for_timeliine(df):
    df["day_name"] = pd.to_datetime(df["date"]).dt.day_name()
    df["day"] = pd.to_datetime(df["date"]).dt.day
    df["month"] = pd.to_datetime(df["date"]).dt.month
    df["month_name"] = pd.to_datetime(df["date"]).dt.month_name()
    df["year"] = pd.to_datetime(df["date"]).dt.year
    df["hour"] = pd.to_datetime(df["time"]).dt.hour
    df = df.drop(columns=['date' , 'time'])
    return df
