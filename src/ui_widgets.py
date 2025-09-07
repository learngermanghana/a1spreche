"""Reusable Streamlit UI widgets."""
from __future__ import annotations

import hashlib
import json
import streamlit as st
import streamlit.components.v1 as components


def render_google_button_once(auth_url: str, key: str = "primary") -> None:
    """Render a branded Google button once per session key."""
    ss_key = f"__google_btn_rendered::{key}"
    if st.session_state.get(ss_key):
        return
    st.session_state[ss_key] = True
    btn_html = f"""
    <div class="flex-center g-btn-wrap">
      <a href="{auth_url}" class="no-decoration">
        <button aria-label="Continue with Google" class="btn btn-google">
          <span class="google-logo">
            <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48' width='18' height='18'>
              <path fill='#FFC107' d='M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12
              s5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24
              s8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z'/>
              <path fill='#FF3D00' d='M6.306,14.691l6.571,4.819C14.655,16.108,18.961,13,24,13c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657
              C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z'/>
              <path fill='#4CAF50' d='M24,44c5.185,0,9.93-1.986,13.49-5.221l-6.232-5.268C29.218,35.091,26.715,36,24,36
              c-5.202,0-9.619-3.317-11.273-7.953l-6.5,5.012C9.545,39.556,16.227,44,24,44z'/>
              <path fill='#1976D2' d='M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.115,5.512c0.001-0.001,0.002-0.001,0.003-0.002
              l6.232,5.268C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z'/>
            </svg>
          </span>
          Continue with Google
        </button>
      </a>
    </div>
    """
    st.markdown(btn_html, unsafe_allow_html=True)



def render_google_signin_once(auth_url: str, full_width: bool = True) -> None:
    """Render a single Google sign-in button with guard."""
    if not auth_url or st.session_state.get("_google_btn_rendered"):
        return
    btn_html = f"""
    <style>
      .g-wrap {{
        display:flex; justify-content:center; margin:8px 0 12px;
      }}
      .g-btn {{
        appearance:none; -webkit-appearance:none;
        display:inline-flex; align-items:center; gap:10px;
        background:#ffffff; color:#1f2937;
        border:1px solid rgba(2,6,23,.12);
        border-radius:12px; padding:12px 18px;
        font-weight:800; font-size:1.05rem; letter-spacing:.01em;
        box-shadow:0 2px 8px rgba(2,6,23,.06);
        cursor:pointer; text-decoration:none;
        transition: box-shadow .18s ease, transform .02s ease, border-color .18s ease;
        line-height:1;
        {"width:100%; justify-content:center;" if full_width else ""}
      }}
      .g-btn:hover {{
        border-color:#93c5fd;
        box-shadow:0 6px 18px rgba(2,6,23,.12);
      }}
      .g-btn:active {{ transform: translateY(1px); }}
      .g-logo {{ width:20px; height:20px; display:inline-block; }}
      @media (prefers-color-scheme: dark) {{
        .g-btn {{ background:#ffffff; color:#111827; }}
      }}
    </style>
    <div class="g-wrap">
      <a class="g-btn" href="{auth_url}">
        <svg class="g-logo" viewBox="0 0 533.5 544.3" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path fill="#4285F4" d="M533.5 278.4a320 320 0 0 0-5.1-57.1H272.1v108.1h146.9a125.5 125.5 0 0 1-54.4 82.4v68.3h87.9c51.4-47.3 80.9-117.1 80.9-201.7z"/>
          <path fill="#34A853" d="M272.1 544.3c73.4 0 135-24.2 180-65.6l-87.9-68.3c-24.4 16.4-55.8 26-92.1 26-70.7 0-130.6-47.7-152.1-111.7H29.2v70.2a272.1 272.1 0 0 0 242.9 149.4z"/>
          <path fill="#FBBC05" d="M120 325.7a163.1 163.1 0 0 1 0-107.1V148.4H29.2a272.1 272.1 0 0 0 0 247.5l90.8-70.2z"/>
          <path fill="#EA4335" d="M272.1 106.8c40 0 76 13.8 104.3 40.9l78.2-78.2C406.8 25.1 345.2 0 272.1 0 149.2 0 39.9 69.4 29.2 148.4l90.8 70.2C141.5 154.5 201.4 106.8 272.1 106.8z"/>
        </svg>
        Continue with Google
      </a>
    </div>
    """
    try:
        components.html(btn_html, height=72, scrolling=False)
    except Exception:
        st.link_button("Continue with Google", auth_url, use_container_width=full_width)
    st.session_state["_google_btn_rendered"] = True


