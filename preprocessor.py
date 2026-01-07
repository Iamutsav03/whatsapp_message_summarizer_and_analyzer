import pandas as pd
import re


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
    df.index = df.index +1

    return df
