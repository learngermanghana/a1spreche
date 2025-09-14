import streamlit as st

st.logo("static/icons/falowen-512.png")
st.set_page_config(
    page_title="Falowen – Your German Conversation Partner",
    page_icon="static/icons/falowen-512.png",
    layout="wide",
)

from src.styles import inject_global_styles
from a1sprechen import hide_streamlit_header, login_page

hide_streamlit_header()
inject_global_styles()
st.markdown(
    """
    <style>
    html, body { overscroll-behavior-y: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

login_page()
