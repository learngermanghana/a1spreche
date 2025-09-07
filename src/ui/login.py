"""UI helpers for the Falowen login page and global styling."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from functools import lru_cache

import streamlit as st
import streamlit.components.v1 as components

BASE = st.secrets.get("PUBLIC_BASE_URL", "")
_MANIFEST = f"{BASE}/manifest.webmanifest" if BASE else "/manifest.webmanifest"
_ICON180 = f"{BASE}/static/icons/falowen-180.png" if BASE else "/static/icons/falowen-180.png"

def inject_meta_tags() -> None:
    """Inject PWA meta tags into the page head."""
    if st.session_state.get("_pwa_head_done"):
        return
    snippet = f"""<script>
      (function(){{
        try {{
          var head = document.getElementsByTagName('head')[0];
          var tags = [
            '<link rel="manifest" href="{_MANIFEST}">',
            '<link rel="apple-touch-icon" href="{_ICON180}">',
            '<meta name="apple-mobile-web-app-capable" content="yes">',
            '<meta name="apple-mobile-web-app-title" content="Falowen">',
            '<meta name="apple-mobile-web-app-status-bar-style" content="default">',
            '<meta name="color-scheme" content="light">',
            '<meta name="theme-color" content="#f3f7fb">',
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
          ];
          tags.forEach(function(t){{ head.insertAdjacentHTML('beforeend', t); }});
          if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/sw.js', {{ scope: '/' }}).catch(function(){{}});
          }}
        }} catch(e) {{}}
      }})();
    </script>
    """
    try:
        components.html(snippet, height=1, scrolling=False)
    except Exception:  # pragma: no cover - UI failure
        pass
    st.session_state["_pwa_head_done"] = True

def inject_notice_css() -> None:
    """Inject shared CSS used across the app."""
    st.markdown(
        """
    <style>
      :root{ --chip-border: rgba(148,163,184,.35); }
      @media (prefers-color-scheme: dark){
        :root{ --chip-border: rgba(148,163,184,.28); }
      }

      /* ---- chips (unchanged) ---- */
      .chip { display:inline-flex; align-items:center; gap:8px;
              padding:8px 12px; border-radius:999px; font-weight:700; font-size:.98rem;
              border:1px solid var(--chip-border); }
      .chip-red   { background:#fef2f2; color:#991b1b; border-color:#fecaca; }
      .chip-amber { background:#fff7ed; color:#7c2d12; border-color:#fed7aa; }
      .chip-blue  { background:#eef4ff; color:#2541b2; border-color:#c7d2fe; }
      .chip-gray  { background:#f1f5f9; color:#334155; border-color:#cbd5e1; }

      .pill { display:inline-block; padding:3px 9px; border-radius:999px; font-weight:700; font-size:.92rem; }
      .pill-green  { background:#e6ffed; color:#0a7f33; }
      .pill-purple { background:#efe9ff; color:#5b21b6; }
      .pill-amber  { background:#fff7ed; color:#7c2d12; }

      /* ---- mini-card grid (ensure horizontal cards) ---- */
      .minirow{
        display:grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap:14px;
        margin:10px 0 6px 0;
        align-items:stretch;
      }
      .minicard{
        border:1px solid var(--chip-border);
        border-radius:12px;
        padding:12px;
        background:#fff;
        box-shadow:0 1px 4px rgba(2,6,23,.04);
      }
      .minicard h4 { margin:0 0 6px 0; font-size:1.02rem; color:#0f172a; }
      .minicard .sub { color:#475569; font-size:.92rem; }

      @media (max-width:640px){
        .minicard{ padding:11px; }
      }
    </style>
    """,
        unsafe_allow_html=True,
    )

@lru_cache(maxsize=1)
def load_falowen_login_html() -> str:
    """Load and sanitize the Falowen login hero HTML template."""
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "templates"
        / "falowen_login.html"
    )
    try:
        html = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:  # pragma: no cover - malformed file
        raise RuntimeError("falowen_login.html must be valid UTF-8") from exc
    html = re.sub(r"<aside[\s\S]*?</aside>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"</body>.*", "</body>", html, flags=re.IGNORECASE | re.DOTALL)
    return html

def render_falowen_login(
    google_auth_url: str = "",
    show_google_in_hero: bool = False,
    *,
    st=st,
    components=components,
    logging=logging,
) -> None:
    """Render the Falowen login hero."""
    try:
        html = load_falowen_login_html()
    except Exception:
        st.error("Falowen login template missing or unreadable.")
        logging.exception("Failed to load Falowen login HTML")
        return
    components.html(html, height=720, scrolling=True)

__all__ = [
    "inject_meta_tags",
    "inject_notice_css",
    "load_falowen_login_html",
    "render_falowen_login",
]
