from urlextract import URLExtract
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import emoji
import pandas as pd
from collections import Counter

extractor = URLExtract()


def most_active_users(df, top_n=10):
    contribution_df = round((df["users"].value_counts()/df.shape[0])*100 , 2).reset_index().rename(columns={'index' : 'User' , 'users' : 'Contribution(%)'})
    contribution_df.index = contribution_df.index +1
    return contribution_df.head(top_n)


# def daily_timeline(df):
#     timeline = df.groupby(df["date"].dt.date).size().reset_index(name="messages")
#     return timeline

def Link_count(df):
    return df["user_messages"].apply(lambda x: len(extractor.find_urls(x)) > 0).sum()

def generate_word_cloud(df):
    wc = WordCloud(width=350 , height=300 , max_words=100 , max_font_size=80 ,background_color='black')
    df_wc = wc.generate(df)
    fig, ax = plt.subplots()
    img = df_wc.to_image()
    ax.imshow(np.array(img))
    ax.axis("off")
    return fig


def emoji_analysis(df):
    emojis = []

    for message in df["user_messages"]:
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])

    emoji_counter = Counter(emojis)

    emojis_df = pd.DataFrame(
        emoji_counter.items(), columns=["EMOJI", "COUNT"]
    ).sort_values(by="COUNT", ascending=False).reset_index(drop=True)
    emojis_df.index = emojis_df.index +1 

    return emojis_df


def prepare_emoji_pie_data(emoji_df, top_n=6):
    top = emoji_df.head(top_n)
    others_count = emoji_df["COUNT"][top_n:].sum()

    if others_count > 0:
        top = pd.concat(
            [
                top,
                pd.DataFrame({"EMOJI": ["Others"], "COUNT": [others_count]}),
            ],
            ignore_index=True,
        )

    return top

def most_active_months(df):
    xyz = (
        df["month_name"]
        .value_counts()
        .reset_index(name="COUNT")
        .rename(columns={"index": "MONTH"})
    )
    xyz.index = xyz.index + 1
    return xyz


def most_active_dayName(df):
    xyz = (
        df["day_name"]
        .value_counts()
        .reset_index(name="COUNT")
        .rename(columns={"index": "DAY NAME"})
    )
    xyz.index = xyz.index + 1
    return xyz


def most_active_years(df):
    xyz = (
        df["year"]
        .value_counts()
        .reset_index(name="COUNT")
        .rename(columns={"index": "YEAR"})
    )
    xyz.index = xyz.index + 1
    return xyz
