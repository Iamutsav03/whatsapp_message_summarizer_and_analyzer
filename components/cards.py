import streamlit as st

def render_metric_card(title: str, value: str, icon: str = "", help_text: str = "", details: list = None):
    """
    Renders a clean SaaS-style metric card.
    All layout & visual properties live in assets/styles.css (.metric-card, .value).
    Single-line HTML construction avoids Streamlit markdown escaping.
    """
    container_class = "metric-card tooltip-container" if help_text else "metric-card"
    tooltip_html = f'<div class="tooltip-text">{help_text}</div>' if help_text else ""

    details_html = ""
    if details:
        rows = "".join(f"<div>{d}</div>" for d in details)
        details_html = f'<div class="card-details mt-8 text-muted">{rows}</div>'

    html = f'<div class="{container_class}"><div><h3>{icon}&nbsp;{title}</h3><div class="value">{value}</div></div>{details_html}{tooltip_html}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_health_gauge(score: int, help_text: str = ""):
    """
    Renders the SVG-based chat health score gauge.
    All card chrome comes from .metric-card in styles.css.
    """
    color  = "#25D366" if score >= 75 else "#F6E05E" if score >= 50 else "#EF4444"
    label  = "Healthy"  if score >= 75 else "Moderate" if score >= 50 else "Needs Attention"

    container_class = "metric-card metric-card-health tooltip-container" if help_text else "metric-card metric-card-health"
    tooltip_html = f'<div class="tooltip-text">{help_text}</div>' if help_text else ""

    radius = 44
    circ   = round(2 * 3.14159 * radius, 2)
    dash   = round(circ * score / 100, 1)

    html = (
        f'<div class="{container_class}">'
        f'<h3><i class="bi bi-heart-pulse"></i>&nbsp;CHAT HEALTH SCORE</h3>'
        f'<div class="health-gauge-svg-container">'
        f'<svg width="110" height="110" viewBox="0 0 110 110">'
        f'<circle cx="55" cy="55" r="{radius}" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="10"/>'
        f'<circle cx="55" cy="55" r="{radius}" fill="none" stroke="{color}" stroke-width="10" stroke-dasharray="{dash} {circ}" stroke-linecap="round" transform="rotate(-90 55 55)" style="transition:stroke-dasharray 0.6s ease;"/>'
        f'<text x="55" y="60" text-anchor="middle" font-size="22" font-weight="700" fill="white" font-family="Inter,sans-serif">{score}</text>'
        f'</svg>'
        f'</div>'
        f'<p class="health-label" style="color:{color};">{label}</p>'
        f'{tooltip_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
