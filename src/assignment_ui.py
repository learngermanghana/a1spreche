"""Assignment results and resources tab helpers."""

from __future__ import annotations

import base64 as _b64
import io
import os
import re
import tempfile
from datetime import date
from typing import Tuple

import pandas as pd
import requests
import streamlit as st
from fpdf import FPDF

from .assignment import linkify_html, _clean_link, _is_http_url
from .schedule import get_level_schedules as _get_level_schedules
# ``load_school_logo`` is defined below; only import QR helper here.
from .pdf_utils import make_qr_code
from .data_loading import load_student_data
from .utils.currency import format_cedis

# URLs for letterhead and watermark images are configurable via environment
# variables so deployments can easily swap in different assets without touching
# the code.
LETTERHEAD_URL = os.getenv(
    "LETTERHEAD_URL",
    "https://via.placeholder.com/600x100.png?text=Letterhead",
)
WATERMARK_URL = os.getenv(
    "WATERMARK_URL",
    "https://drive.google.com/uc?export=download&id=1dEXHtaPBmvnX941GKK-DsTmj3szz2Z5A",
)

# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600)
def _load_assignment_scores_cached() -> pd.DataFrame:
    SHEET_ID = "1BRb8p3Rq0VpFCLSwL4eS9tSgXBo9hSWzfW_J_7W36NQ"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
    df = pd.read_csv(url, dtype=str)
    df.columns = df.columns.str.strip().str.lower()
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def load_assignment_scores() -> pd.DataFrame:
    """Return assignment scores DataFrame cached in session state."""
    if "assignment_scores_df" not in st.session_state:
        st.session_state["assignment_scores_df"] = _load_assignment_scores_cached()
    return st.session_state["assignment_scores_df"]


# ---------------------------------------------------------------------------
# Helpers used by the Results & Resources tab
# ---------------------------------------------------------------------------

# Score labels are reused in the PDF export; keep logic in one place.
def score_label_fmt(score, *, plain: bool = False) -> str:
    try:
        s = float(score)
    except Exception:
        return "" if not plain else "Needs Improvement"
    if s >= 90:
        return "Excellent 🌟" if not plain else "Excellent"
    if s >= 75:
        return "Good 👍" if not plain else "Good"
    if s >= 60:
        return "Sufficient ✔️" if not plain else "Sufficient"
    return "Needs Improvement ❗" if not plain else "Needs Improvement"


def clean_for_pdf(text: str) -> str:
    import unicodedata as _ud

    if not isinstance(text, str):
        text = str(text)
    text = _ud.normalize("NFKD", text)
    text = text.replace("\n", " ").replace("\r", " ")
    text = "".join(c if c.isprintable() else "?" for c in text)

    # Ensure the result is compatible with the Latin-1 encoding used by FPDF.
    # Characters outside that range are replaced with ``?`` so encoding will
    # not fail when generating PDFs.

    text = text.encode("latin-1", "replace").decode("latin-1")
    return text


def load_school_logo() -> str:
    """Return path to the school logo image, downloading if necessary."""
    local_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(local_path):
        return local_path

    cache_path = "/tmp/school_logo.png"
    if os.path.exists(cache_path):
        return cache_path

    url = (
        "https://drive.google.com/uc?export=download&id="
        "1xLTtiCbEeHJjrASvFjBgfFuGrgVzg6wU"
    )
    try:  # pragma: no cover - network
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        with open(cache_path, "wb") as fh:
            fh.write(resp.content)
        return cache_path
    except Exception:  # noqa: BLE001 - best effort
        return ""

def _results_csv_url() -> str:
    try:
        u = (
            st.secrets.get("results", {}).get("csv_url", "")
            if hasattr(st, "secrets")
            else ""
        ).strip()
        if u:
            return u
    except Exception:
        pass
    return "https://docs.google.com/spreadsheets/d/1BRb8p3Rq0VpFCLSwL4eS9tSgXBo9hSWzfW_J_7W36NQ/gviz/tq?tqx=out:csv"


