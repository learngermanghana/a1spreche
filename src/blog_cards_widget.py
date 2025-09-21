# src/blog_cards_widget.py
from __future__ import annotations
from typing import List, Dict
from bs4 import BeautifulSoup
import html
import streamlit as st
import streamlit.components.v1 as components


def strip_html(s: str) -> str:
    try:
        return BeautifulSoup(s or "", "html.parser").get_text(" ", strip=True)
    except Exception:
        return s or ""


def esc(s: str) -> str:
    # Safer/faster than manual replace chain
    return html.escape(s or "", quote=True)


def safe_http_url(u: str) -> str:
    """Allow only http(s); normalize //example to https://example."""
    u = (u or "").strip()
    if u.startswith("//"):
        u = "https:" + u
    if u.startswith("http://") or u.startswith("https://"):
        return u
    return ""


def render_blog_cards(
    items: List[Dict[str, str]],
    height: int = 380,
    max_width_px: int = 1120,
    fallback_text: str = "Tap to read →",
) -> None:
    if not items:
        st.info("No blog posts available right now.")
        return

    cards: List[str] = []
    for it in items:
        title_txt = it.get("title", "") or ""
        href_txt = it.get("href", "") or "#"

        # Body: strip HTML to plain text; provide a readable fallback if empty
        raw_body = it.get("body", "") or ""
        clean_body = strip_html(raw_body)
        snippet = (clean_body if clean_body else fallback_text)[:220]

        # Image: only allow http(s); otherwise omit
        img_url = safe_http_url(it.get("image") or "")

        title = esc(title_txt)
        href = esc(href_txt)
        body = esc(snippet)

        img_html = (
            f'<img class="card-img" src="{esc(img_url)}" alt="{title}" '
            f'loading="lazy" decoding="async" referrerpolicy="no-referrer">'
            if img_url
            else ""
        )

        cards.append(
            f"""
            <a class="blog-card" href="{href}" target="_blank"
               rel="noopener noreferrer nofollow"
               aria-label="Open blog post: {title}">
              <div class="card-img-wrap">{img_html}</div>
              <div class="card-content">
                <div class="card-title">{title}</div>
                <div class="card-body">{body}</div>
              </div>
            </a>
            """
        )

    html_block = f"""
    <div class="falowen-blog-outer" style="max-width:{max_width_px}px;">
      <div class="falowen-blog-wrap">
        {''.join(cards)}
      </div>
    </div>
    <style>
      .falowen-blog-outer {{
        margin: 0 auto; width: 100%; padding: 0 8px;
      }}
      .falowen-blog-wrap {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 16px;
        width: 100%;
      }}

      .blog-card {{
        display: flex;
        flex-direction: column;
        background: rgba(255,255,255,0.96);
        border-radius: 16px;
        text-decoration: none;
        border: 1px solid rgba(0,0,0,0.06);
        overflow: hidden;
        transition: transform 120ms ease, box-shadow 120ms ease;
        outline: none;
      }}
      .blog-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
      }}
      .blog-card:focus-visible {{
        box-shadow: 0 0 0 3px rgba(59,130,246,0.5); /* focus ring */
        transform: translateY(-1px);
      }}

      .card-img-wrap {{
        position: relative;
        width: 100%;
        aspect-ratio: 16/9;
        background: linear-gradient(180deg, rgba(0,0,0,0.05), rgba(0,0,0,0.02));
        overflow: hidden;
      }}
      .card-img {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
      }}

      .card-content {{
        padding: 12px 14px 14px;
      }}
      .card-title {{
        font-weight: 700;
        font-size: 15px;
        line-height: 1.2;
        margin-bottom: 6px;
        color: #0f172a;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        min-height: 2.4em;
      }}
      .card-body {{
        font-size: 13px;
        color: #475569;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        min-height: 3.6em;
      }}

      @media (max-width: 640px) {{
        .falowen-blog-wrap {{ grid-template-columns: 1fr 1fr; }}
      }}
      @media (max-width: 420px) {{
        .falowen-blog-wrap {{ grid-template-columns: 1fr; }}
      }}
    </style>
    <script>
      (() => {{
        let lastHeight = 0;
        const updateHeight = () => {{
          const outer = document.querySelector('.falowen-blog-outer');
          if (!outer) return;
          const height = Math.ceil(outer.getBoundingClientRect().height);
          if (!height || height === lastHeight) return;
          lastHeight = height;
          document.body.style.minHeight = height + 'px';
          document.documentElement.style.minHeight = height + 'px';
          if (window.parent && window.parent !== window) {{
            window.parent.postMessage({{ type: 'streamlit:setFrameHeight', height }}, '*');
          }}
        }};

        const init = () => {{
          const outer = document.querySelector('.falowen-blog-outer');
          if (!outer) {{
            window.requestAnimationFrame(init);
            return;
          }}
          updateHeight();
          const observer = new ResizeObserver(() => window.requestAnimationFrame(updateHeight));
          observer.observe(outer);
          window.addEventListener('load', updateHeight, {{ once: true }});
        }};

        if ('ResizeObserver' in window) {{
          init();
        }} else {{
          window.addEventListener('load', updateHeight);
        }}
      }})();
    </script>
    """
    components.html(html_block, height=height, scrolling=False)
