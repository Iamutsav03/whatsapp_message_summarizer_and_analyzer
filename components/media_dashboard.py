import streamlit as st
import pandas as pd
import plotly.express as px
from media.gallery import render_media_gallery
from visualization.charts import (
    apply_plotly_layout, plot_media_type_pie,
    plot_media_stacked_by_sender, plot_media_timeline
)
from config.media_settings import SAMPLING_STRATEGIES, MAX_AI_IMAGES
from config.settings import GEMINI_API_KEY
from components.cards import render_metric_card
from config.tooltips import TOOLTIPS


def render_media_dashboard(media_df: pd.DataFrame, session_id: str):
    """
    Full Media Intelligence tab:
      1. KPI summary row
      2. Deterministic analytics (stacked charts, timeline)
      3. Interactive searchable gallery
      4. Opt-in AI Control Panel
    """
    # ── KPI Row ────────────────────────────────────────────────────────────────
    total_files  = len(media_df)
    total_images = len(media_df[media_df["media_type"] == "Image"])
    total_videos = len(media_df[media_df["media_type"] == "Video"])
    total_docs   = len(media_df[media_df["media_type"] == "Document"])
    total_audio  = len(media_df[media_df["media_type"] == "Audio"])
    total_size   = media_df["size_bytes"].sum() / (1024 * 1024)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        render_metric_card("Total Files", str(total_files), '<i class="bi bi-folder2-open"></i>', help_text="Total number of media files uploaded.")
    with c2:
        render_metric_card("Images", str(total_images), '<i class="bi bi-image"></i>', help_text=TOOLTIPS["images"])
    with c3:
        render_metric_card("Videos", str(total_videos), '<i class="bi bi-camera-video"></i>', help_text=TOOLTIPS["videos"])
    with c4:
        render_metric_card("Audio", str(total_audio), '<i class="bi bi-mic"></i>', help_text=TOOLTIPS["audio"])
    with c5:
        render_metric_card("Documents", str(total_docs), '<i class="bi bi-file-earmark-text"></i>', help_text=TOOLTIPS["documents"])
    with c6:
        render_metric_card("Total Size", f"{total_size:.1f} MB", '<i class="bi bi-hdd"></i>', help_text="Combined file size of all indexed media.")

    # ── Analytics ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Media Analytics")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_media_type_pie(media_df), use_container_width=True)
    with col2:
        st.plotly_chart(plot_media_stacked_by_sender(media_df), use_container_width=True)

    # Media timeline (only if timestamps were successfully linked)
    if media_df["timestamp"].notna().sum() > 5:
        st.plotly_chart(plot_media_timeline(media_df), use_container_width=True)

    # ── Gallery ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Interactive Gallery")

    f1, f2, f3 = st.columns(3)
    with f1:
        search_q = st.text_input("Search Filename")
    with f2:
        senders = ["All"] + sorted(media_df["sender"].unique().tolist())
        sel_sender = st.selectbox("Sender", senders)
    with f3:
        types = ["All"] + sorted(media_df["media_type"].unique().tolist())
        default_idx = types.index("Image") if "Image" in types else 0
        sel_type = st.selectbox("Media Type", types, index=default_idx)

    filtered = media_df.copy()
    if search_q:
        filtered = filtered[filtered["filename"].str.contains(search_q, case=False, na=False)]
    if sel_sender != "All":
        filtered = filtered[filtered["sender"] == sel_sender]
    if sel_type != "All":
        filtered = filtered[filtered["media_type"] == sel_type]

    st.caption(f"Showing **{len(filtered)}** of **{total_files}** files")

    if sel_type in ("Image", "All"):
        render_media_gallery(filtered, session_id)
    else:
        display_cols = ["filename", "sender", "media_type", "size_bytes", "extension"]
        st.dataframe(filtered[display_cols].reset_index(drop=True), use_container_width=True)

    # ── AI Control Panel ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### AI Image Analysis *(Opt-In)*")

    if not GEMINI_API_KEY:
        st.warning("Configure `GEMINI_API_KEY` in `.env` to enable AI analysis.")
        return

    st.info(
        "Privacy First — images are sent to Gemini Vision **only** "
        "after you click **Run AI Analysis**. Nothing is processed automatically."
    )

    with st.expander("Configure AI Analysis Settings", expanded=False):
        ai_strategy  = st.selectbox("Sampling Strategy", SAMPLING_STRATEGIES)
        ai_max       = st.slider("Maximum Images", 5, MAX_AI_IMAGES, 20, step=5)
        sender_opts  = ["All"] + sorted(
            media_df[media_df["media_type"] == "Image"]["sender"].unique().tolist()
        )
        ai_sender    = st.selectbox("Filter by Sender", sender_opts)
        ai_ocr       = st.checkbox("Enable OCR (extract text from screenshots)", value=False)

    col_run, col_clear = st.columns(2)
    with col_run:
        run_ai = st.button("Run AI Analysis", type="primary", use_container_width=True)
    with col_clear:
        if st.button("Clear AI Results", use_container_width=True):
            st.session_state.pop("ai_media_results", None)
            st.rerun()

    if run_ai:
        from ai.image_classifier import run_ai_media_analysis
        with st.spinner("Gemini Vision is classifying sampled images…"):
            results = run_ai_media_analysis(
                media_df=media_df,
                session_id=session_id,
                strategy=ai_strategy,
                max_images=ai_max,
                sender_filter=ai_sender,
                enable_ocr=ai_ocr
            )
        st.session_state["ai_media_results"] = results
        st.success(f"Analysed {len(results)} images.")

    if "ai_media_results" in st.session_state and not st.session_state["ai_media_results"].empty:
        from ai.media_summary import render_ai_results_panel, generate_media_summary
        render_ai_results_panel(st.session_state["ai_media_results"])

        st.markdown("#### AI Media Summary")
        if st.button("Generate Media Summary", use_container_width=True):
            with st.spinner("Generating summary…"):
                summary = generate_media_summary("", st.session_state["ai_media_results"])
            st.info(summary)
