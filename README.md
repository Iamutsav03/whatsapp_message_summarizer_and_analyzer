# 💬 ChatScope — WhatsApp Chat Analyzer & Summarizer

Turn your exported WhatsApp chats into clear, visual insights — powered by AI.

> Upload any WhatsApp chat export and instantly see who talks the most, how the mood
> shifts over time, what topics come up, and get an AI-written summary of the whole
> conversation — all without any manual reading.

---

## 🌟 What is this?

ChatScope is a free, privacy-first web app that reads your exported WhatsApp chat
(the `.txt` or `.zip` file WhatsApp lets you export from any conversation) and turns
it into an interactive dashboard. No technical knowledge needed — just upload and explore.

---

## ✨ Features

| Feature | What it actually tells you |
|---|---|
| 📊 **Message Stats** | How many messages were sent, by whom, and how active each person is |
| ⏱️ **Reply Speed** | How fast people typically reply to each other |
| 🔥 **Activity Patterns** | What time of day and which days you chat the most |
| 💬 **Conversation Sessions** | How many separate "conversations" happened, and who usually starts them |
| 🎭 **Mood & Sentiment** | Whether the overall tone of the chat is positive, negative, or neutral — and how it changes day to day |
| 🏷️ **Topics Discussed** | What you actually talk about most, grouped into simple themes |
| 🤖 **AI Executive Summary** | A short, human-readable summary of the entire conversation, written by AI |
| 💡 **Smart Insight Cards** | Interesting, non-obvious patterns AI notices in your chat |
| 🖼️ **Media Gallery** | A browsable gallery of shared photos, with AI able to describe or read text in them (optional) |
| ☁️ **Word Cloud & Top Contributors** | The most-used words and a leaderboard of who's most active |

Everything above works from a single upload — no setup, no signup required for basic use.

---

## 🔒 Privacy First

- Your chat data is processed only for your session and is not permanently stored.
- AI-powered features (summaries, topic naming, image analysis) are **opt-in** — you choose when to trigger them.
- This is a personal portfolio project. As a transparency note: uploaded chats may be
  reviewed by the developer for debugging or quality/abuse-prevention purposes.
  Please avoid uploading chats containing information you wouldn't want a third party to see.

---

## 🚀 How to Use It

1. Export a chat from WhatsApp (`Chat → More → Export Chat`, with or without media).
2. Open ChatScope and upload the `.txt` or `.zip` file from the sidebar.
3. Explore the tabs: Overview, AI Insights, Topics, Sentiment, Activity, Content, Media, and Chat Sessions.
4. Optionally trigger AI features (summaries, mood explanations, topic naming) with a single click per section.

---

## 🛠️ Technical Overview

### Architecture
ChatScope is a **monolithic Python web application** built with **Streamlit**, combining
frontend rendering and backend logic in a single process. Deterministic computation runs
entirely server-side; generative AI tasks are delegated asynchronously to the **Google Gemini API**.

### Tech Stack

| Layer | Technology |
|---|---|
| **App Framework** | Python, Streamlit |
| **Data Processing** | pandas, numpy |
| **Visualization** | Plotly (Express & Graph Objects), Matplotlib, WordCloud |
| **NLP / Analytics** | VADER (sentiment analysis), scikit-learn (TF-IDF + NMF for topic modeling), urlextract, emoji parsing |
| **AI Integration** | Google Gemini (`google-genai` SDK) — summarization, semantic labeling, and vision-based image classification/OCR |
| **Media Handling** | Pillow (thumbnailing), zipfile (secure extraction), UUID-based session isolation |
| **Deployment** | Render (Python web service, environment-based configuration) |

### Key Engineering Details

- **Modular architecture**: clear separation of concerns across `ai/`, `media/`, `utils/`,
  `visualization/`, `components/`, and `config/` — UI rendering is fully decoupled from
  business logic and AI orchestration.
- **Deterministic vs. generative split**: all core metrics (message counts, response times,
  activity patterns, sentiment scoring) are computed locally and deterministically before
  any AI call is made — Gemini is used only for summarization, natural-language explanation,
  and vision tasks, minimizing API cost and latency.
- **Session isolation**: each upload is scoped to a UUID-based session directory, preventing
  data collisions between concurrent users and enabling clean per-session cleanup.
- **Secure file handling**: ZIP extraction is hardened against path-traversal ("Zip Slip") exploits.
- **NLP pipeline**: custom Hinglish-aware stopword filtering, TF-IDF vectorization, and
  NMF-based topic extraction, with Gemini used to translate raw topic clusters into
  human-readable labels.
- **Production-ready deployment config**: pinned dependencies, environment-based secrets
  management, session-scoped ephemeral storage, and a Streamlit production configuration
  tuned for headless deployment on Render.

### Why this project is worth a look
It demonstrates end-to-end product thinking beyond just "calling an LLM API" —
deterministic data engineering, thoughtful AI/cost-conscious architecture, security-aware
file handling, and a full path from local prototype to a deployed, production-configured
web application.

---
## 📄 License

This project is open source. Feel free to explore the code, fork it, or reach out if you'd like to discuss it.
