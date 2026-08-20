"""
Session Analytics UI Component — Phase 2.5

Renders the full Chat Sessions feature:
- Session insight cards (longest, fastest, most positive, etc.)
- Chronological session timeline with AI title + summary
- Overall AI explanation of the sessions
"""

import streamlit as st
import pandas as pd
from ai.conversation import generate_session_title, generate_session_summary
from ai.explainer import explain_conversation_stats
from components.cards import render_metric_card
from config.tooltips import TOOLTIPS


def _fmt_duration(seconds: float) -> str:
    """Formats seconds into a human-readable duration string."""
    total_minutes = int(seconds // 60)
    if total_minutes < 60:
        return f"{total_minutes} min"
    hours   = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m" if minutes else f"{hours}h"


def _mood_label(avg_sentiment: float) -> str:
    if avg_sentiment > 0.1:  return "Positive"
    if avg_sentiment < -0.1: return "Negative"
    return "Neutral"


def render_session_insights(conversations: dict):
    """Top-row insight cards for the special sessions."""
    conv_df: pd.DataFrame = conversations.get("raw_conversations_df", pd.DataFrame())
    if conv_df.empty:
        return

    st.markdown("### Session Highlights")
    cols = st.columns(4)

    longest_row = conv_df.loc[conv_df["duration_seconds"].idxmax()]
    most_active = conv_df.loc[conv_df["message_count"].idxmax()]
    most_pos    = conv_df.loc[conv_df["avg_sentiment"].idxmax()]

    with cols[0]:
        render_metric_card(
            "Longest Session",
            _fmt_duration(longest_row['duration_seconds']),
            '<i class="bi bi-trophy"></i>',
            help_text=TOOLTIPS["longest_session"],
            details=[f"Session #{int(longest_row['conv_id'])} · {longest_row['message_count']} msgs"]
        )

    with cols[1]:
        render_metric_card(
            "Most Active",
            f"{most_active['message_count']} msgs",
            '<i class="bi bi-fire"></i>',
            help_text=TOOLTIPS["most_active_session"],
            details=[f"Session #{int(most_active['conv_id'])} · {_fmt_duration(most_active['duration_seconds'])}"]
        )

    with cols[2]:
        render_metric_card(
            "Most Positive",
            f"+{most_pos['avg_sentiment']:.2f}",
            '<i class="bi bi-emoji-smile"></i>',
            help_text="The session with the highest average sentiment score.",
            details=[f"Session #{int(most_pos['conv_id'])} · {most_pos['message_count']} msgs"]
        )

    with cols[3]:
        gap_min = conversations.get("longest_gap_minutes", 0)
        gap_before = conversations.get("longest_gap_before", "—")
        gap_hours = gap_min / 60
        gap_str = f"{gap_hours:.0f}h" if gap_hours >= 1 else f"{gap_min:.0f} min"
        render_metric_card(
            "Longest Silence",
            gap_str,
            '<i class="bi bi-moon-stars"></i>',
            help_text=TOOLTIPS["longest_gap"],
            details=[f"Before {gap_before}"]
        )


def render_session_timeline(conversations: dict):
    """Chronological session list with AI title + on-demand summary."""
    conv_df: pd.DataFrame = conversations.get("raw_conversations_df", pd.DataFrame())
    if conv_df.empty:
        st.info("No sessions detected.")
        return

    st.markdown("### Session Timeline")
    st.caption(
        f"Showing all **{len(conv_df)}** sessions — "
        "detected using a 30-minute inactivity threshold."
    )

    # Pagination to avoid rendering 100+ sessions at once
    page_size = 10
    total_pages = max(1, (len(conv_df) + page_size - 1) // page_size)
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1,
                           label_visibility="collapsed")
    start_idx = (page - 1) * page_size
    page_df = conv_df.sort_values("start_time", ascending=False).iloc[start_idx:start_idx + page_size]

    for _, row in page_df.iterrows():
        _render_session_card(row, conversations)


def _render_session_card(row: pd.Series, conversations: dict):
    """Renders a single session expander with AI title, stats, and on-demand summary."""
    conv_id   = int(row["conv_id"])
    dur_str   = _fmt_duration(row["duration_seconds"])
    start     = row["start_time"]
    end       = row["end_time"]
    mood      = _mood_label(row.get("avg_sentiment", 0))
    date_str  = start.strftime("%d %B %Y")
    time_str  = f"{start.strftime('%I:%M %p')} → {end.strftime('%I:%M %p')}"
    participants = ", ".join(row.get("participants", []))
    sample    = row.get("sample_messages", [])
    stats     = {
        "duration_minutes": row["duration_seconds"] / 60,
        "message_count":    row["message_count"],
        "avg_sentiment":    row.get("avg_sentiment", 0),
    }

    # Get cached AI title from session_state if available
    cache_key = f"session_title_{conv_id}"
    title = st.session_state.get(cache_key, f"Session #{conv_id}")

    with st.expander(f"**{title}** · {date_str} · {dur_str} · {row['message_count']} msgs", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Date",      date_str)
        col2.metric("Duration",  dur_str)
        col3.metric("Messages",  row["message_count"])
        col4.metric("Mood",      mood)

        st.markdown(f"**Time:** `{time_str}`")
        st.markdown(f"**Participants:** {participants}")

        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            if st.button("Generate Session Title", key=f"title_btn_{conv_id}"):
                with st.spinner("Generating title…"):
                    ai_title = generate_session_title(sample, stats)
                st.session_state[f"session_title_{conv_id}"] = ai_title
                st.success(f"**{ai_title}**")
                st.rerun()

        with btn_col2:
            if st.button("Generate Summary", key=f"summary_btn_{conv_id}"):
                with st.spinner("Summarising session…"):
                    ai_summary = generate_session_summary(sample, stats)
                st.session_state[f"session_summary_{conv_id}"] = ai_summary

        # Show cached summary if available
        summary_key = f"session_summary_{conv_id}"
        if summary_key in st.session_state:
            st.info(st.session_state[summary_key])

        # Show sample messages
        with st.expander("Preview messages from this session"):
            for msg in sample[:10]:
                st.markdown(f"> {msg}")


def render_session_analytics(conversations: dict):
    """
    Full session analytics section — inserted into the Overview tab
    or a dedicated Sessions tab.
    """
    if not conversations or conversations.get("total_conversations", 0) == 0:
        st.info("No session data available.")
        return

    total  = conversations.get("total_conversations", 0)
    avg_d  = conversations.get("avg_duration_minutes", 0)
    avg_m  = conversations.get("avg_messages_per_conv", 0)
    lng_d  = conversations.get("longest_duration_minutes", 0)
    srt_d  = conversations.get("shortest_duration_minutes", 0)

    # ── Summary metrics ──────────────────────────────────────────────────────
    st.markdown("### Chat Sessions Overview")
    st.caption("A new session starts when there is no activity for more than 30 minutes.")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card("Total Sessions", str(total), '<i class="bi bi-chat-dots"></i>', help_text=TOOLTIPS["sessions"])
    with c2:
        render_metric_card("Avg Duration", f"{avg_d:.0f} min", '<i class="bi bi-hourglass-split"></i>', help_text=TOOLTIPS["avg_duration"])
    with c3:
        render_metric_card("Avg Messages", f"{avg_m:.0f}", '<i class="bi bi-chat-text"></i>', help_text=TOOLTIPS["avg_msgs_session"])
    with c4:
        render_metric_card("Longest Session", _fmt_duration(lng_d * 60), '<i class="bi bi-trophy"></i>', help_text=TOOLTIPS["longest_session"])
    with c5:
        render_metric_card("Shortest Session", _fmt_duration(srt_d * 60), '<i class="bi bi-stopwatch"></i>', help_text=TOOLTIPS["shortest_session"])

    st.markdown("---")

    # ── AI explanation ───────────────────────────────────────────────────────
    with st.expander("AI: Explain these sessions", expanded=False):
        if st.button("Generate Session Explanation", key="explain_sessions"):
            with st.spinner("Asking Gemini…"):
                explanation = explain_conversation_stats(conversations)
            st.write(explanation)

    # ── Insight cards ────────────────────────────────────────────────────────
    render_session_insights(conversations)

    st.markdown("---")

    # ── Timeline ─────────────────────────────────────────────────────────────
    render_session_timeline(conversations)
