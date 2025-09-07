"""Global styling helpers for Streamlit UI components."""
from __future__ import annotations

import streamlit as st

# Shared CSS variables and utility classes
GLOBAL_CSS = """
:root {
  --google-blue: #1a73e8;
  --text-light: #ffffff;
}

.flex-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

.g-btn-wrap {
  margin: 12px 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 700;
}

.btn-google {
  background: var(--google-blue);
  color: var(--text-light);
  box-shadow: 0 2px 8px rgba(26,115,232,.25);
  padding: 10px 18px;
  font-size: 15px;
}

.google-logo {
  display: inline-flex;
  width: 18px;
  height: 18px;
}

.no-decoration {
  text-decoration: none;
}
"""

def inject_global_styles() -> None:
    """Inject shared CSS variables and classes into the app."""
    st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)
