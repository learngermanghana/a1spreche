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
    df = pd.read_csv(url)

    # Normalize column headers immediately for downstream lookups.
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Consolidate common student-code aliases.
    alias_map = {
        "student_code": "studentcode",
        "student code": "studentcode",
    }
    df = df.rename(columns={k: v for k, v in alias_map.items() if k in df.columns})

    required_columns = {"assignment", "level", "score"}
    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        missing_str = ", ".join(missing_columns)
        raise ValueError(
            "Assignment scores data is missing the required column(s): "
            f"{missing_str}. Please update the sheet to include them."
        )

    return df


def load_assignment_scores(force_refresh: bool = False) -> pd.DataFrame:
    """Public wrapper around :func:`_load_assignment_scores_cached`."""

    return _load_assignment_scores_cached(force_refresh=force_refresh)


def fetch_scores(*_args, **_kwargs) -> pd.DataFrame:
    """Compatibility shim so tests can monkeypatch score fetching."""

    return load_assignment_scores()


def get_assignment_summary(student_code: str, level: str, df: pd.DataFrame) -> dict:
    """Summarize assignment progress for a student at a given level."""

    schedules = _get_level_schedules() or {}
    schedule = (
        schedules.get(level)
        or schedules.get((level or "").upper())
        or schedules.get((level or "").title())
        or []
    )

    def _extract_all_nums(chapter_str: str) -> list[float]:
        text = "" if chapter_str is None else str(chapter_str)
        if not text:
            return []
        numbers: list[float] = []
        base_prefix: str | None = None
        decimal_len = 0
        for match in re.finditer(r"\d+(?:\.\d+)?", text):
            token = match.group()
            if "." in token:
                integer_part, decimal_part = token.split(".", 1)
                base_prefix = integer_part
                decimal_len = len(decimal_part)
                numbers.append(float(f"{integer_part}.{decimal_part}"))
            else:
                plain = token.lstrip("0") or "0"
                if (
                    base_prefix is not None
                    and decimal_len
                    and plain.isdigit()
                    and len(plain) <= decimal_len
                ):
                    combined = f"{base_prefix}.{plain.zfill(decimal_len)}"
                    numbers.append(float(combined))
                else:
                    numbers.append(float(token))
                    base_prefix = None
                    decimal_len = 0
        return numbers

    def _numbers_from_source(value: object) -> list[float]:
        if value is None:
            return []
        text = str(value).strip()
        if not text:
            return []
        return _extract_all_nums(text)

    def _collect_section_numbers(section: object, fallback: object) -> list[float]:
        numbers: list[float] = []
        if isinstance(section, dict):
            if section.get("assignment"):
                numbers.extend(_numbers_from_source(section.get("chapter", fallback)))
        elif isinstance(section, list):
            for item in section:
                if isinstance(item, dict) and item.get("assignment"):
                    numbers.extend(_numbers_from_source(item.get("chapter", fallback)))
        return numbers

    def _chapter_strings(lesson: dict) -> list[str]:
        chapters: list[str] = []

        def _maybe_add(value: object) -> None:
            if value is None:
                return
            text = str(value).strip()
            if text:
                chapters.append(text)

        _maybe_add(lesson.get("chapter"))
        for section_name in ("lesen_hören", "schreiben_sprechen"):
            section = lesson.get(section_name)
            if isinstance(section, dict):
                _maybe_add(section.get("chapter"))
            elif isinstance(section, list):
                for item in section:
                    if isinstance(item, dict):
                        _maybe_add(item.get("chapter"))
        return chapters

    student_norm = (student_code or "").strip().casefold()
    level_norm = (level or "").strip().casefold()

    completed_nums: set[float] = set()
    if isinstance(df, pd.DataFrame) and not df.empty:
        required_columns = {"studentcode", "assignment", "level"}
        if required_columns.issubset(df.columns):
            student_series = (
                df["studentcode"].astype(str).str.strip().str.casefold()
            )
            level_series = df["level"].astype(str).str.strip().str.casefold()
            mask = (student_series == student_norm) & (level_series == level_norm)
            if mask.any():
                for value in df.loc[mask, "assignment"]:
                    if pd.isna(value):
                        continue
                    text = str(value).strip()
                    if not text:
                        continue
                    for num in _extract_all_nums(text):
                        completed_nums.add(num)

    def _to_int(value: object) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    lessons_info: list[dict[str, object]] = []

    for lesson in schedule:
        if not isinstance(lesson, dict):
            continue

        topic_value = lesson.get("topic")
        topic = str(topic_value) if topic_value is not None else ""
        if topic and "goethe" in topic.casefold():
            continue

        chapter_candidates = _chapter_strings(lesson)
        chapter_display = chapter_candidates[0] if chapter_candidates else ""
        if any(
            cand.strip().startswith("14.") or cand.strip() == "14"
            for cand in chapter_candidates
        ):
            continue

        general_nums = (
            _numbers_from_source(lesson.get("chapter")) if lesson.get("assignment") else []
        )
        reading_nums = _collect_section_numbers(lesson.get("lesen_hören"), lesson.get("chapter"))
        writing_nums = _collect_section_numbers(
            lesson.get("schreiben_sprechen"), lesson.get("chapter")
        )

        has_reading = bool(general_nums or reading_nums)
        has_writing = bool(writing_nums)
        if not has_reading and has_writing:
            continue

        seen: set[float] = set()
        relevant_nums: list[float] = []
        for num in general_nums + reading_nums + writing_nums:
            if num not in seen:
                seen.add(num)
                relevant_nums.append(num)

        if not relevant_nums:
            continue

        lessons_info.append(
            {
                "day": lesson.get("day"),
                "day_int": _to_int(lesson.get("day")),
                "chapter": chapter_display,
                "topic": topic,
                "goal": lesson.get("goal"),
                "relevant_nums": relevant_nums,
            }
        )

    for info in lessons_info:
        info["completed"] = all(num in completed_nums for num in info["relevant_nums"])

    completed_day_ints = [
        info["day_int"]
        for info in lessons_info
        if info["day_int"] is not None and info.get("completed")
    ]
    max_completed_day = max(completed_day_ints) if completed_day_ints else None

    def _format_line(info: dict[str, object]) -> str:
        day_value = info.get("day")
        day_display = day_value if day_value is not None else "?"
        line = f"Day {day_display}:"
        chapter_text = info.get("chapter") or ""
        topic_text = info.get("topic") or ""
        if chapter_text:
            line += f" Chapter {chapter_text}"
        if topic_text:
            line += f" – {topic_text}"
        return line

    missed: list[str] = []
    next_assignment: dict | None = None

    for info in lessons_info:
        if info.get("completed"):
            continue

        if next_assignment is None:
            day_int = info.get("day_int")
            day_value = info.get("day")
            next_assignment = {
                "day": day_int if day_int is not None else (day_value if day_value is not None else "?"),
                "chapter": info.get("chapter"),
                "topic": info.get("topic"),
                "goal": info.get("goal"),
            }

        day_int = info.get("day_int")
        if (
            max_completed_day is not None
            and day_int is not None
            and day_int <= max_completed_day
        ):
            missed.append(_format_line(info))

    return {"missed": missed, "next": next_assignment}

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

    student_row_state = st.session_state.get("student_row")
    if not isinstance(student_row_state, dict) or not student_row_state:
        student_code_raw = st.session_state.get("student_code", "")
        student_code = str(student_code_raw or "").strip()
        if not student_code and "code_key" in globals():
            try:
                student_code = str(globals().get("code_key", "") or "").strip()
            except Exception:
                student_code = ""
        if student_code:
            try:
                roster_df = load_student_data()
            except Exception:
                roster_df = None
            else:
                if (
                    isinstance(roster_df, pd.DataFrame)
                    and not roster_df.empty
                    and "StudentCode" in roster_df.columns
                ):
                    norm_codes = (
                        roster_df["StudentCode"].astype(str).str.strip().str.lower()
                    )
                    sc_norm = student_code.lower()
                    matches = roster_df[norm_codes == sc_norm]
                    if not matches.empty:
                        row_series = matches.iloc[0]
                        try:
                            row_series = row_series.where(pd.notna(row_series), None)
                        except Exception:
                            pass
                        student_row_state = row_series.to_dict()
                        st.session_state["student_row"] = student_row_state
    student_row = st.session_state.get("student_row")
    if not isinstance(student_row, dict):
        student_row = {}

    def _read_money(x):
        try:
            s = str(x).replace(",", "").replace(" ", "").strip()
            return float(s) if s not in ("", "nan", "None") else 0.0
        except Exception:
            return 0.0

    def _session_str(key: str, default: str = "") -> str:
        value = st.session_state.get(key)
        if value is None:
            return default
        text = str(value).strip()
        return text if text else default

    def _row_str(*keys: str, default: str = "") -> str:
        for key in keys:
            if not key or not isinstance(student_row, dict):
                continue
            value = student_row.get(key)
            if value is None:
                continue
            try:
                if pd.isna(value):
                    continue
            except Exception:
                pass
            text = str(value).strip()
            if text and text.lower() != "nan":
                return text
        return default

    def _normalize_date_str(value: object, default: str = "") -> str:
        if value is None:
            return default
        try:
            if pd.isna(value):
                return default
        except Exception:
            pass
        text = str(value).strip()
        if not text:
            return default
        try:
            dt = pd.to_datetime(text, errors="coerce")
        except Exception:
            dt = pd.NaT
        if pd.isna(dt):
            return text
        return dt.strftime("%Y-%m-%d")

    def _row_money(*keys: str, default: float = 0.0) -> float:
        for key in keys:
            if not key or not isinstance(student_row, dict):
                continue
            if key not in student_row:
                continue
            raw = student_row.get(key)
            if raw is None:
                continue
            try:
                if pd.isna(raw):
                    continue
            except Exception:
                pass
            if isinstance(raw, str) and not raw.strip():
                continue
            try:
                return _read_money(raw)
            except Exception:
                continue
        return default

    # ------- Assignment score data prep -------
    selected_code = _row_str("StudentCode", default=_session_str("student_code", "")).strip()
    selected_level = _row_str("Level", default=_session_str("student_level", "")).strip()

    fetch_payload = {"student_code": selected_code, "level": selected_level}
    try:
        df_scores_raw = fetch_scores(student_code=selected_code, level=selected_level)
    except TypeError as exc:  # compat with simple lambda replacements in tests
        if "student_code" in str(exc) or "level" in str(exc):
            df_scores_raw = fetch_scores(fetch_payload)
        else:  # pragma: no cover - propagate unexpected type errors
            raise
    except Exception:
        df_scores_raw = pd.DataFrame()
    if not isinstance(df_scores_raw, pd.DataFrame):
        df_scores_raw = pd.DataFrame()

    df_scores = df_scores_raw.copy()
    if not df_scores.empty:
        normalized_cols = {}
        for col in df_scores.columns:
            col_key = re.sub(r"[^0-9a-z]+", "_", str(col).strip().lower())
            col_key = re.sub(r"_+", "_", col_key).strip("_")
            normalized_cols[col] = col_key
        df_scores.rename(columns=normalized_cols, inplace=True)
    else:
        df_scores = pd.DataFrame()

    def _first_series(df: pd.DataFrame, candidates: list[str]) -> pd.Series | None:
        for candidate in candidates:
            if candidate in df.columns:
                return df[candidate]
        return None

    def _clean_text(value: object) -> str:
        if value is None:
            return ""
        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass
        text = str(value).strip()
        return "" if not text or text.lower() == "nan" else text

    def _coerce_score_value(value: object) -> float | None:
        text = _clean_text(value)
        if not text:
            return None
        normalized = text.replace(",", "")
        frac_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)\s*$", normalized)
        if frac_match:
            try:
                numerator = float(frac_match.group(1))
                denominator = float(frac_match.group(2))
            except ValueError:
                return None
            if denominator == 0:
                return None
            ratio = numerator / denominator
            return ratio * 100.0 if 0 <= ratio <= 1 else numerator
        percent_match = re.search(r"-?\d+(?:\.\d+)?(?=%)", normalized)
        if percent_match:
            try:
                return float(percent_match.group())
            except ValueError:
                return None
        number_match = re.search(r"-?\d+(?:\.\d+)?", normalized)
        if number_match:
            try:
                value_num = float(number_match.group())
            except ValueError:
                return None
            if 0 <= value_num <= 1 and "%" not in normalized:
                return value_num * 100.0
            return value_num
        return None

    def _display_from_numeric(val: float) -> str:
        if pd.isna(val):
            return ""
        if 0 <= val <= 1:
            return f"{val:.0%}"
        if 0 <= val <= 100:
            return f"{val:.0f}%"
        return f"{val:.0f}"

    def _format_date_value(value: object) -> str:
        text = _clean_text(value)
        if not text:
            return ""
        try:
            parsed = pd.to_datetime(text, errors="coerce")
        except Exception:
            parsed = pd.NaT
        if pd.isna(parsed):
            return text
        return parsed.strftime("%Y-%m-%d")

    student_code_norm = selected_code.casefold() if selected_code else ""
    student_level_norm = selected_level.casefold() if selected_level else ""

    df_user = df_scores.iloc[0:0].copy() if isinstance(df_scores, pd.DataFrame) else pd.DataFrame()
    if isinstance(df_scores, pd.DataFrame) and not df_scores.empty and student_code_norm:
        mask = pd.Series(True, index=df_scores.index, dtype=bool)
        code_series = _first_series(df_scores, ["student_code", "studentcode", "code"])
        if code_series is not None:
            code_norm = code_series.astype(str).str.strip().str.casefold()
            mask &= code_norm == student_code_norm
        else:
            mask &= False
        if student_level_norm:
            level_series = _first_series(
                df_scores,
                ["level", "student_level", "class_level", "lvl"],
            )
            if level_series is not None:
                level_norm = level_series.astype(str).str.strip().str.casefold()
                mask &= level_norm == student_level_norm
        if mask.any():
            df_user = df_scores.loc[mask].copy()
        else:
            df_user = df_scores.iloc[0:0].copy()

    total = int(df_user.shape[0]) if isinstance(df_user, pd.DataFrame) else 0
    completed = 0
    avg_score = 0.0
    best_score = 0.0
    df_display = pd.DataFrame(columns=["assignment", "score", "date"])

    if isinstance(df_user, pd.DataFrame) and not df_user.empty:
        assignment_series = _first_series(
            df_user,
            [
                "assignment",
                "assignment_name",
                "assignmenttitle",
                "task",
                "chapter",
                "lesson",
            ],
        )
        score_series = _first_series(
            df_user,
            ["score", "grade", "points", "result", "marks", "percentage"],
        )
        date_series = _first_series(
            df_user,
            [
                "date",
                "submission_date",
                "submitted",
                "submitted_on",
                "completed_on",
                "timestamp",
            ],
        )

        if assignment_series is not None:
            assignment_display = assignment_series.map(_clean_text)
        else:
            assignment_display = pd.Series(
                [""] * len(df_user), index=df_user.index, dtype=object
            )

        if score_series is not None:
            score_display = score_series.map(_clean_text)
            numeric_series = pd.to_numeric(
                score_series.map(_coerce_score_value), errors="coerce"
            )
            score_display = score_display.where(
                score_display.astype(bool),
                numeric_series.map(_display_from_numeric),
            )
        else:
            score_display = pd.Series(
                [""] * len(df_user), index=df_user.index, dtype=object
            )
            numeric_series = pd.Series(
                [float("nan")] * len(df_user), index=df_user.index
            )

        if date_series is not None:
            date_display = date_series.map(_format_date_value)
        else:
            date_display = pd.Series(
                [""] * len(df_user), index=df_user.index, dtype=object
            )

        df_display = pd.DataFrame(
            {
                "assignment": assignment_display.astype(str),
                "score": score_display.astype(str),
                "date": date_display.astype(str),
            }
        ).reset_index(drop=True)

        numeric_nonnull = numeric_series.dropna()
        completed = int(numeric_nonnull.count())
        if completed:
            avg_score = float(numeric_nonnull.mean())
            best_score = float(numeric_nonnull.max())
            if pd.isna(avg_score):
                avg_score = 0.0
            if pd.isna(best_score):
                best_score = 0.0

    def score_label_fmt(score_value: object, plain: bool = False) -> str:
        cleaned_text = _clean_text(score_value)
        numeric_value = _coerce_score_value(score_value)
        if numeric_value is None:
            return "Not completed yet" if plain else "⏳ Not completed yet"
        if plain:
            return cleaned_text or _display_from_numeric(numeric_value)
        if numeric_value >= 90:
            prefix = "🌟 Excellent work"
        elif numeric_value >= 75:
            prefix = "✅ Great job"
        elif numeric_value >= 60:
            prefix = "👍 Keep going"
        else:
            prefix = "⚠️ Needs improvement"
        display_value = cleaned_text or _display_from_numeric(numeric_value)
        return f"{prefix} ({display_value})"

    avg_display_fmt = f"{avg_score:.1f}%" if completed else "N/A"
    best_display_fmt = f"{best_score:.0f}%" if completed else "N/A"

    display_records: list[dict[str, object]]
    if isinstance(df_display, pd.DataFrame) and not df_display.empty:
        display_records = df_display.to_dict(orient="records")
    else:
        display_records = []

    overview_tab, feedback_tab, achievements_tab, downloads_tab = st.tabs(
        ["Overview", "Feedback", "Achievements", "Downloads"]
    )

    with overview_tab:
        st.subheader("Progress overview")
        st.write(f"Total assignments: {total}")
        st.write(f"Completed assignments: {completed}")
        st.write(f"Average score: {avg_display_fmt}")
        st.write(f"Best score: {best_display_fmt}")
        if display_records:
            st.write("Assignment summary:")
            st.write(df_display)
        else:
            st.info("No assignment data available yet.")

    with feedback_tab:
        st.subheader("Personalized feedback")
        if not display_records:
            st.info("No feedback available yet.")
        else:
            for idx, record in enumerate(display_records):
                assignment_name = str(record.get("assignment") or "Assignment")
                st.markdown(f"**{assignment_name}**")
                st.write(score_label_fmt(record.get("score")))
                date_value = record.get("date")
                if date_value:
                    st.write(f"Date: {date_value}")
                if idx < len(display_records) - 1:
                    st.markdown("---")

    with achievements_tab:
        st.subheader("Achievements")
        if not completed:
            st.info("Complete your first assignment to unlock achievements.")
        else:
            st.write(f"Completed assignments: {completed} / {total}")
            st.write(f"Average score: {avg_display_fmt}")
            st.write(f"Best score: {best_display_fmt}")

            top_result: dict[str, object] | None = None
            for record in display_records:
                numeric_value = _coerce_score_value(record.get("score"))
                if numeric_value is None:
                    continue
                if (
                    top_result is None
                    or numeric_value > float(top_result.get("score", float("-inf")))
                ):
                    top_result = {
                        "assignment": record.get("assignment"),
                        "score": float(numeric_value),
                        "raw": record.get("score"),
                    }

            if top_result is not None:
                assignment_display = str(top_result.get("assignment") or "Assignment")
                st.write(
                    f"Top performance: **{assignment_display}** — "
                    f"{score_label_fmt(top_result.get('raw'))}"
                )
            else:
                st.info("Scores will appear once assignments have been graded.")

    with downloads_tab:
        choice = st.radio(
            "Select a download",
            ["Results PDF", "Enrollment Letter", "Receipt", "Attendance PDF"],
            horizontal=True,
        )

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
                shown_name = _row_str("Name", "StudentName")
                if not shown_name:
                    try:
                        shown_name = df_user.name.iloc[0]  # type: ignore[name-defined]
                    except Exception:
                        shown_name = _session_str("student_name", "Student")

                raw_code = _row_str("StudentCode")
                if raw_code:
                    code_val = raw_code.upper()
                else:
                    fallback_code = _session_str("student_code", "-")
                    code_val = fallback_code.upper() if fallback_code else "-"

                raw_level = _row_str("Level")
                if raw_level:
                    level_val = raw_level.upper()
                else:
                    fallback_level = _session_str("student_level", "-")
                    level_val = fallback_level.upper() if fallback_level else "-"

                pdf.cell(0, 8, t(f"Name: {shown_name}"), ln=1)
                pdf.cell(0, 8, t(f"Code: {code_val}     Level: {level_val}"), ln=1)
                pdf.cell(0, 8, t(f"Date: {pd.Timestamp.now():%Y-%m-%d %H:%M}"), ln=1)
                pdf.ln(5)

                # Summary
                pdf.set_font("DejaVu", "B", 13)
                pdf.cell(0, 10, t("Summary Metrics"), ln=1)
                pdf.set_font("DejaVu", "", 11)
                avg_display = f"{avg_score:.1f}" if completed else "N/A"
                best_display = f"{best_score:.0f}" if completed else "N/A"
                summary_line = (
                    f"Total: {total}   Completed: {completed}   Avg: {avg_display}   Best: {best_display}"
                )
                pdf.cell(0, 8, t(summary_line), ln=1)
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
                rows_iter = df_display.iterrows() if isinstance(df_display, pd.DataFrame) else []
                for _, row in rows_iter:  # type: ignore[misc]
                    assn = t(str(row.get("assignment", "")))
                    score_txt = t(str(row.get("score", "")))
                    date_txt = t(str(row.get("date", "")))
                    label = t(score_label_fmt(row.get("score", None), plain=True))
                    pdf.cell(COL_ASSN_W, 8, assn, 1, 0, "L", row_fill)
                    pdf.cell(COL_SCORE_W, 8, score_txt, 1, 0, "C", row_fill)
                    pdf.cell(COL_DATE_W, 8, date_txt, 1, 0, "C", row_fill)
                    pdf.multi_cell(FEEDBACK_W, 8, label, 1, "C", row_fill)
                    row_fill = not row_fill
                pdf.set_fill_color(255, 255, 255)

                pdf_bytes = pdf.output(dest="S").encode("latin1", "replace")
                file_code = code_val if code_val and code_val != "-" else "student"
                file_level = level_val if level_val and level_val != "-" else "level"
                file_stem = f"{file_code}_results_{file_level}".replace(" ", "_")
                file_name = f"{file_stem}.pdf"
                st.download_button(
                    label="Download Results PDF",
                    data=pdf_bytes,
                    file_name=file_name,
                    mime="application/pdf",
                )
                b64 = _b64.b64encode(pdf_bytes).decode()
                st.markdown(
                    f'<a href="data:application/pdf;base64,{b64}" download="{file_name}" '
                    f'style="font-size:1.1em;font-weight:600;color:#2563eb;">📥 Click here to download results PDF (manual)</a>',
                    unsafe_allow_html=True,
                )
                st.info("If the button does not work, right-click the blue link above and choose 'Save link as...'")

        # ------- Enrollment Letter -------
        elif choice == "Enrollment Letter":
            st.markdown("**Enrollment letter**")

            outstanding_balance = _row_money(
                "Balance", "OutstandingBalance", "BalanceDue", default=0.0
            )
            if outstanding_balance <= 0:
                lookup_code = selected_code or _row_str(
                    "StudentCode", default=_session_str("student_code", "")
                )
                lookup_code_norm = lookup_code.strip().casefold() if lookup_code else ""
                if lookup_code_norm:

                    try:
                        roster_df = load_student_data()
                    except Exception:
                        roster_df = None

                    if (
                        isinstance(roster_df, pd.DataFrame)
                        and not roster_df.empty
                        and "StudentCode" in roster_df.columns
                    ):
                        roster_norm = (
                            roster_df["StudentCode"].astype(str).str.strip().str.casefold()
                        )
                        matches = roster_df[roster_norm == lookup_code_norm]
                        if not matches.empty:
                            roster_row = matches.iloc[0]
                            for key in ["Balance", "OutstandingBalance", "BalanceDue"]:
                                if key not in roster_row:
                                    continue
                                candidate = roster_row.get(key)
                                if candidate in (None, ""):
                                    continue
                                try:
                                    if pd.isna(candidate):
                                        continue
                                except Exception:
                                    pass
                                candidate_val = _read_money(candidate)
                                if candidate_val > outstanding_balance:
                                    outstanding_balance = candidate_val
                                    try:
                                        if isinstance(student_row, dict):
                                            student_row[key] = candidate
                                            st.session_state.setdefault("student_row", {})[key] = candidate
                                    except Exception:
                                        pass
                                    break
            if outstanding_balance > 0:
                st.error("Outstanding balance…")
                st.info(
                    "Please settle the outstanding balance before requesting an enrollment letter."
                )

                return
            name_val = _row_str("Name", "StudentName", default=_session_str("student_name", "Student"))
            level_raw = _row_str("Level", default=_session_str("student_level", ""))
            level_display = level_raw.upper() if level_raw else "-"

            start_candidate = None
            for key in ["ContractStart", "StartDate", "ContractBegin", "Start", "Begin", "EnrollDate"]:
                candidate = student_row.get(key) if isinstance(student_row, dict) else None
                if candidate in (None, ""):
                    continue
                try:
                    if pd.isna(candidate):
                        continue
                except Exception:
                    pass
                start_candidate = candidate
                break
            start_val = _normalize_date_str(start_candidate, default="")
            if not start_val:
                start_val = pd.Timestamp.today().strftime("%Y-%m-%d")

            end_candidate = None
            for key in ["ContractEnd", "EndDate", "ContractFinish", "End"]:
                candidate = student_row.get(key) if isinstance(student_row, dict) else None
                if candidate in (None, ""):
                    continue
                try:
                    if pd.isna(candidate):
                        continue
                except Exception:
                    pass
                end_candidate = candidate
                break
            end_val = _normalize_date_str(end_candidate, default="")
            if not end_val:
                try:
                    start_dt = pd.to_datetime(start_val, errors="coerce")
                except Exception:
                    start_dt = pd.NaT
                if not pd.isna(start_dt):
                    end_val = (start_dt + pd.Timedelta(days=90)).strftime("%Y-%m-%d")
                else:
                    end_val = (pd.Timestamp.today() + pd.Timedelta(days=90)).strftime("%Y-%m-%d")

            st.text_input("Student name", value=name_val, disabled=True)
            st.text_input("Level", value=level_display, disabled=True)
            st.text_input("Enrollment start", value=start_val, disabled=True)
            st.text_input("Enrollment end", value=end_val, disabled=True)

            if st.button("Generate Enrollment Letter"):
                pdf_bytes = generate_enrollment_letter_pdf(name_val, level_display, start_val, end_val)
                file_stub = (name_val or "student").strip().replace(" ", "_") or "student"
                st.download_button(
                    "Download Enrollment Letter PDF",
                    data=pdf_bytes,
                    file_name=f"{file_stub}_enrollment_letter.pdf",
                    mime="application/pdf",
                )

        # ------- Receipt -------
        elif choice == "Receipt":
            st.markdown("**Payment receipt**")
            name_val = _row_str("Name", "StudentName", default=_session_str("student_name", "Student"))
            level_raw = _row_str("Level", default=_session_str("student_level", ""))
            level_display = level_raw.upper() if level_raw else "-"
            code_raw = _row_str("StudentCode", default=_session_str("student_code", ""))
            code_display = code_raw.upper() if code_raw else "-"

            start_candidate = None
            for key in ["ContractStart", "StartDate", "ContractBegin", "Start", "Begin"]:
                candidate = student_row.get(key) if isinstance(student_row, dict) else None
                if candidate in (None, ""):
                    continue
                try:
                    if pd.isna(candidate):
                        continue
                except Exception:
                    pass
                start_candidate = candidate
                break
            contract_start = _normalize_date_str(start_candidate, default="")
            if not contract_start:
                contract_start = pd.Timestamp.today().strftime("%Y-%m-%d")

            paid_amt = _row_money(
                "LastPaymentAmount",
                "AmountPaid",
                "AmountPaidGHS",
                "AmountPaidToDate",
                "PaidAmount",
                "Paid",
                default=0.0,
            )
            balance_amt = _row_money("Balance", "OutstandingBalance", "BalanceDue", default=0.0)

            receipt_candidate = None
            for key in ["LastPaymentDate", "PaymentDate", "ReceiptDate", "LastPayment", "Date"]:
                candidate = student_row.get(key) if isinstance(student_row, dict) else None
                if candidate in (None, ""):
                    continue
                try:
                    if pd.isna(candidate):
                        continue
                except Exception:
                    pass
                receipt_candidate = candidate
                break
            receipt_date = _normalize_date_str(receipt_candidate, default="")
            if not receipt_date:
                receipt_date = pd.Timestamp.now().strftime("%Y-%m-%d")

            st.text_input("Student name", value=name_val, disabled=True)
            st.text_input("Level", value=level_display, disabled=True)
            st.text_input("Student Code", value=code_display, disabled=True)
            st.text_input("Contract start", value=contract_start, disabled=True)
            st.text_input("Amount Paid", value=format_cedis(paid_amt), disabled=True)
            st.text_input("Balance", value=format_cedis(balance_amt), disabled=True)
            st.text_input("Date", value=receipt_date, disabled=True)

            if st.button("Generate Receipt"):
                pdf_bytes = generate_receipt_pdf(
                    name_val,
                    level_display,
                    code_display,
                    contract_start,
                    paid_amt,
                    balance_amt,
                    receipt_date,
                )
                receipt_stub = code_display if code_display and code_display != "-" else "student"
                receipt_stub = receipt_stub.replace(" ", "_") or "student"
                st.download_button(
                    "Download Receipt PDF",
                    data=pdf_bytes,
                    file_name=f"{receipt_stub}_receipt.pdf",
                    mime="application/pdf",
                )

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

                    max_session_width = 120
                    ellipsis = "..."

                    def _shorten_session_text(raw: object) -> str:
                        base_text = t(str(raw or ""))
                        if pdf.get_string_width(base_text) <= max_session_width:
                            return base_text

                        ellipsis_width = pdf.get_string_width(ellipsis)
                        available_width = max_session_width - ellipsis_width
                        if available_width <= 0:
                            return ellipsis if ellipsis_width <= max_session_width else ""

                        shortened = base_text
                        while shortened and pdf.get_string_width(shortened) > available_width:
                            shortened = shortened[:-1]
                        shortened = shortened.rstrip()
                        if not shortened:
                            return ellipsis

                        candidate = f"{shortened}{ellipsis}"
                        while shortened and pdf.get_string_width(candidate) > max_session_width:
                            shortened = shortened[:-1].rstrip()
                            candidate = f"{shortened}{ellipsis}" if shortened else ellipsis
                        return candidate

                    for _, row in df_att.iterrows():
                        session_text = _shorten_session_text(row.get("session", ""))
                        pdf.cell(120, 8, session_text, 1, 0, "L")
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