@st.cache_data(ttl=600)
def fetch_scores(csv_url: str) -> pd.DataFrame:
    required = ["student_code", "name", "assignment", "score", "date", "level"]
    try:
        resp = requests.get(csv_url, timeout=8)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:  # pragma: no cover - network errors
        st.error(f"Unable to fetch scores: {exc}")
        return pd.DataFrame(columns=required)
    try:
        df = pd.read_csv(io.StringIO(resp.text), engine="python")
    except pd.errors.ParserError as exc:
        st.warning(f"Unable to parse scores: {exc}")
        return pd.DataFrame(columns=required)
    df.columns = [
        str(c).strip().lower().replace("studentcode", "student_code")
        for c in df.columns
    ]
    aliases = {
        "assignment/chapter": "assignment",
        "chapter": "assignment",
        "score (%)": "score",
    }
    for src, dst in aliases.items():
        if src in df.columns and dst not in df.columns:
            df = df.rename(columns={src: dst})
    if not set(required).issubset(df.columns):
        return pd.DataFrame(columns=required)
    df = df.dropna(subset=["student_code", "assignment", "score", "date", "level"])
    return df


def _get_current_student() -> Tuple[str, str, str]:
    row = st.session_state.get("student_row") or {}
    code = (
        row.get("StudentCode")
        or st.session_state.get("student_code", "")
        or ""
    ).strip()
    name = (
        row.get("Name") or st.session_state.get("student_name", "") or ""
    ).strip()
    level = (row.get("Level") or "").strip().upper()
    return code, name, level


def get_assignment_summary(student_code: str, level: str) -> dict:
    """Return missed assignments and next recommendation for a student.

    Parameters
    ----------
    student_code: str
        The student's unique code.
    level: str
        The level to check (e.g., "A1").

    Returns
    -------
    dict
        A dictionary with keys ``missed`` (list of str) and ``next`` (lesson dict
        or ``None``).
    """

    try:
        df = load_assignment_scores()
    except Exception:
        return {"missed": [], "next": None}

    if df.empty or not {"studentcode", "assignment", "level"}.issubset(df.columns):
        return {"missed": [], "next": None}

    code_key = (student_code or "").lower().strip()
    lvl = (level or "").upper().strip()

    df = df[
        (df["studentcode"].astype(str).str.lower().str.strip() == code_key)
        & (df["level"].astype(str).str.upper().str.strip() == lvl)
    ]

    if df.empty:
        return {"missed": [], "next": None}

    schedule = _get_level_schedules().get(lvl, [])

    def _extract_all_nums(chapter_str: str):
        parts = re.split(r"[_\s,;]+", str(chapter_str))
        nums = []
        for part in parts:
            m = re.search(r"\d+(?:\.\d+)?", part)
            if m:
                nums.append(float(m.group()))
        return nums

    completed_nums = set()
    for _, row in df.iterrows():
        for num in _extract_all_nums(row["assignment"]):
            completed_nums.add(num)
    last_num = max(completed_nums) if completed_nums else 0.0

    skipped_assignments = []
    for lesson in schedule:
        chapter_field = lesson.get("chapter", "")
        lesson_nums = _extract_all_nums(chapter_field)
        day = lesson.get("day", "")
        has_assignment = lesson.get("assignment", False)
        for chap_num in lesson_nums:
            if has_assignment and chap_num < last_num and chap_num not in completed_nums:
                skipped_assignments.append(
                    f"Day {day}: Chapter {chapter_field} – {lesson.get('topic','')}"
                )
                break

    def _is_recommendable(lesson: dict) -> bool:
        topic = str(lesson.get("topic", "")).lower()
        return not ("schreiben" in topic and "sprechen" in topic)

    def _extract_max_num(chapter: str):
        nums = re.findall(r"\d+(?:\.\d+)?", str(chapter))
        return max([float(n) for n in nums], default=None)

    completed_chapters = []
    for a in df["assignment"]:
        n = _extract_max_num(a)
        if n is not None:
            completed_chapters.append(n)
    last_num2 = max(completed_chapters) if completed_chapters else 0.0

    next_assignment = None
    for lesson in schedule:
        chap_num = _extract_max_num(lesson.get("chapter", ""))
        if not _is_recommendable(lesson):
            continue
        if chap_num and chap_num > last_num2:
            next_assignment = lesson
            break

    return {"missed": skipped_assignments, "next": next_assignment}


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

