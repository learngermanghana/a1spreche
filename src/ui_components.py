"""Small reusable UI components for Streamlit."""

from __future__ import annotations

import streamlit as st


def render_assignment_reminder() -> None:
    """Show a yellow assignment reminder box."""

    st.markdown(
        '''
        <div style="
            box-sizing: border-box;
            width: 100%;
            max-width: 600px;
            padding: 16px;
            background: #ffc107;
            color: #000;
            border-left: 6px solid #e0a800;
            margin: 16px auto;
            border-radius: 8px;
            font-size: 1.1rem;
            line-height: 1.4;
            text-align: center;
            overflow-wrap: break-word;
            word-wrap: break-word;
        ">
            ⬆️ <strong>Your Assignment:</strong><br>
            Complete the exercises in your <em>workbook</em> for this chapter.
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_link(label: str, url: str) -> None:
    """Render a bullet link."""

    st.markdown(f"- [{label}]({url})")
