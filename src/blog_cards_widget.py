
from __future__ import annotations
from typing import List, Dict

import streamlit as st
import streamlit.components.v1 as components


def render_blog_cards(items: List[Dict[str, str]], height: int = 380) -> None:
    """Render a responsive card grid with optional images for each blog post.

    Each item: title, href, optional body, optional image.
    """
    if not items:
        st.info("No blog posts available right now.")
        return

    def esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    card_html = []
    for it in items:
        title = esc(it.get("title", ""))
        href = esc(it.get("href", "#"))
        body = esc(it.get("body", ""))
        img = it.get("image") or ""

        img_html = f'<img class="card-img" src="{esc(img)}" alt="">' if img else ""
        card_html.append(
            f'''
            <a class="blog-card" href="{href}" target="_blank" rel="noopener noreferrer">
              <div class="card-img-wrap">
                {img_html}
              </div>
              <div class="card-content">
                <div class="card-title">{title}</div>
                <div class="card-body">{body}</div>
              </div>
            </a>
            '''
        )

    html = f"""
    <div class="falowen-blog-outer">
      <div class="falowen-blog-wrap">
        {''.join(card_html)}
      </div>
    </div>
    <style>
      .falowen-blog-outer {{
        max-width: 1120px;
        margin: 0 auto;
        width: 100%;
        padding: 0 8px;
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
      }}
      .blog-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
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
        .falowen-blog-wrap {{
          grid-template-columns: 1fr 1fr;
        }}
      }}
      @media (max-width: 420px) {{
        .falowen-blog-wrap {{
          grid-template-columns: 1fr;
        }}
      }}
    </style>
    """
    components.html(html, height=height, scrolling=True)
