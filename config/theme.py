import streamlit as st

def apply_custom_theme():
    """Injects custom CSS theme into Streamlit."""
    try:
        with open("assets/variables.css", "r") as f:
            variables_css = f.read()
        with open("assets/styles.css", "r") as f:
            styles_css = f.read()
            
        st.markdown(f"<style>{variables_css}</style>", unsafe_allow_html=True)
        st.markdown(f"<style>{styles_css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Custom CSS files not found. Using default Streamlit theme.")
