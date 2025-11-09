# Minimal fallback for notice CSS to avoid ModuleNotFoundError
import streamlit as st

def inject_notice_css():
    # Keeps compatibility with existing call sites.
    st.markdown(
        """
        <style>
          /* Fallback notice styles (safe defaults) */
          .falowen-notice{
            background:#eef3fc;
            color:#1a2340;
            border:1px solid #e5e7eb;
            border-radius:12px;
            padding:12px 14px;
            margin:8px 0 16px;
            font-size:0.95rem;
          }
        </style>
        """, 
        unsafe_allow_html=True
    )
