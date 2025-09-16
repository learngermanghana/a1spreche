"""Assignment results and resources tab helpers (corrected).

This refactor centralizes PDF font handling via `_load_pdf_fonts`, removes
accidental merge-artifacts/duplications, and ensures graceful fallback when
bundled DejaVu fonts are unavailable.
"""
from __future__ import annotations

import base64 as _b64
import io
import os
import re
import tempfile
from datetime import date
from typing import Callable, NamedTuple

import pandas as pd
import requests
import streamlit as st
from fpdf import FPDF

from .assignment import linkify_html
from .schedule import get_level_schedules as _get_level_schedules
# ``load_school_logo`` is expected to be defined elsewhere in this package.
from .pdf_utils import make_qr_code, clean_for_pdf
from .data_loading import load_student_data
from .attendance_utils import load_attendance_records
from .utils.currency import format_cedis
from src.utils.toasts import refresh_with_toast

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# URLs for letterhead and watermark images are configurable via environment
# variables so deployments can swap assets without touching the code.
LETTERHEAD_URL = os.getenv(
    "LETTERHEAD_URL",
    "https://via.placeholder.com/600x100.png?text=Letterhead",
)
WATERMARK_URL = os.getenv(
    "WATERMARK_URL",
    "https://drive.google.com/uc?export=download&id=1dEXHtaPBmvnX941GKK-DsTmj3szz2Z5A",
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REGULAR_FONT_PATH = os.path.join(BASE_DIR, "font", "DejaVuSans.ttf")
BOLD_FONT_PATH = os.path.join(BASE_DIR, "font", "DejaVuSans-Bold.ttf")

# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600)
def _load_assignment_scores_cached(force_refresh: bool = False) -> pd.DataFrame:
    """Fetch assignment scores from the Google Sheet.

    Parameters
    ----------
    force_refresh: bool, optional
        When ``True`` the Streamlit data cache is cleared before fetching the
        scores.
    """

    if force_refresh:
        try:
            st.cache_data.clear()
        except Exception:  # pragma: no cover - best effort
            pass

    SHEET_ID = "1BRb8p3Rq0VpFCLSwL4eS9tSgXBo9hSWzfW_J_7W36NQ"
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
    )
    return pd.read_csv(url)

# ---------------------------------------------------------------------------
# Helpers used elsewhere in the module (stubs shown here for completeness)
# ---------------------------------------------------------------------------

_num_pat = re.compile(r"(\d+(?:[.,]\d+)?)")

def _extract_max_num(text: str | float | int | None) -> float | None:
    if text is None:
        return None
    s = str(text)
    nums = [float(x.replace(",", ".")) for x in _num_pat.findall(s)]
    return max(nums) if nums else None


def _is_recommendable(lesson: dict) -> bool:
    # Placeholder business rule (kept minimal since original logic not included)
    return bool(lesson)

# ---------------------------------------------------------------------------
# Font handling for PDFs
# ---------------------------------------------------------------------------

class PDFFontConfig(NamedTuple):
    """Runtime configuration for PDF font usage."""

    family: str
    transform: Callable[[str], str]
    uses_dejavu: bool
    bold_available: bool


def _load_pdf_fonts(pdf: FPDF) -> PDFFontConfig:
    """Register DejaVu fonts if available and provide fallback helpers.

    Returns a tuple with the chosen family, a text-transform function that
    sanitizes/encodes text appropriately for the active font setup, and flags
    indicating whether DejaVu and its bold face are usable.
    """

    uses_dejavu = True
    bold_available = True
    try:
        pdf.add_font("DejaVu", "", REGULAR_FONT_PATH, uni=True)
    except (RuntimeError, OSError):
        uses_dejavu = False
        bold_available = False
    else:
        try:
            pdf.add_font("DejaVu", "B", BOLD_FONT_PATH, uni=True)
        except (RuntimeError, OSError):
            bold_available = False

    if not uses_dejavu:
        font_family = "Helvetica"  # built-in Latin-1 font
        bold_available = True       # Helvetica has bold style
    else:
        font_family = "DejaVu"

    def _transform(text: str) -> str:
        # Always run shared sanitizer first.
        text = clean_for_pdf(text)
        if uses_dejavu:
            return text
        # When not using a Unicode TTF font, coerce to latin1 with replacement.
        return text.encode("latin1", "replace").decode("latin1")

    return PDFFontConfig(font_family, _transform, uses_dejavu, bold_available)

