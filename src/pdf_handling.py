"""Utilities for PDF extraction and generation used by the Falowen app."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List

from .pdf_utils import clean_for_pdf

try:  # pragma: no cover - optional dependency
    from fpdf import FPDF
except Exception:  # pragma: no cover
    FPDF = None  # type: ignore


FONT_PATH = Path(__file__).resolve().parent.parent / "font/DejaVuSans.ttf"


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Return text extracted from PDF bytes using best-effort parsers."""
    try:  # pragma: no cover - optional dependency
        from pypdf import PdfReader

        t: List[str] = []
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for p in reader.pages:
            try:
                t.append(p.extract_text() or "")
            except Exception:
                t.append("")
        return "\n".join(t)
    except Exception:
        pass
    try:  # pragma: no cover - optional dependency
        from pdfminer.high_level import extract_text

        return extract_text(io.BytesIO(pdf_bytes)) or ""
    except Exception:
        return ""


def generate_notes_pdf(
    notes: List[Dict[str, Any]],
    font_path: str = str(FONT_PATH),
) -> bytes:
    """Return a PDF containing the provided notes."""
    if FPDF is None:  # pragma: no cover - dependency missing
        return b""

    class PDF(FPDF):
        def header(self) -> None:  # pragma: no cover - layout only
            self.set_font("DejaVu", "", 16)
            self.cell(0, 12, "My Learning Notes", align="C", ln=1)
            self.ln(5)

    def _build_pdf(ns: List[Dict[str, Any]]) -> "FPDF":
        pdf = PDF()
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("DejaVu", "", 13)
        pdf.cell(0, 10, "Table of Contents", ln=1)
        pdf.set_font("DejaVu", "", 11)
        for idx, note in enumerate(ns):
            toc_line = f"{idx+1}. {note.get('title','')} - {note.get('created', note.get('updated',''))}"
            pdf.cell(0, 8, clean_for_pdf(toc_line), ln=1)
        pdf.ln(5)
        for n in ns:
            pdf.set_font("DejaVu", "", 13)
            pdf.cell(0, 10, clean_for_pdf(f"Title: {n.get('title','')}"), ln=1)
            pdf.set_font("DejaVu", "", 11)
            if n.get("tag"):
                pdf.cell(0, 8, clean_for_pdf(f"Tag: {n['tag']}"), ln=1)
            if n.get("lesson"):
                pdf.cell(0, 8, clean_for_pdf(f"Lesson: {n['lesson']}"), ln=1)
            pdf.set_font("DejaVu", "", 12)
            for line in n.get("text", "").split("\n"):
                pdf.multi_cell(0, 7, clean_for_pdf(line))
            pdf.ln(1)
            pdf.set_font("DejaVu", "", 11)
            pdf.cell(0, 8, clean_for_pdf(f"Date: {n.get('updated', n.get('created',''))}"), ln=1)
            pdf.ln(5)
            pdf.set_font("DejaVu", "", 10)
            pdf.cell(0, 4, "-" * 55, ln=1)
            pdf.ln(8)
        return pdf

    pdf = _build_pdf(notes)
    try:
        return pdf.output(dest="S").encode("latin1", "replace")
    except IndexError:
        cleaned: List[Dict[str, Any]] = []
        for note in notes:
            new_note: Dict[str, Any] = {}
            for k, v in note.items():
                if isinstance(v, str):
                    v = v.encode("utf-8", "ignore").decode("utf-8")
                    v = v.encode("latin1", "ignore").decode("latin1")
                new_note[k] = v
            cleaned.append(new_note)
        pdf = _build_pdf(cleaned)
        return pdf.output(dest="S").encode("latin1", "replace")


def generate_single_note_pdf(
    note: Dict[str, Any],
    font_path: str = str(FONT_PATH),
) -> bytes:
    """Return a PDF for a single note."""
    if FPDF is None:  # pragma: no cover - dependency missing
        return b""

    class SingleNotePDF(FPDF):
        def header(self) -> None:  # pragma: no cover - layout only
            self.set_font("DejaVu", "", 13)
            self.cell(0, 10, clean_for_pdf(note.get("title", "Note")), ln=True, align="C")
            self.ln(2)

    pdf_note = SingleNotePDF()
    pdf_note.add_font("DejaVu", "", font_path, uni=True)
    pdf_note.add_page()
    pdf_note.set_font("DejaVu", "", 12)
    if note.get("tag"):
        pdf_note.cell(0, 8, clean_for_pdf(f"Tag: {note.get('tag','')}"), ln=1)
    if note.get("lesson"):
        pdf_note.cell(0, 8, clean_for_pdf(f"Lesson: {note.get('lesson','')}"), ln=1)
    for line in note.get("text", "").split("\n"):
        pdf_note.multi_cell(0, 7, clean_for_pdf(line))
    pdf_note.ln(1)
    pdf_note.set_font("DejaVu", "", 11)
    pdf_note.cell(0, 8, clean_for_pdf(f"Date: {note.get('updated', note.get('created',''))}"), ln=1)
    return pdf_note.output(dest="S").encode("latin1", "replace")


def generate_chat_pdf(messages: List[Dict[str, Any]]) -> bytes:
    """Return a PDF transcript of chat messages."""
    if FPDF is None:  # pragma: no cover - dependency missing
        return b""

    def _build_pdf(msgs: List[Dict[str, Any]]) -> "FPDF":
        pdf = FPDF()
        pdf.add_font("DejaVu", "", str(FONT_PATH), uni=True)
        pdf.add_page()
        pdf.set_font("DejaVu", size=12)
        for m in msgs:
            who = "Herr Felix" if m.get("role") == "assistant" else "Student"
            who = clean_for_pdf(who)
            content = clean_for_pdf(m.get("content", ""))
            line = f"{who}: {content}"
            pdf.multi_cell(0, 8, line)
            pdf.ln(1)
        return pdf

    pdf = _build_pdf(messages)
    try:
        return pdf.output(dest="S").encode("latin1", "replace")
    except IndexError:
        cleaned: List[Dict[str, Any]] = []
        for m in messages:
            c = m.get("content", "")
            c = c.encode("utf-8", errors="ignore").decode("utf-8")
            c = c.encode("latin1", errors="ignore").decode("latin1")
            cleaned.append({**m, "content": c})
        pdf = _build_pdf(cleaned)
        return pdf.output(dest="S").encode("latin1", "replace")


__all__ = [
    "extract_text_from_pdf",
    "generate_notes_pdf",
    "generate_single_note_pdf",
    "generate_chat_pdf",
]
