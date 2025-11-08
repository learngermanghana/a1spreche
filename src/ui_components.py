"""Small reusable UI components for Streamlit."""

from __future__ import annotations

import base64
import json
import logging
from typing import Optional, Union
from uuid import uuid4
from urllib.parse import urlparse, urlunparse
import re

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

try:  # pragma: no cover - dependency might be missing in some environments
    from rapidfuzz import process
except ImportError:  # pragma: no cover
    process = None

# Google Sheet ID for vocabulary lookup
VOCAB_SHEET_ID = "1I1yAnqzSh3DPjwWRh9cdRSfzNSPsi7o4r5Taj9Y36NU"


@st.cache_data(show_spinner=False)
def _load_vocab_sheet(sheet_id: str = VOCAB_SHEET_ID) -> Optional[pd.DataFrame]:
    """Download the vocabulary sheet as a DataFrame.

    Returns ``None`` if the sheet cannot be loaded.
    """

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        return pd.read_csv(url)
    except Exception:  # pragma: no cover - network or parsing issues
        logging.exception("Failed to load vocabulary sheet")
        return None


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
        '''
        ,
        unsafe_allow_html=True,
    )


def render_link(label: str, url: str) -> None:
    """Render a bullet link."""

    st.markdown(f"- [{label}]({url})")


def prepare_audio_url(url: str) -> Optional[str]:
    """Ensure the audio URL uses HTTPS and returns ``audio/mpeg``."""

    if not url:
        return None
    try:
        parsed = urlparse(str(url))
        if parsed.scheme not in {"http", "https"}:
            return None
        if parsed.scheme == "http":
            parsed = parsed._replace(scheme="https")
            url = urlunparse(parsed)
        resp = requests.head(url, allow_redirects=True, timeout=5)
        ctype = resp.headers.get("Content-Type", "")
        if ctype.split(";")[0].strip().lower() != "audio/mpeg":
            return None
        return url
    except Exception:  # pragma: no cover - best effort
        logging.exception("Failed to verify audio URL")
        return None


def render_audio_player(source: Union[str, bytes], *, verified: bool = False) -> None:
    """Render an HTML5 audio player with mobile-friendly attributes."""

    if isinstance(source, (bytes, bytearray)):
        b64 = base64.b64encode(source).decode()
        url = f"data:audio/mpeg;base64,{b64}"
    else:
        url = source if verified else prepare_audio_url(source)
        if not url:
            st.markdown(f"[⬇️ Download MP3]({source})")
            return
    ua = ""
    is_ios = False
    try:  # pragma: no cover - environment dependent
        from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore

        ctx = get_script_run_ctx()
        if ctx and getattr(ctx, "session_info", None):
            client = getattr(ctx.session_info, "client", None)
            ua = getattr(client, "user_agent", "") if client else ""
            if ua:
                is_ios = re.search(r"iPad|iPhone|iPod", ua) is not None
    except Exception:
        is_ios = False

    if is_ios:
        st.caption(
            "ℹ️ iPhone and iPad browsers may not play audio inline. Tap the download link to listen."
        )

    element_id = f"audio_{uuid4().hex}"
    html = f"""
    <audio id="{element_id}" controls preload="none" playsinline controlsList="nodownload" src="{url}"></audio>
    <div id="{element_id}_dl" style="display:none">
      <a href="{url}" download>Download MP3</a>
    </div>
    <script>
    const audio = document.getElementById('{element_id}');
    const dl = document.getElementById('{element_id}_dl');
    audio.addEventListener('error', () => dl.style.display = 'block');
    if (/iPad|iPhone|iPod/.test(navigator.userAgent)) dl.style.display = 'block';
    </script>
    """
    components.html(html, height=80)


def render_vocab_lookup(key: str, context_label: Optional[str] = None) -> None:
    """Render a small vocabulary lookup widget.

    Parameters
    ----------
    key:
        Unique key so Streamlit state doesn't clash across lessons.
    context_label:
        Optional label providing context (e.g. lesson info) for the lookup.
    """

    header = "#### 📖 Mini Dictionary"
    if context_label:
        header += f" – {context_label}"
    st.markdown(header)
    st.caption("Search words from this assignment")

    helper_url = (
        "https://www.falowen.app/?tab=Chat+%E2%80%A2+Grammar+%E2%80%A2+Exams"
        "&t=ijw4H_7TnhTgX0swRfZ3BqBqiilBBfV3spz9U1cwS5AvLUJDwVYRbnc3I_HuQoss"
    )
    translate_caption = (
        'Need help beyond a single word? Try the '
        '<a href="https://chat.grammar.page" target="_blank">Grammar Helper</a> '
        'or <a href="https://chat.grammar.page" target="_blank">Assignment Helper</a>.'
    )

    df = _load_vocab_sheet()
    if df is None:
        st.info("Vocabulary lookup currently unavailable.")
        st.caption(translate_caption, unsafe_allow_html=True)
        return

    st.caption(translate_caption, unsafe_allow_html=True)

    query = st.text_input("🔎 Search vocabulary", key=f"vocab-{key}")
    if not query:
        return

    mask = df.apply(
        lambda row: row.astype(str).str.contains(query, case=False, na=False).any(),
        axis=1,
    )
    search_col = next(
        (col for col in ["German", "Word"] if col in df.columns), df.columns[0]
    )
    translation_col = next(
        (
            col
            for col in ["English", "Translation", "Meaning"]
            if col in df.columns and col != search_col
        ),
        df.columns[1] if len(df.columns) > 1 else search_col,
    )

    columns = [search_col, translation_col]
    for col in ["Audio", "Audio Link"]:
        if col in df.columns and col not in columns:
            columns.append(col)

    results = df.loc[mask, columns]

    if results.empty and process is not None:
        choices = df[search_col].dropna().astype(str).tolist()
        fuzzy_matches = process.extract(query, choices, limit=5)
        matched_values = [match[0] for match in fuzzy_matches]
        results = df[df[search_col].isin(matched_values)][columns]
        
    if results.empty:
        st.write("No matches found.")
    else:
        for _, row in results.iterrows():
            word = row[search_col]
            meaning = row[translation_col]
            audio_url = row.get("Audio")
            if not audio_url or pd.isna(audio_url):
                audio_url = row.get("Audio Link")
            audio_url = prepare_audio_url(audio_url) if audio_url else None

            line = f"- **{word}** – {meaning}"
            if audio_url:
                line += f" [▶️]({audio_url}) [⬇️]({audio_url})"
            st.markdown(line)
            if audio_url:
                try:  # pragma: no cover - best effort on mobile browsers
                    render_audio_player(audio_url, verified=True)
                except Exception:
                    logging.exception("Failed to play audio")


def render_reviews() -> None:
    """Render a carousel of student reviews."""

    REVIEWS = [
        {
            "quote": "Falowen helped me pass A2 in 8 weeks. The assignments and feedback were spot on.",
            "author": "Ama",
            "location": "Accra, Ghana 🇬🇭",
            "level": "A2",
            "time": "20 weeks",
            "used": ["Course Book", "Assignments", "Results emails"],
            "outcome": "Passed Goethe A2",
        },
        {
            "quote": "The Course Book and Results emails keep me consistent. The vocab trainer is brilliant.",
            "author": "Tunde",
            "location": "Lagos, Nigeria 🇳🇬",
            "level": "B1",
            "time": "30 weeks",
            "used": ["Vocab Trainer", "Results emails", "Course Book"],
            "outcome": "Completed B1 modules",
        },
        {
            "quote": "Clear lessons, easy submissions, and I get notified quickly when marked.",
            "author": "Mariama",
            "location": "Freetown, Sierra Leone 🇸🇱",
            "level": "A1",
            "time": "10 weeks",
            "used": ["Assignments", "Course Book"],
            "outcome": "A1 basics completed",
        },
        {
            "quote": "I like the locked submissions and the clean Results tab.",
            "author": "Kwaku",
            "location": "Kumasi, Ghana 🇬🇭",
            "level": "B2",
            "time": "40 weeks",
            "used": ["Results tab", "Assignments"],
            "outcome": "B2 writing improved",
        },
    ]

    _html = """
    <div class="page-wrap" style="max-width:900px;margin-top:8px;">
      <section id="reviews" aria-label="Student stories" class="rev-wrap" tabindex="-1">
        <header class="rev-head">
          <h3 class="rev-title">Student stories</h3>
          <div class="rev-cta">
            <button class="rev-btn" id="rev_prev" aria-label="Previous review" title="Previous">◀</button>
            <button class="rev-btn" id="rev_next" aria-label="Next review" title="Next">▶</button>
          </div>
        </header>

        <article class="rev-card" aria-live="polite" aria-atomic="true">
          <blockquote id="rev_quote" class="rev-quote"></blockquote>
          <div class="rev-meta">
            <div class="rev-name" id="rev_author"></div>
            <div class="rev-sub"  id="rev_location"></div>
          </div>

          <div class="rev-badges">
            <span class="badge" id="rev_level"></span>
            <span class="badge" id="rev_time"></span>
            <span class="badge badge-ok" id="rev_outcome"></span>
          </div>

          <div class="rev-used" id="rev_used" aria-label="Features used"></div>
        </article>

        <nav class="rev-dots" aria-label="Slide indicators" id="rev_dots"></nav>
      </section>
    </div>

    <style>
      .rev-wrap{
        background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:14px;
        box-shadow:0 4px 16px rgba(0,0,0,.05);
      }
      .rev-head{ display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
      .rev-title{ margin:0; font-size:1.05rem; color:#25317e; }
      .rev-cta{ display:flex; gap:6px; }
      .rev-btn{
        background:#eef3fc; border:1px solid #cbd5e1; border-radius:8px; padding:4px 10px; cursor:pointer;
        font-weight:700;
      }
      .rev-btn:hover{ background:#e2e8f0; }

      .rev-card{ position:relative; min-height:190px; }
      .rev-quote{ font-size:1.06rem; line-height:1.45; margin:4px 0 10px 0; color:#0f172a; }
      .rev-meta{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:8px; }
      .rev-name{ font-weight:700; color:#1e293b; }
      .rev-sub{ color:#475569; }

      .rev-badges{ display:flex; gap:6px; flex-wrap:wrap; margin:6px 0 8px; }
      .badge{
        display:inline-block; background:#f1f5f9; border:1px solid #e2e8f0; color:#0f172a;
        padding:4px 8px; border-radius:999px; font-size:.86rem; font-weight:600;
      }
      .badge-ok{ background:#ecfdf5; border-color:#bbf7d0; color:#065f46; }

      .rev-used{ display:flex; gap:6px; flex-wrap:wrap; }
      .rev-used .chip{
        background:#eef2ff; border:1px solid #c7d2fe; color:#3730a3;
        padding:3px 8px; border-radius:999px; font-size:.82rem; font-weight:600;
      }

      .rev-dots{ display:flex; gap:6px; justify-content:center; margin-top:10px; }
      .rev-dot{
        width:8px; height:8px; border-radius:999px; background:#cbd5e1; border:none; padding:0; cursor:pointer; touch-action:manipulation;
      }
      .rev-dot[aria-current="true"]{ background:#25317e; }
      .fade{ opacity:0; transform:translateY(4px); transition:opacity .28s ease, transform .28s ease; }
      .fade.show{ opacity:1; transform:none; }
      @media (prefers-reduced-motion: reduce){ .fade{ transition:none; opacity:1; transform:none; } }
    </style>

    <script>
      const DATA = __DATA__;
      const q  = (id) => document.getElementById(id);
      const qs = (sel) => document.querySelector(sel);
      const wrap = qs("#reviews");
      const quote = q("rev_quote");
      const author = q("rev_author");
      const locationEl = q("rev_location");
      const level = q("rev_level");
      const time  = q("rev_time");
      const outcome = q("rev_outcome");
      const used = q("rev_used");
      const dots = q("rev_dots");
      const prevBtn = q("rev_prev");
      const nextBtn = q("rev_next");

      let i = 0, timer = null, hovered = false;
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      function setUsedChips(items){
        used.innerHTML = "";
        (items || []).forEach(t => {
          const s = document.createElement("span");
          s.className = "chip";
          s.textContent = t;
          used.appendChild(s);
        });
      }

      function bindQuick(el, handler){
        el.addEventListener("click", handler);
        el.addEventListener("pointerdown", (e)=>{
          if(e.pointerType !== "mouse"){ e.preventDefault(); handler(); }
        });
      }

      function setDots(){
        dots.innerHTML = "";
        DATA.forEach((_, idx) => {
          const b = document.createElement("button");
          b.className = "rev-dot";
          b.setAttribute("aria-label", "Go to review " + (idx+1));
          if(idx === i) b.setAttribute("aria-current","true");
          bindQuick(b, () => { i = idx; show(true); restart(); });
          dots.appendChild(b);
        });
      }

      function show(animate){
        const c = DATA[i];
        quote.textContent = '"' + (c.quote || '') + '"';
        author.textContent = c.author ? c.author + ' — ' : '';
        locationEl.textContent = c.location || '';
        level.textContent = 'Level: ' + (c.level || '—');
        time.textContent  = 'Time: ' + (c.time  || '—');
        outcome.textContent = c.outcome || '';

        setUsedChips(c.used);
        setDots();

        const card = wrap.querySelector(".rev-card");
        if(animate && !reduced){
          card.classList.remove("show");
          card.classList.add("fade");
          requestAnimationFrame(() => {
            requestAnimationFrame(() => card.classList.add("show"));
          });
        }
      }

      function next(){ i = (i + 1) % DATA.length; show(true); }
      function prev(){ i = (i - 1 + DATA.length) % DATA.length; show(true); }

      function start(){ if(reduced) return; timer = setInterval(() => { if(!hovered) next(); }, 6000); }
      function stop(){ if(timer){ clearInterval(timer); timer = null; } }
      function restart(){ stop(); start(); }

      bindQuick(nextBtn, () => { next(); restart(); });
      bindQuick(prevBtn, () => { prev(); restart(); });
      wrap.addEventListener("mouseenter", () => { hovered = true; });
      wrap.addEventListener("mouseleave", () => { hovered = false; });

      wrap.addEventListener("keydown", (e) => {
        if(e.key === "ArrowRight"){ next(); restart(); }
        if(e.key === "ArrowLeft"){  prev(); restart(); }
      });

      show(false);
      start();
    </script>
    """
    _json = json.dumps(REVIEWS)
    components.html(_html.replace("__DATA__", _json), height=300, scrolling=False)
