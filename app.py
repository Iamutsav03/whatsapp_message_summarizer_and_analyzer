import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from config.settings import APP_TITLE, APP_ICON, LAYOUT
from config.theme import apply_custom_theme
from utils.parser import parse_chat_text
from utils.preprocessor import preprocess_dataframe
from utils.analytics import get_basic_metrics, get_peak_session, calculate_response_times
from utils.helpers import build_structured_context, format_number
from ai.conversation import detect_conversations
from ai.topic_model import extract_topics, extract_monthly_topics
from ai.sentiment import analyze_sentiment, explain_daily_sentiment
from ai.gemini_client import GeminiClient
from ai.explainer import (
    explain_sentiment, explain_activity_pattern, explain_topics,
    explain_conversation_stats, generate_insight_cards
)
from visualization.charts import (
    plot_monthly_activity, plot_daily_activity, plot_day_of_week_activity,
    plot_sentiment_distribution, plot_sentiment_timeline, apply_plotly_layout
)
from visualization.heatmaps import plot_hourly_heatmap
from visualization.wordclouds import generate_wordcloud
from components.sidebar import render_sidebar
from components.cards import render_metric_card, render_health_gauge
from media.storage import create_session_storage, extract_zip_safely, clear_session_storage
from media.media_indexer import index_media_directory, link_media_to_chat
from config.tooltips import TOOLTIPS
import os
import tempfile

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout=LAYOUT)
apply_custom_theme()

