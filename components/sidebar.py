import streamlit as st
import pandas as pd
from typing import Tuple, Any

def render_sidebar(chat_df: pd.DataFrame) -> Tuple[Any, str]:
    """Renders the ChatScope sidebar with upload, user filter, and session controls."""
    with st.sidebar:

        # ── Wordmark ──────────────────────────────────────────────────────────
        st.markdown(
            '<div class="sidebar-wordmark">'
            '<div class="sidebar-wordmark-icon">'
            '<i class="bi bi-graph-up-arrow"></i>'
            '</div>'
            '<span class="sidebar-wordmark-name">ChatScope</span>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

        # ── Upload Section ────────────────────────────────────────────────────
        st.markdown(
            '<p class="sidebar-section-label">'
            '<i class="bi bi-upload"></i> Chat Export'
            '</p>',
            unsafe_allow_html=True
        )
        uploaded_file = st.file_uploader(
            label="Upload a .txt or .zip WhatsApp export",
            type=["txt", "zip"],
            label_visibility="collapsed"
        )

        # ── User Filter (only after data loaded) ──────────────────────────────
        selected_user = "Overall"
        if chat_df is not None and not chat_df.empty:
            st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
            st.markdown(
                '<p class="sidebar-section-label">'
                '<i class="bi bi-person-check"></i> Filter by User'
                '</p>',
                unsafe_allow_html=True
            )
            users_list = ["Overall"] + sorted(chat_df["users"].unique().tolist())
            selected_user = st.selectbox(
                "User",
                users_list,
                label_visibility="collapsed"
            )

        # ── Privacy & Session ─────────────────────────────────────────────────
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown(
            '<p class="sidebar-section-label">'
            '<i class="bi bi-shield-lock"></i> Privacy &amp; Session'
            '</p>',
            unsafe_allow_html=True
        )

        if st.button("Clear Session & Media", use_container_width=True):
            if st.session_state.get("session_id"):
                from media.storage import clear_session_storage
                clear_session_storage(st.session_state.session_id)
            st.session_state.clear()
            st.rerun()

        st.markdown(
            '<p class="sidebar-footer">'
            'Media processed locally. AI features are opt-in only.'
            '</p>',
            unsafe_allow_html=True
        )

        return uploaded_file, selected_user
