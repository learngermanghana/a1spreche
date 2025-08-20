# ==== Standard Library ====
import atexit
import base64
import calendar
import difflib
import hashlib
import html as html_stdlib
import io
import json
import math
import os
import random
import re
import sqlite3
import tempfile
import time
import urllib.parse as _urllib
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

# ==== Third-Party Packages ====
import bcrypt
import firebase_admin
import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st
import warnings
import streamlit.components.v1 as components
from docx import Document
from firebase_admin import credentials, firestore
from fpdf import FPDF
from gtts import gTTS
from openai import OpenAI
from streamlit.components.v1 import html as st_html
from streamlit_cookies_manager import EncryptedCookieManager
from streamlit_quill import st_quill

# ==== Email (Gmail via SMTP) ====
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ------------------------------------------------------------------------------
# Page config MUST be the first Streamlit call
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Falowen – Your German Conversation Partner",
    page_icon="👋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# Silence the st.cache deprecation banner & provide a compat shim
# ------------------------------------------------------------------------------
try:
    try:
        from streamlit.errors import StreamlitDeprecationWarning as _StDepWarn
    except Exception:
        try:
            from streamlit import StreamlitDeprecationWarning as _StDepWarn
        except Exception:
            _StDepWarn = DeprecationWarning

    warnings.filterwarnings(
        "ignore",
        r".*st\.cache is deprecated and will be removed soon.*",
        category=_StDepWarn,
    )
    warnings.filterwarnings(
        "ignore",
        r".*st\.cache is deprecated and will be removed soon.*",
        category=DeprecationWarning,
    )
except Exception:
    pass

def _cache_compat(*dargs, **dkwargs):
    allow_mut = bool(dkwargs.pop("allow_output_mutation", False))
    decorator = st.cache_resource if allow_mut else st.cache_data
    return decorator(*dargs, **dkwargs)

try:
    if getattr(getattr(st, "cache", None), "__name__", "") != "_cache_compat":
        st.cache = _cache_compat  # monkey-patch only if not already our shim
except Exception:
    pass

# ------------------------------------------------------------------------------
# Email creds
# ------------------------------------------------------------------------------
EMAIL_ADDRESS = st.secrets.get("SMTP_FROM", "learngermanghana@gmail.com")
EMAIL_PASSWORD = st.secrets.get("SMTP_PASSWORD", "mwxlxvvtnrcxqdml")  # Gmail App Password

def send_reset_email(to_email: str, reset_link: str) -> bool:
    """Send a password reset email. Returns True on success, False otherwise."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = "Falowen Password Reset"

        html = f"""
        <p>Hello,</p>
        <p>You requested to reset your password. Click below to continue:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>This link will expire in 1 hour.</p>
        <br>
        <p>– Falowen Team</p>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, [to_email], msg.as_string())
        return True
    except Exception as e:
        st.error(f"❌ Failed to send reset email: {e}")
        return False

# Prefer Apps Script reset page for password updates
GAS_RESET_URL = st.secrets.get(
    "GAS_RESET_URL",
    "https://script.google.com/macros/s/AKfycbwdgYJtya39qzBZaXdUqkk1i2_LIHna5CN-lHYveq7O1yG46KghKZWKNKqGYlh_xyZU/exec?token=<THE_TOKEN>"
)

def build_gas_reset_link(token: str) -> str:
    """
    Build a valid Apps Script reset link with ?token=.
    Supports either a placeholder (<THE_TOKEN>) or a bare /exec URL.
    """
    url = GAS_RESET_URL.strip()
    if "<THE_TOKEN>" in url:
        return url.replace("<THE_TOKEN>", _urllib.quote(token, safe=""))

    parts = _urllib.urlparse(url)
    qs = dict(_urllib.parse_qsl(parts.query, keep_blank_values=True))
    qs["token"] = token
    new_query = _urllib.urlencode(qs, doseq=True)
    return _urllib.urlunparse(parts._replace(query=new_query))

# ------------------------------------------------------------------------------
# Firebase init (Firestore)
# ------------------------------------------------------------------------------
try:
    if not firebase_admin._apps:   # guard against re-init
        cred_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"Firebase init failed: {e}")
    st.stop()

# ------------------------------------------------------------------------------
# Top spacing + chrome (tighter)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
/* Remove Streamlit's top padding */
[data-testid="stAppViewContainer"] > .main .block-container {
  padding-top: 0 !important;
}
/* First rendered block — keep a small gap only */
[data-testid="stAppViewContainer"] .main .block-container > div:first-child {
  margin-top: 0 !important;
  margin-bottom: 8px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}
