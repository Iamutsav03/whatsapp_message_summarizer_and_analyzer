import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd
import streamlit as st
import numpy as np
from utils.nlp_cleaner import get_clean_corpus

@st.cache_data(show_spinner=False)
def generate_wordcloud(df: pd.DataFrame):
    """
    Generates a clean word cloud using the Global NLP Preprocessing Layer.
    All WhatsApp export artifacts are removed before rendering.
    """
    if df.empty:
        return None

    _, joined_text = get_clean_corpus(df)

    if not joined_text.strip():
        return None

    wc = WordCloud(
        width=900, height=450,
        background_color=None, mode="RGBA",
        max_words=150,
        colormap="Greens",
        prefer_horizontal=0.85,
        collocations=False,        # avoid duplicate bigrams
    )

    img = wc.generate(joined_text).to_image()

    fig, ax = plt.subplots(figsize=(10, 5), facecolor='none')
    ax.imshow(np.array(img), interpolation="bilinear")
    ax.axis("off")
    fig.patch.set_alpha(0)
    return fig