def render_google_brand_button_once(auth_url: str, center: bool = True) -> None:
    """Render a branded Google call-to-action only once."""
    if not auth_url or st.session_state.get("_google_cta_rendered"):
        return
    align = "text-align:center;" if center else ""
    st.markdown(
        f"""
        <div style="{align} margin:12px 0;">
          <a href="{auth_url}" style="text-decoration:none;">
            <div role="button"
                 style="display:inline-flex;align-items:center;gap:10px;"
                        "background:#fff;border:1px solid #dadce0;border-radius:8px;"
                        "padding:10px 18px;font-weight:700;color:#3c4043;"
                        "box-shadow:0 1px 2px rgba(0,0,0,.05);">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"
                   width="22" height="22" aria-hidden="true">
                <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.6 32.9 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.9 6 29.7 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20c10 0 18.6-7.3 19.9-16.8.1-.8.2-1.7.2-2.7 0-1-.1-1.9-.5-3z"/>
                <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.3 16.5 18.8 12 24 12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.9 6 29.7 4 24 4 16.1 4 9.2 8.6 6.3 14.7z"/>
                <path fill="#4CAF50" d="M24 44c5.2 0 10-2 13.5-5.3l-6.2-5.1C29.3 36 26.8 37 24 37c-5.3 0-9.7-3.1-11.6-7.5l-6.6 5.1C9.1 40.3 16.1 44 24 44z"/>
                <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-1.3 3.4-4.5 6-8.3 6-2.8 0-5.3-1-7.1-2.9l-6.6 5.1C15.1 40.9 19.3 43 24 43c10 0 18.6-7.3 19.9-16.8.1-.8.2-1.7.2-2.7 0-1-.1-1.9-.5-3z"/>
              </svg>
              Continue with Google
            </div>
          </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_google_cta_rendered"] = True


def render_announcements(announcements: list) -> None:
    """Render announcement cards from a list of data."""
    if not announcements:
        st.info("📣 No new updates to show.")
        return
    _html = """
    <style>
      :root{ --brand:#1d4ed8; --ring:#93c5fd; --text:#0b1220; --muted:#475569; --card:#ffffff;
             --chip-bg:#eaf2ff; --chip-fg:#1e3a8a; --link:#1d4ed8; --shell-border: rgba(2,6,23,.08); }
      @media (prefers-color-scheme: dark){
        :root{ --text:#e5e7eb; --muted:#cbd5e1; --card:#111827; --chip-bg:#1f2937; --chip-fg:#e5e7eb; --link:#93c5fd; --shell-border: rgba(148,163,184,.25); }
      }
      .page-wrap{max-width:1100px;margin:0 auto;padding:0 10px;}
      .ann-title{font-weight:800;font-size:1.05rem;line-height:1.2; padding-left:12px;border-left:5px solid var(--brand);margin:0 0 6px 0;color:var(--text);}
      .ann-shell{border-radius:14px;border:1px solid var(--shell-border);background:var(--card);box-shadow:0 6px 18px rgba(2,6,23,.12);padding:12px 14px;overflow:hidden;}
      .ann-heading{display:flex;align-items:center;gap:10px;margin:0 0 6px 0;font-weight:800;color:var(--text);}
      .ann-chip{font-size:.78rem;font-weight:800;text-transform:uppercase;background:var(--chip-bg);color:var(--chip-fg);padding:4px 9px;border-radius:999px;border:1px solid var(--shell-border);}
      .ann-body{color:var(--muted);margin:0;line-height:1.55;font-size:1rem}
      .ann-actions{margin-top:8px}
      .ann-actions a{color:var(--link);text-decoration:none;font-weight:700}
      .ann-dots{display:flex;gap:12px;justify-content:center;margin-top:12px}
      .ann-dot{width:11px;height:11px;border-radius:999px;background:#9ca3af;opacity:.9;transform:scale(.95);border:none;cursor:pointer;}
      .ann-dot[aria-current="true"]{background:var(--brand);opacity:1;transform:scale(1.22);box-shadow:0 0 0 4px var(--ring)}
    </style>
    <div class="page-wrap">
      <div class="ann-title">📣 New Updates</div>
      <div class="ann-shell" id="ann_shell" aria-live="polite">
        <div id="ann_card">
          <div class="ann-heading"><span class="ann-chip" id="ann_tag" style="display:none;"></span><span id="ann_title"></span></div>
          <p class="ann-body" id="ann_body">loading…</p>
          <div class="ann-actions" id="ann_action" style="display:none;"></div>
        </div>
        <div class="ann-dots" id="ann_dots" role="tablist" aria-label="Announcement selector"></div>
      </div>
    </div>
    <script>
      const data = __DATA__;
      const titleEl = document.getElementById('ann_title');
      const bodyEl  = document.getElementById('ann_body');
      const tagEl   = document.getElementById('ann_tag');
      const actionEl= document.getElementById('ann_action');
      const dotsWrap= document.getElementById('ann_dots');
      let i = 0;
      function setActiveDot(idx){ [...dotsWrap.children].forEach((d,j)=> d.setAttribute('aria-current', j===idx ? 'true':'false')); }
      function render(idx){
        const c = data[idx] || {};
        titleEl.textContent = c.title || '';
        bodyEl.textContent  = c.body  || '';
        if (c.tag){ tagEl.textContent = c.tag; tagEl.style.display=''; } else { tagEl.style.display='none'; }
        if (c.href){ const link = document.createElement('a'); link.href = c.href; link.target = '_blank'; link.rel='noopener'; link.textContent='Open';
          actionEl.textContent=''; actionEl.appendChild(link); actionEl.style.display=''; } else { actionEl.textContent=''; actionEl.style.display='none'; }
        setActiveDot(idx);
      }
      data.forEach((_, idx)=>{ const b=document.createElement('button'); b.className='ann-dot'; b.type='button'; b.setAttribute('role','tab');
        b.setAttribute('aria-label','Slide '+(idx+1)); b.setAttribute('tabindex','0'); b.addEventListener('click', ()=>{ i=idx; render(i); });
        b.addEventListener('keydown', (e)=>{ if(e.key==='Enter'||e.key===' '||e.key==='Spacebar'){ e.preventDefault(); i=idx; render(i); }});
        dotsWrap.appendChild(b); });
      render(i);
    </script>
    """
    try:
        components.html(
            _html.replace("__DATA__", json.dumps(announcements, ensure_ascii=False)),
            height=220,
            scrolling=False,
        )
    except TypeError:
        for a in announcements:
            st.markdown(f"**{a.get('title','')}** — {a.get('body','')}")


def render_announcements_once(data: list, dashboard_active: bool) -> None:
    """Render announcements only when data changes or dashboard is active."""
    data_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
    prev_hash = st.session_state.get("_ann_hash")
    if dashboard_active or data_hash != prev_hash:
        if dashboard_active:
            render_announcements(data)
        st.session_state["_ann_hash"] = data_hash
