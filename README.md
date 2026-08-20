# WhatsApp Intelligence Dashboard

A premium, AI-powered analytics dashboard for WhatsApp chat exports — built as a portfolio-grade full-stack data science project.

---

## Features

### Phase 1 — Chat Analytics
- Upload `.txt` or `.zip` WhatsApp exports
- Parse and preprocess chat data with robust regex support
- Deterministic metrics: total messages, users, links, media, avg messages/day
- Monthly, daily, hourly, and day-of-week activity charts (all Plotly)
- Hourly heatmap
- Word cloud (artifact-free via Global NLP Preprocessor)
- Top active users leaderboard
- Conversation detection (30-minute gap rule)
- Response time analysis (avg, fastest, slowest, per-user)
- Peak chat session detection
- Conversation starter distribution

### Phase 2 — AI Intelligence (Gemini)
- AI Executive Summary (Group vs Personal chat-aware)
- Smart Insight Cards (10+ non-obvious behavioural insights)
- TF-IDF + NMF Topic Detection with **Gemini topic naming** (keywords only — never full chat)
- Monthly topic breakdown (how discussions evolved over time)
- VADER Sentiment Analysis per message
- Sentiment timeline and distribution
- **Daily sentiment drill-down** — click any day, get AI explanation
- **"Explain This"** button on every major chart section
- AI Conversation Intelligence explanation
- Chat Health Score

### Phase 2 — Media Intelligence
- Support for `.zip` WhatsApp exports containing media
- Instant deterministic media indexer (no AI)
- Stacked media charts by sender (phone numbers anonymised)
- Media type distribution, timeline, storage usage
- Interactive searchable/filterable image gallery with lazy thumbnails
- **Opt-in AI Image Classification** via Gemini Vision
  - Sampling strategies: Random, Newest, Oldest, Largest, By Sender
  - User-controlled limits
  - Structured results: category, confidence, description, OCR text
  - Category distribution and per-sender breakdown charts
- Optional OCR via Gemini Vision
- AI Media Summary
- Session privacy controls: "Clear Session & Media" wipes all temp files

---

## Project Structure

```
Whatsapp-Analyzer/
├── app.py                   Main Streamlit application
├── .env                     API key config (never commit this)
├── requirements.txt
├── hinglish.txt             Hinglish stopwords for NLP cleaning
│
├── assets/
│   ├── styles.css           Premium dark CSS theme
│   └── variables.css        CSS custom properties
│
├── config/
│   ├── settings.py          Centralised app config
│   ├── media_settings.py    Media processing config
│   └── theme.py             CSS injection
│
├── utils/
│   ├── parser.py            WhatsApp regex parser
│   ├── preprocessor.py      DateTime feature extraction
│   ├── analytics.py         Deterministic metrics
│   ├── nlp_cleaner.py       Global NLP preprocessor (Phase 2.5)
│   ├── helpers.py           Structured context builder
│   └── constants.py        App-wide constants
│
├── ai/
│   ├── gemini_client.py     Gemini summary + insights wrapper
│   ├── sentiment.py         VADER + daily drill-down
│   ├── topic_model.py       TF-IDF + NMF + Gemini naming
│   ├── conversation.py      30-min gap conversation detection
│   ├── explainer.py         "Explain This" for all charts
│   ├── vision.py            GeminiVisionProvider
│   ├── providers.py         Abstract VisionProvider interface
│   ├── image_classifier.py  Opt-in batch image analysis
│   └── media_summary.py     AI media summary generation
│
├── visualization/
│   ├── charts.py            All Plotly charts (dark themed)
│   ├── heatmaps.py          Hourly heatmap
│   └── wordclouds.py        Artifact-free word cloud
│
├── components/
│   ├── sidebar.py           Upload + user filter + privacy controls
│   ├── cards.py             Metric cards + health gauge
│   └── media_dashboard.py   Full media tab
│
├── media/
│   ├── storage.py           Secure ZIP extraction (Zip Slip safe)
│   ├── media_indexer.py     Fast deterministic file cataloguer
│   ├── metadata.py          File metadata extractor
│   ├── gallery.py           Responsive image grid
│   └── thumbnail_generator.py  Lazy cached thumbnails
│
└── prompts/
    ├── summary_prompt.txt   Gemini chat summary prompt
    └── insights_prompt.txt  Gemini insight cards prompt
```

---

## Installation

```bash
git clone https://github.com/yourusername/whatsapp-analyzer.git
cd whatsapp-analyzer
pip install -r requirements.txt
```

### Download NLTK data (first run only)

```python
import nltk
nltk.download("stopwords")
```

---

## Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_key_here
```

### Getting a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **Get API Key** → **Create API key**
4. Copy and paste into your `.env` file

> The free tier is sufficient for most personal chats. For large group chats, consider Gemini 1.5 Flash which has a generous free quota.

---

## Running Locally

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## AI Design Principle

> **Compute everything measurable locally. Use AI only to explain, summarise, and generate actionable insights.**

- All statistics (message counts, sentiment scores, topic keywords, conversation gaps) are computed deterministically in Python
- Gemini receives only structured JSON context or small keyword sets — never the full chat
- Media AI is strictly opt-in. Zero images are sent to Gemini automatically
- All AI calls are cached in `st.session_state` to avoid redundant API usage

---

## Future Roadmap

- [ ] Semantic search across messages
- [ ] AI Chat (conversational Q&A over your chat history)
- [ ] Face clustering in shared photos (privacy-preserving)
- [ ] Duplicate image detection
- [ ] PDF/HTML report export
- [ ] Multi-chat comparison
- [ ] Authentication + cloud storage
- [ ] OpenAI / Claude as alternative AI providers