/* If that first block is an iframe, collapse it completely */
[data-testid="stAppViewContainer"] .main .block-container > div:first-child [data-testid="stIFrame"] {
  display: block;
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  overflow: hidden !important;
}
/* Keep hero flush and compact */
.hero { margin-top: 2px !important; margin-bottom: 4px !important; padding-top: 6px !important; display: flow-root; }
.hero h1:first-child { margin-top: 0 !important; }
/* Trim default gap above Streamlit tabs */
[data-testid="stTabs"] { margin-top: 8px !important; }
/* Hide default Streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Compatibility alias
html = st_html

# ---- PWA head helper (define BEFORE you call it) ----
BASE = st.secrets.get("PUBLIC_BASE_URL", "")
_manifest = f'{BASE}/static/manifest.webmanifest' if BASE else "/static/manifest.webmanifest"
_icon180  = f'{BASE}/static/icons/falowen-180.png' if BASE else "/static/icons/falowen-180.png"

def _inject_meta_tags():
    """Inject PWA meta + register the service worker once per session."""
    if st.session_state.get("_pwa_head_done"):
        return
    components.html(f"""
      <link rel="manifest" href="{_manifest}">
      <link rel="apple-touch-icon" href="{_icon180}">
      <meta name="apple-mobile-web-app-capable" content="yes">
      <meta name="apple-mobile-web-app-title" content="Falowen">
      <meta name="apple-mobile-web-app-status-bar-style" content="black">
      <meta name="theme-color" content="#000000">
      <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
      <script>
        if ('serviceWorker' in navigator) {{
          navigator.serviceWorker.register('/sw.js', {{ scope: '/' }}).catch(()=>{{}});
        }}
      </script>
    """, height=0)
    st.session_state["_pwa_head_done"] = True

# inject now (kept close to definition so it runs early)
_inject_meta_tags()

# --- State bootstrap ---
def _bootstrap_state():
    defaults = {
        "logged_in": False,
        "student_row": None,
        "student_code": "",
        "student_name": "",
        "session_token": "",
        "cookie_synced": False,
        "__last_refresh": 0.0,
        "__ua_hash": "",
        "_oauth_state": "",
        "_oauth_code_redeemed": "",
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)
_bootstrap_state()

# ==== Hide Streamlit chrome ====
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Firestore sessions (server-side auth state)
# ------------------------------------------------------------------------------
SESSIONS_COL = "sessions"
SESSION_TTL_MIN = 60 * 24 * 14         # 14 days
SESSION_ROTATE_AFTER_MIN = 60 * 24 * 7 # 7 days

def _rand_token(nbytes: int = 48) -> str:
    return base64.urlsafe_b64encode(os.urandom(nbytes)).rstrip(b"=").decode("ascii")

def create_session_token(student_code: str, name: str, ua_hash: str = "") -> str:
    now = time.time()
    token = _rand_token()
    db.collection(SESSIONS_COL).document(token).set({
        "student_code": (student_code or "").strip().lower(),
        "name": name or "",
        "issued_at": now,
        "expires_at": now + (SESSION_TTL_MIN * 60),
        "ua_hash": ua_hash or "",
    })
    return token

def validate_session_token(token: str, ua_hash: str = "") -> dict | None:
    if not token:
        return None
    try:
        snap = db.collection(SESSIONS_COL).document(token).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        if float(data.get("expires_at", 0)) < time.time():
            return None
        if data.get("ua_hash") and ua_hash and data["ua_hash"] != ua_hash:
            return None
        return data
    except Exception:
        return None

def refresh_or_rotate_session_token(token: str) -> str:
    try:
        ref = db.collection(SESSIONS_COL).document(token)
        snap = ref.get()
        if not snap.exists:
            return token
        data = snap.to_dict() or {}
        now = time.time()
        # Extend TTL
        ref.update({"expires_at": now + (SESSION_TTL_MIN * 60)})
        # Rotate if old
        if now - float(data.get("issued_at", now)) > (SESSION_ROTATE_AFTER_MIN * 60):
            new_token = _rand_token()
            db.collection(SESSIONS_COL).document(new_token).set({
                **data},
                merge=True
            )
            db.collection(SESSIONS_COL).document(new_token).update({
                "issued_at": now,
                "expires_at": now + (SESSION_TTL_MIN * 60),
            })
            try:
                ref.delete()
            except Exception:
                pass
            return new_token
    except Exception:
        pass
    return token

def destroy_session_token(token: str) -> None:
    try:
        db.collection(SESSIONS_COL).document(token).delete()
    except Exception:
        pass

# ------------------------------------------------------------------------------
# OpenAI (used elsewhere in app)
# ------------------------------------------------------------------------------
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("Missing OpenAI API key. Please add OPENAI_API_KEY in Streamlit secrets.")
    st.stop()
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------------------------------------------------------
# DB (SQLite) and initialization
# ------------------------------------------------------------------------------
def get_connection():
    if "conn" not in st.session_state:
        st.session_state["conn"] = sqlite3.connect(
            "vocab_progress.db", check_same_thread=False
        )
        atexit.register(st.session_state["conn"].close)
    return st.session_state["conn"]

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vocab_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT,
            name TEXT,
            level TEXT,
            word TEXT,
            student_answer TEXT,
            is_correct INTEGER,
            date TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS schreiben_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT,
            name TEXT,
            level TEXT,
            essay TEXT,
            score INTEGER,
            feedback TEXT,
            date TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sprechen_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT,
            name TEXT,
            level TEXT,
            teil TEXT,
            message TEXT,
            score INTEGER,
            feedback TEXT,
            date TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS exam_progress (
            student_code TEXT,
            level TEXT,
            teil TEXT,
            remaining TEXT,
            used TEXT,
            PRIMARY KEY (student_code, level, teil)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS my_vocab (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT,
            level TEXT,
            word TEXT,
            translation TEXT,
            date_added TEXT
        )
    """)
    for tbl in ["sprechen_usage", "letter_coach_usage", "schreiben_usage"]:
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {tbl} (
                student_code TEXT,
                date TEXT,
                count INTEGER,
                PRIMARY KEY (student_code, date)
            )
        """)
    conn.commit()
init_db()

# ------------------------------------------------------------------------------
# Constants & helpers
# ------------------------------------------------------------------------------
FALOWEN_DAILY_LIMIT = 20
VOCAB_DAILY_LIMIT = 20
SCHREIBEN_DAILY_LIMIT = 5

def get_sprechen_usage(student_code):
    today = str(date.today())
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT count FROM sprechen_usage WHERE student_code=? AND date=?",
        (student_code, today)
    )
    row = c.fetchone()
    return row[0] if row else 0

def inc_sprechen_usage(student_code):
    today = str(date.today())
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO sprechen_usage (student_code, date, count)
        VALUES (?, ?, 1)
        ON CONFLICT(student_code, date)
        DO UPDATE SET count = count + 1
        """,
        (student_code, today)
    )
    conn.commit()

def has_sprechen_quota(student_code, limit=FALOWEN_DAILY_LIMIT):
    return get_sprechen_usage(student_code) < limit

# ------------------------------------------------------------------------------
# YouTube helpers
# ------------------------------------------------------------------------------
YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", "AIzaSyBA3nJi6dh6-rmOLkA4Bb0d7h0tLAp7xE4")

YOUTUBE_PLAYLIST_IDS = {
    "A1": ["PL5vnwpT4NVTdwFarD9kwm1HONsqQ11l-b"],
    "A2": ["PLs7zUO7VPyJ7YxTq_g2Rcl3Jthd5bpTdY", "PLquImyRfMt6dVHL4MxFXMILrFh86H_HAc", "PLs7zUO7VPyJ5Eg0NOtF9g-RhqA25v385c"],
    "B1": ["PLs7zUO7VPyJ5razSfhOUVbTv9q6SAuPx-", "PLB92CD6B288E5DB61"],
    "B2": ["PLs7zUO7VPyJ5XMfT7pLvweRx6kHVgP_9C", "PLs7zUO7VPyJ6jZP-s6dlkINuEjFPvKMG0", "PLs7zUO7VPyJ4SMosRdB-35Q07brhnVToY"],
}

@st.cache_data(ttl=43200)
def fetch_youtube_playlist_videos(playlist_id, api_key=YOUTUBE_API_KEY):
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {"part": "snippet", "playlistId": playlist_id, "maxResults": 50, "key": api_key}
    videos, next_page = [], ""
    while True:
        if next_page:
            params["pageToken"] = next_page
        response = requests.get(base_url, params=params, timeout=12)
        data = response.json()
        for item in data.get("items", []):
            vid = item["snippet"]["resourceId"]["videoId"]
            videos.append({"title": item["snippet"]["title"], "url": f"https://www.youtube.com/watch?v={vid}"})
        next_page = data.get("nextPageToken")
        if not next_page:
            break
    return videos