# ---------------------------------------------------------------------------
# PDF generators
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
    font_config = _load_pdf_fonts(pdf)

    def _set_font(style: str = "", size: int = 12) -> None:
        chosen_style = style
        if font_config.family == "DejaVu" and style == "B" and not font_config.bold_available:
            chosen_style = ""
        pdf.set_font(font_config.family, chosen_style, size)

    t = font_config.transform

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
    _set_font("B", 16)
    pdf.cell(0, 10, t("Learn Language Education Academy"), ln=1, align="C")
    _set_font(size=10)
    pdf.cell(0, 6, t("https://www.learngermanghana.com | 0205706589 | Accra, Ghana"), ln=1, align="C")
    pdf.cell(0, 6, t("Business Reg No: BN173410224"), ln=1, align="C")
    pdf.ln(10)

    _set_font(size=12)
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
        pdf.multi_cell(0, 8, t(line))
        pdf.ln(1)

    # QR code in bottom-right
    try:
        qr_payload = f"{student_name}|{student_level}|{enrollment_start}|{enrollment_end}"
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
    """Generate a simple payment receipt as PDF bytes.

    Includes a status line indicating whether the payment is complete or an
    installment with a remaining balance.
    """

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    font_config = _load_pdf_fonts(pdf)

    def _set_font(style: str = "", size: int = 12) -> None:
        chosen_style = style
        if font_config.family == "DejaVu" and style == "B" and not font_config.bold_available:
            chosen_style = ""
        pdf.set_font(font_config.family, chosen_style, size)

    t = font_config.transform

    # Optional logo
    try:
        logo = load_school_logo()  # type: ignore[name-defined]
    except Exception:
        logo = None
    if logo:
        try:  # pragma: no cover - rendering
            pdf.image(logo, x=10, y=8, w=40)
            pdf.ln(35)
        except Exception:
            pdf.ln(5)
    else:
        pdf.ln(5)

    _set_font("B", 16)
    pdf.cell(0, 10, t("Payment Receipt"), ln=1, align="C")
    _set_font(size=10)
    pdf.cell(0, 6, t("Learn Language Education Academy"), ln=1, align="C")
    pdf.cell(0, 6, t("https://www.learngermanghana.com | 0205706589 | Accra, Ghana"), ln=1, align="C")
    pdf.cell(0, 6, t("Business Reg No: BN173410224"), ln=1, align="C")
    pdf.ln(10)

    _set_font(size=12)
    status_line = "Status: Full payment" if balance == 0 else f"Status: Installment – Balance remaining {format_cedis(balance)}"
    lines = [
        status_line,
        f"Student: {student_name} ({student_level})",
        f"Student Code: {student_code}",
        f"Contract Start: {contract_start}",
        f"Amount Paid: {format_cedis(paid)}",
        f"Balance: {format_cedis(balance)}",
        f"Date: {receipt_date}",
    ]
    for idx, line in enumerate(lines):
        pdf.multi_cell(0, 8, t(line))
        pdf.ln(4 if idx == 0 else 2)

    return pdf.output(dest="S").encode("latin1", "replace")