def generate_enrollment_letter_pdf(
    student_name: str,
    student_level: str,
    enrollment_start: str,
    enrollment_end: str,
) -> bytes:
    """Generate an enrollment letter as PDF bytes."""

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Insert letterhead at the top of the page
    try:  # pragma: no cover - network use is best effort
        resp = requests.get(LETTERHEAD_URL, timeout=8)
        resp.raise_for_status()
        tmp_lh = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_lh.write(resp.content)
        tmp_lh.flush()
        pdf.image(tmp_lh.name, x=10, y=8, w=pdf.w - 20)
    except Exception:
        pass

    # Centered watermark image
    try:  # pragma: no cover - network use is best effort
        resp = requests.get(WATERMARK_URL, timeout=8)
        resp.raise_for_status()
        tmp_wm = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_wm.write(resp.content)
        tmp_wm.flush()
        wm_w = pdf.w * 0.8
        wm_x = (pdf.w - wm_w) / 2
        wm_y = (pdf.h - wm_w) / 2
        try:
            pdf.set_alpha(0.15)  # type: ignore[attr-defined]
        except Exception:
            pass
        pdf.image(tmp_wm.name, x=wm_x, y=wm_y, w=wm_w)
        try:
            pdf.set_alpha(1)  # type: ignore[attr-defined]
        except Exception:
            pass
    except Exception:
        pass

    pdf.set_y(40)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, clean_for_pdf("Learn Language Education Academy"), ln=1, align="C")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(
        0,
        6,
        clean_for_pdf("https://www.learngermanghana.com | 0205706589 | Accra, Ghana"),
        ln=1,
        align="C",
    )
    pdf.cell(0, 6, clean_for_pdf("Business Reg No: BN173410224"), ln=1, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", size=12)
    body_lines = [
        "To Whom It May Concern,",
        f"{student_name} is officially enrolled in {student_level} at Learn Language Education Academy.",
        f"Enrollment valid from {enrollment_start} to {enrollment_end}.",
        "Business Reg No: BN173410224.",
        "",
        "Yours sincerely,",
        "",
        "Felix Asadu",
        "Director",
        "Learn Language Education Academy",
    ]
    for line in body_lines:
        pdf.multi_cell(0, 8, clean_for_pdf(line))
        pdf.ln(1)

    # QR code
    try:
        qr_payload = (
            f"{student_name}|{student_level}|{enrollment_start}|{enrollment_end}"
        )
        qr_bytes = make_qr_code(qr_payload)
        if qr_bytes:
            tmp_qr = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmp_qr.write(qr_bytes)
            tmp_qr.flush()
            pdf.image(tmp_qr.name, x=pdf.w - 40, y=pdf.h - 50, w=30)
    except Exception:
        pass

    return pdf.output(dest="S").encode("latin1", "replace")


def generate_receipt_pdf(
    student_name: str,
    student_level: str,
    student_code: str,
    contract_start: str,
    paid: float,
    balance: float,
    receipt_date: str,
) -> bytes:
    """Generate a simple payment receipt as PDF bytes with improved fonts."""

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    font_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "font", "DejaVuSans.ttf")
    )
    pdf.add_font("DejaVu", "", font_path, uni=True)

    logo = load_school_logo()
    if logo:
        try:  # pragma: no cover - rendering
            pdf.image(logo, x=10, y=8, w=40)
            pdf.ln(35)
        except Exception:
            pdf.ln(5)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, clean_for_pdf("Payment Receipt"), ln=1, align="C")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(
        0,
        6,
        clean_for_pdf("Learn Language Education Academy"),
        ln=1,
        align="C",
    )
    pdf.cell(
        0,
        6,
        clean_for_pdf("https://www.learngermanghana.com | 0205706589 | Accra, Ghana"),
        ln=1,
        align="C",
    )
    pdf.cell(0, 6, clean_for_pdf("Business Reg No: BN173410224"), ln=1, align="C")
    pdf.ln(10)

    pdf.set_font("DejaVu", size=12)
    lines = [
        f"Student: {student_name} ({student_level})",
        f"Student Code: {student_code}",
        f"Contract Start: {contract_start}",
        f"Amount Paid: {format_cedis(paid)}",
        f"Balance: {format_cedis(balance)}",
        f"Date: {receipt_date}",
    ]
    for line in lines:
        pdf.multi_cell(0, 8, clean_for_pdf(line))
        pdf.ln(2)

    return pdf.output(dest="S").encode("latin1")


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_results_and_resources_tab() -> None:
    """Render the "My Results & Resources" tab."""

    st.markdown(
        """
        <div style="
            padding: 8px 12px;
            background: #17a2b8;
            color: #fff;
            border-radius: 6px;
            text-align: center;
            margin-bottom: 8px;
            font-size: 1.3rem;
        ">
            📊 My Results & Resources
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    GOOGLE_SHEET_CSV = _results_csv_url()

    top_cols = st.columns([1, 1, 2])
    with top_cols[0]:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.success("Cache cleared! Reloading…")
            st.session_state["__refresh"] = st.session_state.get("__refresh", 0) + 1

    df_scores = fetch_scores(GOOGLE_SHEET_CSV)
    required_cols = {
        "student_code",
        "name",
        "assignment",
        "score",
        "date",
        "level",
    }
    if not required_cols.issubset(df_scores.columns):
        st.error("Data format error. Please contact support.")
        st.write("Columns found:", df_scores.columns.tolist())
        st.stop()

    student_code, student_name, guessed_level = _get_current_student()
    code_key = (student_code or "").lower().strip()

    df_user = df_scores[
        df_scores.student_code.astype(str).str.lower().str.strip() == code_key
    ]
    if df_user.empty:
        st.info("No results yet. Complete an assignment to see your scores!")
        level = (guessed_level or "").strip().upper()
        df_lvl = pd.DataFrame(columns=["assignment", "score", "date", "comments", "link"])
        df_display = df_lvl.copy()
        total = completed = 0
        avg_score = best_score = 0.0
        sections = ["Downloads", "Resources"]
    else:
        df_user = df_user.copy()
        df_user["level"] = df_user["level"].astype(str).str.upper().str.strip()
        levels = sorted(df_user["level"].unique())
        level = st.selectbox("Select level:", levels)
        df_lvl = df_user[df_user.level == level].copy()
        df_lvl["score"] = pd.to_numeric(df_lvl["score"], errors="coerce")

        totals = {"A1": 18, "A2": 29, "B1": 28, "B2": 24, "C1": 24}
        total = int(totals.get(level, 0))
        completed = int(df_lvl["assignment"].nunique())
        avg_score = float(df_lvl["score"].mean() or 0)
        best_score = float(df_lvl["score"].max() or 0)

        df_display = (
            df_lvl.sort_values(["assignment", "score"], ascending=[True, False])
            .reset_index(drop=True)
        )
        if "comments" not in df_display.columns:
            df_display["comments"] = ""
        if "link" not in df_display.columns:
            df_display["link"] = ""

        sections = [
            "Overview",
            "My Scores",
            "Badges",
            "Missed & Next",
            "Downloads",
            "Resources",
        ]

    if ("rr_page" not in st.session_state) or (
        st.session_state.get("rr_page") not in sections
    ):
        st.session_state["rr_page"] = sections[0]
    if "rr_prev_page" not in st.session_state:
        st.session_state["rr_prev_page"] = st.session_state["rr_page"]

    def on_rr_page_change() -> None:
        st.session_state["rr_prev_page"] = st.session_state.get("rr_page")

    rr_page = st.radio(
        "Results & Resources section",
        sections,
        horizontal=True,
        key="rr_page",
        on_change=on_rr_page_change,
    )

    if rr_page == "Overview":
        st.subheader("Quick Overview")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Assignments", total)
        c2.metric("Completed", completed)
        c3.metric("Average Score", f"{avg_score:.1f}")
        c4.metric("Best Score", f"{best_score:.0f}")

        st.markdown("---")
        st.markdown("**Latest 5 results**")
        latest = df_display.head(5)
        for _, row in latest.iterrows():
            perf = score_label_fmt(row["score"])
            st.markdown(
                f"""
                <div style="margin-bottom: 12px;">
                    <span style="font-size:1.05em;font-weight:600;">{row['assignment']}</span><br>
                    Score: <b>{row['score']}</b> <span style='margin-left:12px;'>{perf}</span>
                    | Date: {row['date']}
                </div>
                """,
                unsafe_allow_html=True,
            )
        if len(df_display) > 5:
            st.caption("See the **Assignments** tab for the full list and feedback.")

    elif rr_page == "My Scores":
        st.subheader("All Assignments & Feedback")
        base_cols = ["assignment", "score", "date", "comments", "link"]
        for _, row in df_display[base_cols].iterrows():
            perf = score_label_fmt(row["score"])
            comment_html = linkify_html(row["comments"])
            ref_link = _clean_link(row.get("link"))
            show_ref = bool(ref_link) and _is_http_url(ref_link) and pd.notna(
                pd.to_numeric(row["score"], errors="coerce")
            )

            st.markdown(
                f"""
                <div style="margin-bottom: 18px;">
                    <span style="font-size:1.05em;font-weight:600;">{row['assignment']}</span><br>
                    Score: <b>{row['score']}</b> <span style='margin-left:12px;'>{perf}</span>
                    | Date: {row['date']}<br>
                    <div style='margin:8px 0; padding:10px 14px; background:#f2f8fa; border-left:5px solid #007bff; border-radius:7px; color:#333; font-size:1em;'>
                        <b>Feedback:</b> {comment_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if show_ref:
                st.markdown(
                    f'🔍 <a href="{ref_link}" target="_blank" rel="noopener">View answer reference (Lesen & Hören)</a>',
                    unsafe_allow_html=True,
                )
            st.divider()

    elif rr_page == "Badges":
        st.subheader("Badges & Trophies")
        with st.expander("What badges can you earn?", expanded=False):
            st.markdown(
                """
- 🏆 **Completion Trophy**: Finish all assignments for your level.
- 🥇 **Gold Badge**: Maintain an average score above 80.
- 🥈 **Silver Badge**: Average score above 70.
- 🥉 **Bronze Badge**: Average score above 60.
- 🌟 **Star Performer**: Score 85 or higher on any assignment.
"""
            )

        badge_count = 0
        if completed >= total and total > 0:
            st.success("🏆 **Congratulations!** You have completed all assignments for this level!")
            badge_count += 1
        if avg_score >= 90:
            st.info("🥇 **Gold Badge:** Average score above 90!")
            badge_count += 1
        elif avg_score >= 75:
            st.info("🥈 **Silver Badge:** Average score above 75!")
            badge_count += 1
        elif avg_score >= 60:
            st.info("🥉 **Bronze Badge:** Average score above 60!")
            badge_count += 1
        if best_score >= 95:
            st.info("🌟 **Star Performer:** You scored 95 or above on an assignment!")
            badge_count += 1
        if badge_count == 0:
            st.warning("No badges yet. Complete more assignments to earn badges!")

    elif rr_page == "Missed & Next":
        st.subheader("Missed Assignments & Next Recommendation")

        summary = get_assignment_summary(code_key, level)
        skipped_assignments = summary.get("missed", [])
        next_assignment = summary.get("next")

        if skipped_assignments:
            st.markdown(
                f"""
                <div style="
                    background-color: #fff3cd;
                    border-left: 6px solid #ffecb5;
                    color: #7a6001;
                    padding: 16px 18px;
                    border-radius: 8px;
                    margin: 12px 0;
                    font-size: 1.05em;">
                    <b>⚠️ You have skipped the following assignments.<br>
                    Please complete them for full progress:</b><br>
                    {"<br>".join(skipped_assignments)}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.success("No missed assignments detected. Great job!")

        if next_assignment:
            st.info(
                f"**Your next recommended assignment:**\n\n"
                f"**Day {next_assignment.get('day','?')}: {next_assignment.get('chapter','?')} – {next_assignment.get('topic','')}**\n\n"
                f"**Goal:** {next_assignment.get('goal','')}\n\n"
                f"**Instruction:** {next_assignment.get('instruction','')}"
            )
        else:
            st.success("🎉 You’re up to date!")

    elif rr_page == "Downloads":
        st.subheader("Downloads")
        choice = st.radio(
            "Select a download", ["Results PDF", "Enrollment Letter", "Receipt"]
        )

        if choice == "Results PDF":
            st.markdown("**Results summary PDF**")
            COL_ASSN_W, COL_SCORE_W, COL_DATE_W = 45, 18, 30
            PAGE_WIDTH, MARGIN = 210, 10
            FEEDBACK_W = PAGE_WIDTH - 2 * MARGIN - (
                COL_ASSN_W + COL_SCORE_W + COL_DATE_W
            )
            class PDFReport(FPDF):
                def header(self):
                    logo_path = load_school_logo()
                    if logo_path:
                        try:
                            self.image(logo_path, 10, 8, 30)
                        except Exception:
                            pass
                        self.ln(20)
                    else:
                        self.ln(28)
                    self.set_font("Arial", "B", 16)
                    self.cell(
                        0,
                        12,
                        clean_for_pdf("Learn Language Education Academy"),
                        ln=1,
                        align="C",
                    )
                    self.ln(3)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Arial", "I", 9)
                    self.set_text_color(120, 120, 120)
                    footer_text = clean_for_pdf(
                        "Learn Language Education Academy — Results generated on "
                    ) + pd.Timestamp.now().strftime("%d.%m.%Y")
                    self.cell(0, 8, footer_text, 0, 0, "C")
                    self.set_text_color(0, 0, 0)
                    self.alias_nb_pages()

            if st.button("⬇️ Create & Download Results PDF"):
                pdf = PDFReport()
                pdf.add_page()

                pdf.set_font("Arial", "", 12)
                try:
                    shown_name = df_user.name.iloc[0]
                except Exception:
                    shown_name = student_name or "Student"
                pdf.cell(0, 8, clean_for_pdf(f"Name: {shown_name}"), ln=1)
                pdf.cell(
                    0, 8, clean_for_pdf(f"Code: {code_key}     Level: {level}"), ln=1
                )
                pdf.cell(
                    0,
                    8,
                    clean_for_pdf(f"Date: {pd.Timestamp.now():%Y-%m-%d %H:%M}"),
                    ln=1,
                )
                pdf.ln(5)

                pdf.set_font("Arial", "B", 13)
                pdf.cell(0, 10, clean_for_pdf("Summary Metrics"), ln=1)
                pdf.set_font("Arial", "", 11)
                pdf.cell(
                    0,
                    8,
                    clean_for_pdf(
                        f"Total: {total}   Completed: {completed}   Avg: {avg_score:.1f}   Best: {best_score:.0f}"
                    ),
                    ln=1,
                )
                pdf.ln(6)

                pdf.set_font("Arial", "B", 11)
                pdf.cell(COL_ASSN_W, 8, "Assignment", 1, 0, "C")
                pdf.cell(COL_SCORE_W, 8, "Score", 1, 0, "C")
                pdf.cell(COL_DATE_W, 8, "Date", 1, 0, "C")
                pdf.cell(FEEDBACK_W, 8, "Feedback", 1, 1, "C")

                pdf.set_font("Arial", "", 10)
                pdf.set_fill_color(240, 240, 240)
                row_fill = False
                for _, row in df_display.iterrows():
                    assn = clean_for_pdf(str(row["assignment"]))
                    score_txt = clean_for_pdf(str(row["score"]))
                    date_txt = clean_for_pdf(str(row["date"]))
                    label = clean_for_pdf(score_label_fmt(row["score"], plain=True))
                    pdf.cell(COL_ASSN_W, 8, assn, 1, 0, "L", row_fill)
                    pdf.cell(COL_SCORE_W, 8, score_txt, 1, 0, "C", row_fill)
                    pdf.cell(COL_DATE_W, 8, date_txt, 1, 0, "C", row_fill)
                    pdf.multi_cell(FEEDBACK_W, 8, label, 1, "C", row_fill)
                    row_fill = not row_fill
                pdf.set_fill_color(255, 255, 255)

                pdf_bytes = pdf.output(dest="S").encode("latin1", "replace")
                st.download_button(
                    label="Download Results PDF",
                    data=pdf_bytes,
                    file_name=f"{code_key}_results_{level}.pdf",
                    mime="application/pdf",
                )
                b64 = _b64.b64encode(pdf_bytes).decode()
                st.markdown(
                    f'<a href="data:application/pdf;base64,{b64}" download="{code_key}_results_{level}.pdf" '
                    f'style="font-size:1.1em;font-weight:600;color:#2563eb;">📥 Click here to download results PDF (manual)</a>',
                    unsafe_allow_html=True,
                )
                st.info(
                    "If the button does not work, right-click the blue link above and choose 'Save link as...'"
                )

        elif choice == "Enrollment Letter":
            df_students = load_student_data()
            start_date = end_date = ""
            if df_students is not None and "StudentCode" in df_students.columns:
                try:
                    row_match = df_students[
                        df_students["StudentCode"].astype(str).str.lower().str.strip()
                        == code_key
                    ]
                    if not row_match.empty:
                        row0 = row_match.iloc[0]
                        start_date = str(row0.get("ContractStart", ""))
                        end_date = str(row0.get("ContractEnd", ""))
                except Exception:
                    pass
            if st.button("Generate Enrollment Letter"):
                pdf_bytes = generate_enrollment_letter_pdf(
                    student_name or "Student",
                    level,
                    start_date or "",
                    end_date or "",
                )
                st.download_button(
                    "Download Enrollment Letter PDF",
                    data=pdf_bytes,
                    file_name=f"{code_key}_enrollment_letter.pdf",
                    mime="application/pdf",
                )
        else:
            df_students = load_student_data()
            paid = balance = 0.0
            contract_start = ""
            if df_students is not None and "StudentCode" in df_students.columns:
                try:
                    row_match = df_students[
                        df_students["StudentCode"].astype(str).str.lower().str.strip()
                        == code_key
                    ]
                    if not row_match.empty:
                        def _read_money(x):
                            try:
                                s = (
                                    str(x)
                                    .replace(",", "")
                                    .replace(" ", "")
                                    .strip()
                                )
                                return float(s) if s not in ("", "nan", "None") else 0.0
                            except Exception:
                                return 0.0

                        row0 = row_match.iloc[0]
                        paid = _read_money(row0.get("Paid", 0))
                        balance = _read_money(row0.get("Balance", 0))
                        contract_start = str(row0.get("ContractStart", ""))
                except Exception:
                    pass

            receipt_date = st.text_input(
                "Receipt date", value=date.today().isoformat()
            )
            if st.button("Generate Receipt"):
                pdf_bytes = generate_receipt_pdf(
                    student_name or "Student",
                    level,
                    student_code or "",
                    contract_start or "",
                    paid,
                    balance,
                    receipt_date or "",
                )
                st.download_button(
                    "Download Receipt PDF",
                    data=pdf_bytes,
                    file_name=f"{code_key}_receipt.pdf",
                    mime="application/pdf",
                )


    elif rr_page == "Resources":
        st.subheader("Useful Resources")
        st.markdown(
            """
**1. [A1 Schreiben Practice Questions](https://drive.google.com/file/d/1X_PFF2AnBXSrGkqpfrArvAnEIhqdF6fv/view?usp=sharing)**
Practice writing tasks and sample questions for A1.

**2. [A1 Exams Sprechen Guide](https://drive.google.com/file/d/1UWvbCCCcrW3_j9x7pOuWug6_Odvzcvaa/view?usp=sharing)**
Step-by-step guide to the A1 speaking exam.

**3. [German Writing Rules](https://drive.google.com/file/d/1o7_ez3WSNgpgxU_nEtp6EO1PXDyi3K3b/view?usp=sharing)**
Tips and grammar rules for better writing.

**4. [A2 Sprechen Guide](https://drive.google.com/file/d/1TZecDTjNwRYtZXpEeshbWnN8gCftryhI/view?usp=sharing)**
A2-level speaking exam guide.

**5. [B1 Sprechen Guide](https://drive.google.com/file/d/1snk4mL_Q9-xTBXSRfgiZL_gYRI9tya8F/view?usp=sharing)**
How to prepare for your B1 oral exam.
            """
        )


__all__ = [
    "load_assignment_scores",
    "render_results_and_resources_tab",
    "get_assignment_summary",
    "generate_enrollment_letter_pdf",
    "generate_receipt_pdf",
]