# ── Session State Init ─────────────────────────────────────────────────────────
for key, default in [
    ("df", None), ("media_df", None),
    ("session_id", None), ("uploaded_file_name", None)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ────────────────────────────────────────────────────────────────────
uploaded_file, selected_user = render_sidebar(st.session_state.df)

# ── Upload Processing ──────────────────────────────────────────────────────────
if uploaded_file is not None and uploaded_file.name != st.session_state.uploaded_file_name:
    if st.session_state.session_id:
        clear_session_storage(st.session_state.session_id)

    st.session_state.uploaded_file_name = uploaded_file.name
    st.session_state.session_id = create_session_storage()

    with st.spinner("Processing upload…"):
        if uploaded_file.name.endswith(".zip"):
            temp_zip_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
            with open(temp_zip_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            session_dir = extract_zip_safely(temp_zip_path, st.session_state.session_id)
            os.remove(temp_zip_path)

            chat_txt_path = None
            for root, _, files in os.walk(session_dir):
                for file in files:
                    if file.endswith(".txt") and (
                        "chat" in file.lower() or "whatsapp" in file.lower()
                    ):
                        chat_txt_path = os.path.join(root, file)
                        break
                if chat_txt_path:
                    break

            if chat_txt_path:
                with open(chat_txt_path, "r", encoding="utf-8") as f:
                    chat_text = f.read()
                st.session_state.df  = preprocess_dataframe(parse_chat_text(chat_text))
                raw_media = index_media_directory(session_dir)
                st.session_state.media_df = link_media_to_chat(raw_media, st.session_state.df)
            else:
                st.error("No WhatsApp chat .txt found inside the ZIP.")
        else:
            chat_text = uploaded_file.read().decode("utf-8")
            st.session_state.df       = preprocess_dataframe(parse_chat_text(chat_text))
            st.session_state.media_df = pd.DataFrame()

    st.rerun()

# ── Guard: no data yet — show SaaS-style landing page ────────────────────────
if st.session_state.df is None or st.session_state.df.empty:
    _FEATURES = [
        ("bi-bar-chart-line",  "Deterministic Analytics",
         "Message counts, active users, links &amp; media totals, avg messages/day."),
        ("bi-fire",            "Activity Heatmaps",
         "See exactly when conversations peak &#8212; by hour, day, and month."),
        ("bi-chat-dots",       "Session Detection",
         "Auto-splits your chat into conversations using a 30-min inactivity gap."),
        ("bi-emoji-smile",     "Sentiment Tracking",
         "Every message scored with VADER; drill into any day&#39;s mood with AI."),
        ("bi-tags",            "Topic Detection",
         "TF-IDF + NMF surfaces dominant themes; Gemini names them in plain English."),
        ("bi-robot",           "AI Summaries &amp; Insights",
         "Executive summary + 10 non-obvious behavioural insights, powered by Gemini."),
        ("bi-image",           "Media Intelligence",
         "Gallery, storage stats, and opt-in Gemini Vision image classification + OCR."),
        ("bi-cloud",           "Word Clouds &amp; Leaders",
         "Artifact-free word cloud and a top-contributors leaderboard."),
    ]

    _cards = []
    for bi_class, title, desc in _FEATURES:
        _cards.append(
            '<div class="feature-card">'
            '<div class="feature-icon"><i class="bi ' + bi_class + '"></i></div>'
            '<p class="feature-title">' + title + '</p>'
            '<p class="feature-desc">' + desc + '</p>'
            '</div>'
        )
    _grid_html = "".join(_cards)

    _landing_html = (
        '<div class="landing-container">'
        '<div class="landing-hero">'
        '<span class="landing-badge">'
        '<i class="bi bi-stars"></i> AI-Powered &nbsp;&middot;&nbsp; Privacy First &nbsp;&middot;&nbsp; Open Source'
        '</span>'
        '<div class="landing-title">Turn your WhatsApp chats<br>into actionable insights</div>'
        '<p class="landing-subtitle">'
        'Upload any exported chat and get instant analytics, sentiment trends, '
        'topic clusters, and AI-generated summaries &#8212; all computed locally.'
        '</p>'
        '<div class="landing-cue">'
        '<span class="landing-cue-arrow"><i class="bi bi-arrow-left"></i></span>'
        'Upload a <strong>.txt</strong> or <strong>.zip</strong> export from the sidebar to get started'
        '</div>'
        '</div>'
        '<div class="landing-features-grid">' + _grid_html + '</div>'
        '</div>'
    )
    st.markdown(_landing_html, unsafe_allow_html=True)
    st.stop()

# ── Filter by user ─────────────────────────────────────────────────────────────
df = st.session_state.df
if selected_user != "Overall":
    df = df[df["users"] == selected_user]

# ── Core deterministic analytics (cheap, always cached) ───────────────────────
basic_metrics   = get_basic_metrics(df).copy()
conversations   = detect_conversations(df)
response_times  = calculate_response_times(df)
peak            = get_peak_session(df)
basic_metrics["peak_session"] = peak.get("display_string", "Unknown") if peak else "Unknown"

health_score = min(
    100,
    int(
        30 * min(basic_metrics.get("avg_messages_per_day", 0) / 20, 1)
        + 30 * (1 - conversations.get("starters_distribution", {}).get(
            max(conversations.get("starters_distribution", {"x": 0}),
                key=conversations.get("starters_distribution", {"x": 0}).get,
                default="x"), 0))
        + 40
    )
)

# ── Hero Banner ────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='margin-bottom:0;font-family:var(--font-family)'>"
    "<i class='bi bi-bar-chart-line' style='margin-right:10px;color:var(--accent-primary)'></i>"
    "WhatsApp Intelligence</h1>",
    unsafe_allow_html=True
)
chat_type = "Group Chat" if basic_metrics.get("total_users", 0) > 2 else "Personal Chat"
date_col = "date_only" if "date_only" in df.columns else "date"
date_range = (
    f"{df[date_col].min()}  →  {df[date_col].max()}"
    if not df.empty else "—"
)
st.caption(f"**{chat_type}**  ·  {date_range}  ·  `{selected_user}`")

# ── Hero Metric Cards ──────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    render_metric_card("Messages", format_number(basic_metrics.get("total_messages", 0)), '<i class="bi bi-envelope"></i>', help_text=TOOLTIPS["messages"])
with c2:
    render_metric_card("Users", str(basic_metrics.get("total_users", 0)), '<i class="bi bi-people"></i>', help_text=TOOLTIPS["users"])
with c3:
    session_count = conversations.get("total_conversations", 0)
    avg_dur = conversations.get("avg_duration_minutes", 0)
    avg_msgs = conversations.get("avg_messages_per_conv", 0)
    render_metric_card(
        "Chat Sessions",
        f"{session_count} Sessions",
        '<i class="bi bi-chat-dots"></i>',
        help_text=f"{TOOLTIPS['sessions']} (Avg Duration: {avg_dur:.0f} min, Avg Messages: {avg_msgs:.0f})"
    )
with c4:
    avg_reply = response_times.get("avg_response_seconds", 0) / 60
    render_metric_card("Avg Reply", f"{avg_reply:.1f} min", '<i class="bi bi-stopwatch"></i>', help_text=TOOLTIPS["avg_reply"])
with c5:
    render_health_gauge(health_score, help_text=TOOLTIPS["health_score"])

st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

# ── Tab Navigation ─────────────────────────────────────────────────────────────
TAB_NAMES  = ["Overview", "AI Insights", "Topics", "Sentiment", "Activity", "Content", "Media", "Chat Sessions"]
TAB_ICONS  = ["graph-up", "robot", "tags", "emoji-smile", "calendar", "images", "image", "chat-dots"]

selected_tab = option_menu(
    menu_title=None,
    options=TAB_NAMES,
    icons=TAB_ICONS,
    default_index=0,
    orientation="horizontal",
    styles={
        "container":         {"padding": "0 !important", "background-color": "transparent",
                              "border-bottom": "1px solid rgba(255,255,255,0.06)"},
        "icon":              {"color": "var(--text-muted)", "font-size": "14px"},
        "nav-link":          {"font-size": "13px", "font-weight": "500",
                              "color": "var(--text-muted)",
                              "text-align": "center", "padding": "10px 14px",
                              "border-radius": "0", "margin": "0",
                              "border-bottom": "2px solid transparent",
                              "--hover-color": "rgba(248,250,252,0.05)"},
        "nav-link-selected": {"background-color": "transparent",
                              "color": "var(--text-main)",
                              "font-weight": "600",
                              "border-bottom": "2px solid var(--accent-primary)"},
    }
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if selected_tab == "Overview":
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_monthly_activity(df), use_container_width=True)
    with col2:
        st.plotly_chart(plot_day_of_week_activity(df), use_container_width=True)

    st.plotly_chart(plot_hourly_heatmap(df), use_container_width=True)

    # Conversation Intelligence Cards
    st.markdown("### Conversation Intelligence")
    conv_cols = st.columns(3)
    with conv_cols[0]:
        render_metric_card(
            "Total Conversations",
            str(conversations.get("total_conversations", "—")),
            '<i class="bi bi-person-lines-fill"></i>',
            help_text=TOOLTIPS["sessions"]
        )
    with conv_cols[1]:
        avg_dur = conversations.get("avg_duration_minutes", 0)
        render_metric_card(
            "Avg Duration",
            f"{avg_dur:.0f} min",
            '<i class="bi bi-hourglass-split"></i>',
            help_text=TOOLTIPS["avg_duration"]
        )
    with conv_cols[2]:
        render_metric_card(
            "Avg Messages / Conv",
            f"{conversations.get('avg_messages_per_conv', 0):.0f}",
            '<i class="bi bi-chat-text"></i>',
            help_text=TOOLTIPS["avg_msgs_session"]
        )

    # Conversation Starters distribution
    starters = conversations.get("starters_distribution", {})
    if starters:
        st.markdown("#### Conversation Starters")
        starter_df = (
            pd.DataFrame(list(starters.items()), columns=["User", "Share"])
            .sort_values("Share", ascending=False)
            .head(8)
        )
        starter_df["Share %"] = (starter_df["Share"] * 100).round(1)
        fig = px.bar(
            starter_df, x="User", y="Share %",
            color="Share %", color_continuous_scale="Greens",
            labels={"Share %": "% of conversations started"}
        )
        fig = apply_plotly_layout(fig, "Who Starts Conversations?")
        st.plotly_chart(fig, use_container_width=True)

    # Peak session callout
    if peak:
        st.info(
            f"Peak Chat Session — {peak.get('day', '')} "
            f"{peak.get('start_time', '')} to {peak.get('end_time', '')} "
            f"with {peak.get('message_count', '')} messages"
        )

    # Explain activity — opt-in
    with st.expander("AI Explanation — Activity Pattern"):
        if st.button("Generate AI Explanation", key="explain_activity"):
            day_counts = df["day_name"].value_counts().to_dict()
            with st.spinner("Asking Gemini…"):
                explanation = explain_activity_pattern(peak, day_counts)
            st.write(explanation)

# ══════════════════════════════════════════════════════════════════════════════
# TAB: AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "AI Insights":
    st.markdown("### AI-Generated Intelligence")

    with st.spinner("Running NLP and building context…"):
        topics      = extract_topics(df)
        sent_result = analyze_sentiment(df)
        context     = build_structured_context(
            df, basic_metrics, topics,
            sent_result["summary"], conversations
        )

    client = GeminiClient()

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("#### Executive Summary")
        with st.spinner("Generating summary…"):
            summary = client.generate_summary(context)
        st.info(summary)

    with col2:
        st.markdown("#### Peak Activity")
        if peak:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3><i class="bi bi-fire"></i> Peak Session</h3>
                    <div class="value">{peak.get('day','')}</div>
                    <p style="color:var(--accent-primary)">{peak.get('start_time','')} – {peak.get('end_time','')}</p>
                    <p style="color:var(--text-muted)">{peak.get('message_count','')} messages</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("#### Smart Insight Cards")
    with st.spinner("Generating insights…"):
        insights = generate_insight_cards(context)
    cols = st.columns(2)
    for i, insight in enumerate(insights):
        with cols[i % 2]:
            st.success(insight)

    st.markdown("---")
    st.markdown("#### Conversation Intelligence — AI Explanation")
    with st.expander("Explain Conversation Patterns"):
        if st.button("Generate Conversation Explanation", key="explain_conv"):
            with st.spinner("Asking Gemini…"):
                conv_exp = explain_conversation_stats(conversations)
            st.write(conv_exp)

# ══════════════════════════════════════════════════════════════════════════════
# TAB: TOPICS
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "Topics":
    st.markdown("### Discussion Themes")

    with st.spinner("Extracting and naming topics with Gemini…"):
        topics = extract_topics(df)

    if not topics:
        st.warning("Not enough text data to extract topics. Try with a larger chat.")
    else:
        # Topic cards in a grid
        topic_cols = st.columns(min(len(topics), 3))
        for i, t in enumerate(topics):
            with topic_cols[i % len(topic_cols)]:
                kw_html = " &nbsp; ".join(
                    f'<span class="kw-badge">{k}</span>'
                    for k in t["keywords"][:5]
                )
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <h3><i class="bi bi-tags"></i> {t['name']}</h3>
                        <p style="margin-top:8px">{kw_html}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Explain topics
        with st.expander("AI: What do these topics reveal?"):
            if st.button("Generate Topics Explanation", key="explain_topics"):
                with st.spinner("Asking Gemini…"):
                    explanation = explain_topics(topics)
                st.write(explanation)

    # Monthly Topic Breakdown
    st.markdown("---")
    st.markdown("### How Topics Changed Over Time")
    with st.spinner("Computing monthly topic breakdown…"):
        monthly_topics = extract_monthly_topics(df)

    if monthly_topics:
        for period_data in monthly_topics[-6:]:  # show last 6 months
            with st.expander(f"{period_data['period']}", expanded=False):
                for t in period_data["topics"]:
                    kws = ", ".join(t["keywords"][:5])
                    st.markdown(f"**{t['name']}** — `{kws}`")
    else:
        st.info("Not enough monthly data for breakdown.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB: SENTIMENT
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "Sentiment":
    st.markdown("### Mood & Sentiment Analysis")

    with st.spinner("Scoring every message…"):
        res = analyze_sentiment(df)

    if not res["summary"]:
        st.warning("No sentiment data available.")
    else:
        summary = res["summary"]
        sent_df = res["df"]

        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            st.markdown(
                f"""
                <div class="metric-card metric-card-centered">
                    <h3>Overall Mood</h3>
                    <div class="value value-md">{summary['overall_mood']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.plotly_chart(
                plot_sentiment_distribution(summary["distribution"]),
                use_container_width=True
            )
        with col3:
            st.plotly_chart(
                plot_sentiment_timeline(sent_df),
                use_container_width=True
            )

        # AI Mood Explanation
        with st.expander("AI: Why this mood?"):
            if st.button("Explain Overall Sentiment", key="explain_sent"):
                with st.spinner("Asking Gemini…"):
                    sent_exp = explain_sentiment(summary)
                st.write(sent_exp)

        # Daily Sentiment Drill-Down
        st.markdown("---")
        st.markdown("### Daily Sentiment Drill-Down")
        st.caption("Select any day to get an AI explanation of the mood for that day.")

        if "date_only" in sent_df.columns:
            daily_avg = (
                sent_df.groupby("date_only")["sentiment_score"]
                .mean()
                .reset_index()
                .sort_values("date_only")
            )
            daily_avg["date_str"] = daily_avg["date_only"].astype(str)

            selected_date = st.selectbox(
                "Choose a date",
                options=daily_avg["date_str"].tolist()[::-1]
            )

            if selected_date:
                day_df = sent_df[sent_df["date_only"].astype(str) == selected_date]
                day_score = daily_avg[daily_avg["date_str"] == selected_date]["sentiment_score"].values[0]
                mood_label = (
                    "Positive" if day_score > 0.05
                    else "Negative" if day_score < -0.05
                    else "Neutral"
                )

                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <h3><i class="bi bi-calendar3"></i> {selected_date}</h3>
                            <div class="value value-sm">{mood_label}</div>
                            <p style="color:var(--text-muted)">Score: {day_score:.3f}</p>
                            <p style="color:var(--text-muted)">{len(day_df)} messages</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col_b:
                    if st.button("Explain this day's mood (AI)", key="explain_day"):
                        with st.spinner("Gemini is reading the day's conversations…"):
                            day_explanation = explain_daily_sentiment(day_df, selected_date)
                        st.info(day_explanation)

                    # Show a few messages from that day
                    with st.expander("Sample messages from this day"):
                        sample_msgs = day_df[["users", "user_messages", "sentiment_label"]].head(10)
                        st.dataframe(sample_msgs, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB: ACTIVITY
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "Activity":
    st.markdown("### Activity Analytics")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_daily_activity(df), use_container_width=True)
    with col2:
        st.plotly_chart(plot_monthly_activity(df), use_container_width=True)

    st.plotly_chart(plot_day_of_week_activity(df), use_container_width=True)
    st.plotly_chart(plot_hourly_heatmap(df), use_container_width=True)

    if peak:
        st.info(
            f"Peak Session: {peak.get('day','')} "
            f"{peak.get('start_time','')} to {peak.get('end_time','')} "
            f"({peak.get('message_count','')} messages)"
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB: CONTENT
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "Content":
    st.markdown("### Popular Discussion Terms")

    col1, col2 = st.columns([1.5, 1])
    with col1:
        with st.spinner("Generating Word Cloud…"):
            fig = generate_wordcloud(df)
        if fig:
            st.pyplot(fig)
        else:
            st.info("Not enough text data to generate a word cloud.")

    with col2:
        st.markdown("#### Message Stats")
        render_metric_card("Total Messages", format_number(basic_metrics.get("total_messages", 0)), '<i class="bi bi-envelope"></i>', help_text=TOOLTIPS["messages"])
        render_metric_card("Media Shared", str(basic_metrics.get("total_media", 0)), '<i class="bi bi-image"></i>', help_text="Total media elements including images, videos, audio and docs.")
        render_metric_card("Links Shared", str(basic_metrics.get("total_links", 0)), '<i class="bi bi-link-45deg"></i>', help_text="Total links shared in messages.")
        render_metric_card("Avg / Day", f"{basic_metrics.get('avg_messages_per_day', 0):.1f}", '<i class="bi bi-calendar3"></i>', help_text="Average messages shared per day.")

    # Top Users leaderboard
    st.markdown("---")
    st.markdown("### Top Active Users")
    user_counts = (
        df.groupby("users")
        .size()
        .reset_index(name="messages")
        .sort_values("messages", ascending=False)
        .head(10)
    )
    user_counts["contribution %"] = (
        user_counts["messages"] / user_counts["messages"].sum() * 100
    ).round(1)

    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(user_counts.reset_index(drop=True), use_container_width=True)
    with col2:
        fig = px.bar(
            user_counts.head(5), x="users", y="contribution %",
            color="contribution %", color_continuous_scale="Greens"
        )
        fig = apply_plotly_layout(fig, "Contribution %")
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB: MEDIA
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "Media":
    st.markdown("### Media Intelligence")
    st.caption("Deterministic indexing — no AI without your consent.")

    media_df = st.session_state.media_df
    if media_df is None or media_df.empty:
        st.info("Upload a `.zip` WhatsApp export to unlock media analytics.")
    else:
        from components.media_dashboard import render_media_dashboard
        render_media_dashboard(media_df, st.session_state.session_id)

# ══════════════════════════════════════════════════════════════════════════════
# TAB: CHAT SESSIONS
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "Chat Sessions":
    from components.session_analytics import render_session_analytics
    render_session_analytics(conversations)