# ---------------------------------------------------------------------------
# Main renderer (only the affected blocks are shown/cleaned up)
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

    # ... (omitted: upstream UI and data prep code)

    choice = st.selectbox(
        "Select a download", ["Results PDF", "Enrollment Letter", "Receipt", "Attendance PDF"]
    )

    def _read_money(x):
        try:
            s = str(x).replace(",", "").replace(" ", "").strip()
            return float(s) if s not in ("", "nan", "None") else 0.0
        except Exception:
            return 0.0

    # ------- Results PDF -------
    if choice == "Results PDF":
        st.markdown("**Results summary PDF**")
        COL_ASSN_W, COL_SCORE_W, COL_DATE_W = 45, 18, 30
        PAGE_WIDTH, MARGIN = 210, 10
        FEEDBACK_W = PAGE_WIDTH - 2 * MARGIN - (COL_ASSN_W + COL_SCORE_W + COL_DATE_W)

        class PDFReport(FPDF):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                cfg = _load_pdf_fonts(self)
                self._pdf_font_family = cfg.family
                self._text = cfg.transform
                self._dejavu_bold_available = cfg.bold_available

            # Ensure callers can request DejaVu while still honoring fallback logic
            def set_font(self, family, style="", size=0):  # type: ignore[override]
                if family == "DejaVu":
                    family = self._pdf_font_family
                    if self._pdf_font_family == "DejaVu" and style == "B" and not self._dejavu_bold_available:
                        style = ""
                    if style == "I":  # avoid italics with DejaVu in pyfpdf
                        style = ""
                return super().set_font(family, style, size)

            def header(self):
                try:
                    logo_path = load_school_logo()  # type: ignore[name-defined]
                except Exception:
                    logo_path = None
                if logo_path:
                    try:
                        self.image(logo_path, 10, 8, 30)
                    except Exception:
                        pass
                    self.ln(20)
                else:
                    self.ln(28)
                self.set_font("DejaVu", "B", 16)
                self.cell(0, 12, self._text("Learn Language Education Academy"), ln=1, align="C")
                self.ln(3)

            def footer(self):
                self.set_y(-15)
                self.set_font("DejaVu", "", 9)
                self.set_text_color(120, 120, 120)
                footer_text = self._text(
                    f"Learn Language Education Academy — Results generated on {pd.Timestamp.now():%d.%m.%Y}"
                )
                self.cell(0, 8, footer_text, 0, 0, "C")
                self.set_text_color(0, 0, 0)
                self.alias_nb_pages()

        if st.button("⬇️ Create & Download Results PDF"):
            pdf = PDFReport()
            t = pdf._text
            pdf.add_page()

            pdf.set_font("DejaVu", "", 12)
            # `df_user`, `student_name`, `code_key`, `level`, `total`, `completed`, `avg_score`,
            # `best_score`, `df_display`, and `score_label_fmt` are expected from upstream code.
            try:
                shown_name = df_user.name.iloc[0]  # type: ignore[name-defined]
            except Exception:
                shown_name = (student_name if 'student_name' in globals() else "Student")  # type: ignore[name-defined]

            code_val = (code_key if 'code_key' in globals() else "-")  # type: ignore[name-defined]
            level_val = (level if 'level' in globals() else "-")      # type: ignore[name-defined]

            pdf.cell(0, 8, t(f"Name: {shown_name}"), ln=1)
            pdf.cell(0, 8, t(f"Code: {code_val}     Level: {level_val}"), ln=1)
            pdf.cell(0, 8, t(f"Date: {pd.Timestamp.now():%Y-%m-%d %H:%M}"), ln=1)
            pdf.ln(5)

            # Summary
            pdf.set_font("DejaVu", "B", 13)
            pdf.cell(0, 10, t("Summary Metrics"), ln=1)
            pdf.set_font("DejaVu", "", 11)
            total_val = (total if 'total' in globals() else 0)               # type: ignore[name-defined]
            completed_val = (completed if 'completed' in globals() else 0)   # type: ignore[name-defined]
            avg_val = (avg_score if 'avg_score' in globals() else 0.0)       # type: ignore[name-defined]
            best_val = (best_score if 'best_score' in globals() else 0.0)     # type: ignore[name-defined]
            pdf.cell(0, 8, t(f"Total: {total_val}   Completed: {completed_val}   Avg: {avg_val:.1f}   Best: {best_val:.0f}"), ln=1)
            pdf.ln(6)

            # Table header
            pdf.set_font("DejaVu", "B", 11)
            pdf.cell(COL_ASSN_W, 8, t("Assignment"), 1, 0, "C")
            pdf.cell(COL_SCORE_W, 8, t("Score"), 1, 0, "C")
            pdf.cell(COL_DATE_W, 8, t("Date"), 1, 0, "C")
            pdf.cell(FEEDBACK_W, 8, t("Feedback"), 1, 1, "C")

            # Rows
            pdf.set_font("DejaVu", "", 10)
            pdf.set_fill_color(240, 240, 240)
            row_fill = False
            try:
                rows_iter = df_display.iterrows()  # type: ignore[name-defined]
            except Exception:
                rows_iter = []  # type: ignore[assignment]
            for _, row in rows_iter:  # type: ignore[misc]
                assn = t(str(row.get("assignment", "")))
                score_txt = t(str(row.get("score", "")))
                date_txt = t(str(row.get("date", "")))
                try:
                    label = t(score_label_fmt(row.get("score", None), plain=True))  # type: ignore[name-defined]
                except Exception:
                    label = t("")
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
                file_name=f"{code_val}_results_{level_val}.pdf",
                mime="application/pdf",
            )
            b64 = _b64.b64encode(pdf_bytes).decode()
            st.markdown(
                f'<a href="data:application/pdf;base64,{b64}" download="{code_val}_results_{level_val}.pdf" '
                f'style="font-size:1.1em;font-weight:600;color:#2563eb;">📥 Click here to download results PDF (manual)</a>',
                unsafe_allow_html=True,
            )
            st.info("If the button does not work, right-click the blue link above and choose 'Save link as...'")

    # ------- Enrollment Letter -------
    elif choice == "Enrollment Letter":
        st.markdown("**Enrollment letter**")
        with st.form("enroll_form"):
            nm = st.text_input("Student name", (student_name if 'student_name' in globals() else ""))  # type: ignore[name-defined]
            lvl = st.text_input("Level", (level if 'level' in globals() else ""))  # type: ignore[name-defined]
            start = st.date_input("Enrollment start", value=pd.Timestamp.today()).strftime("%Y-%m-%d")
            end = st.date_input("Enrollment end", value=pd.Timestamp.today() + pd.Timedelta(days=90)).strftime("%Y-%m-%d")
            submitted = st.form_submit_button("⬇️ Create & Download Enrollment Letter")
        if submitted:
            pdf_bytes = generate_enrollment_letter_pdf(nm, lvl, start, end)
            st.download_button("Download Enrollment Letter PDF", data=pdf_bytes, file_name=f"{nm}_enrollment_letter.pdf", mime="application/pdf")

    # ------- Receipt -------
    elif choice == "Receipt":
        st.markdown("**Payment receipt**")
        # Upstream code should provide these values; keep form for safety.
        with st.form("receipt_form"):
            nm = st.text_input("Student name", (student_name if 'student_name' in globals() else ""))  # type: ignore[name-defined]
            lvl = st.text_input("Level", (level if 'level' in globals() else ""))  # type: ignore[name-defined]
            code_val = st.text_input("Student Code", (code_key if 'code_key' in globals() else ""))  # type: ignore[name-defined]
            start = st.text_input("Contract start", "YYYY-MM-DD")
            paid_amt = st.number_input("Amount Paid", min_value=0.0, step=1.0)
            bal_amt = st.number_input("Balance", min_value=0.0, step=1.0)
            rdate = st.text_input("Date", pd.Timestamp.now().strftime("%Y-%m-%d"))
            submitted = st.form_submit_button("⬇️ Create & Download Receipt")
        if submitted:
            pdf_bytes = generate_receipt_pdf(nm, lvl, code_val, start, paid_amt, bal_amt, rdate)
            st.download_button("Download Receipt PDF", data=pdf_bytes, file_name=f"{code_val}_receipt.pdf", mime="application/pdf")

    # ------- Attendance PDF -------
    elif choice == "Attendance PDF":
        class_name = st.session_state.get("student_row", {}).get("ClassName")
        student_code = (st.session_state.get("student_row", {}).get("StudentCode")
                        or (code_key if 'code_key' in globals() else None))  # type: ignore[name-defined]
        if not class_name or not student_code:
            st.info("No attendance data available.")
        else:
            records, _sessions, _hours = load_attendance_records(student_code, class_name)
            if records:
                df_att = pd.DataFrame(records)
                df_att["Present"] = df_att["present"].map(lambda x: "Yes" if x else "No")

                pdf = FPDF()
                pdf.add_page()
                font_cfg = _load_pdf_fonts(pdf)

                def _set_font(style: str = "", size: int = 12) -> None:
                    chosen_style = style
                    if font_cfg.family == "DejaVu" and style == "B" and not font_cfg.bold_available:
                        chosen_style = ""
                    pdf.set_font(font_cfg.family, chosen_style, size)

                t = font_cfg.transform

                _set_font("B", 14)
                disp_name = (st.session_state.get("student_row", {}).get("Name")
                             or (student_name if 'student_name' in globals() else 'Student'))  # type: ignore[name-defined]
                pdf.cell(0, 10, t(f"Attendance for {disp_name}"), ln=1, align="C")
                _set_font(size=11)
                pdf.cell(0, 8, t(f"Class: {class_name}"), ln=1)
                pdf.ln(4)

                _set_font("B", 11)
                pdf.cell(120, 8, t("Session"), 1, 0, "C")
                pdf.cell(40, 8, t("Present"), 1, 1, "C")
                _set_font(size=10)
                for _, row in df_att.iterrows():
                    pdf.cell(120, 8, t(str(row.get("session", ""))), 1, 0, "L")
                    pdf.cell(40, 8, t(row.get("Present", "")), 1, 1, "C")

                pdf_bytes = pdf.output(dest="S").encode("latin1", "replace")
                st.download_button(
                    "Download Attendance PDF",
                    data=pdf_bytes,
                    file_name=f"{student_code}_attendance.pdf",
                    mime="application/pdf",
                )
            else:
                st.info("No attendance records found for this student/class.")
