"""Helpers for Falowen's exams practice experience."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import logging
import random

import pandas as pd
import streamlit as st

from src.utils.toasts import rerun_without_toast

try:  # pragma: no cover - fallback for tests
    from falowen.sessions import get_db
except Exception:  # pragma: no cover - graceful fallback when Firestore is stubbed
    def get_db():  # type: ignore
        return None

lesen_links: Dict[str, List[Tuple[str, str]]] = {
    "A1": [("Goethe A1 Lesen (Lesen & Hören page)", "https://www.goethe.de/ins/mm/en/spr/prf/gzsd1/ueb.html")],
    "A2": [("Goethe A2 Lesen (Lesen & Hören page)", "https://www.goethe.de/ins/mm/en/spr/prf/gzsd2/ueb.html")],
    "B1": [("Goethe B1 Lesen (Lesen & Hören page)", "https://www.goethe.de/ins/mm/en/spr/prf/gzb1/ueb.html")],
    "B2": [("Goethe B2 Lesen (Lesen & Hören page)", "https://www.goethe.de/ins/mm/en/spr/prf/gzb2/ue9.html")],
    "C1": [("Goethe C1 Lesen (Lesen & Hören page)", "https://www.goethe.de/ins/be/en/spr/prf/gzc1/u24.html")],
}

hoeren_links: Dict[str, List[Tuple[str, str]]] = {
    "A1": [("Goethe A1 Hören (Lesen & Hören page)", "https://www.goethe.de/ins/mm/en/spr/prf/gzsd1/ueb.html")],
    "A2": [("Goethe A2 Hören (Lesen & Hören page)", "https://www.goethe.de/ins/mm/en/spr/prf/gzsd2/ueb.html")],
    "B1": [("Goethe B1 Hören (Lesen & Hören page)", "https://www.goethe.de/ins/mm/en/spr/prf/gzb1/ueb.html")],
    "B2": [("Goethe B2 Hören (Lesen & Hören page)", "https://www.goethe.de/ins/mm/en/spr/prf/gzb2/ue9.html")],
    "C1": [("Goethe C1 Hören (Lesen & Hören page)", "https://www.goethe.de/ins/be/en/spr/prf/gzc1/u24.html")],
}

exam_sheet_id = "1zaAT5NjRGKiITV7EpuSHvYMBHHENMs9Piw3pNcyQtho"
exam_sheet_name = "exam_topics"
exam_csv_url = (
    f"https://docs.google.com/spreadsheets/d/{exam_sheet_id}/gviz/tq?tqx=out:csv&sheet={exam_sheet_name}"
)


@st.cache_data(ttl=3600)
def _load_exam_topics_cached() -> pd.DataFrame:
    expected_cols = ["Level", "Teil", "Topic/Prompt", "Keyword/Subtopic"]
    try:
        df = pd.read_csv(exam_csv_url)
    except Exception:  # pragma: no cover - network errors are surfaced in Streamlit UI
        logging.exception("Failed to load exam topics")
        st.error("Unable to load exam topics. Please try again later.")
        return pd.DataFrame(columns=expected_cols)

    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""
    for column in df.columns:
        if df[column].dtype == "O":
            df[column] = df[column].astype(str).str.strip()
    return df


def load_exam_topics() -> pd.DataFrame:
    """Return the cached DataFrame of exam topics, storing it in session state."""

    if "exam_topics_df" not in st.session_state:
        st.session_state["exam_topics_df"] = _load_exam_topics_cached()
    return st.session_state["exam_topics_df"]


def save_exam_progress(student_code: Optional[str], progress_items: Sequence[Dict[str, str]], *, db=None) -> None:
    """Persist completed exam prompts for a student."""

    if not student_code:
        return

    firestore = db or get_db()
    if firestore is None:
        return

    doc_ref = firestore.collection("exam_progress").document(student_code)
    try:
        doc = doc_ref.get()
        data = doc.to_dict() if doc.exists else {}
    except Exception:  # pragma: no cover - tolerate transient Firestore issues
        logging.exception("Failed to load exam progress for student %s", student_code)
        return

    all_progress: List[Dict[str, str]] = list(data.get("completed", [])) if isinstance(data, dict) else []
    for item in progress_items:
        if not item:
            continue
        already = any(
            p.get("level") == item.get("level")
            and p.get("teil") == item.get("teil")
            and p.get("topic") == item.get("topic")
            for p in all_progress
        )
        if not already:
            payload = {
                "level": item.get("level", ""),
                "teil": item.get("teil", ""),
                "topic": item.get("topic", ""),
            }
            payload["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            all_progress.append(payload)

    try:
        doc_ref.set({"completed": all_progress}, merge=True)
    except Exception:  # pragma: no cover - Firestore writes may fail in tests
        logging.exception("Failed to save exam progress for student %s", student_code)


@dataclass
class ExamPrompts:
    instruction: str
    system_prompt: str


def build_a1_exam_intro() -> str:
    return (
        "**A1 – Teil 1: Basic Introduction**\n\n"
        "In the A1 exam's first part, you will be asked to introduce yourself. "
        "Typical information includes: your **Name, Land, Wohnort, Sprachen, Beruf, Hobby**.\n\n"
        "After your introduction, you will be asked 3 basic questions such as:\n"
        "- Haben Sie Geschwister?\n"
        "- Wie alt ist deine Mutter?\n"
        "- Bist du verheiratet?\n\n"
        "You might also be asked to spell your name (**Buchstabieren**). "
        "Please introduce yourself now using all the keywords above."
    )


def build_exam_instruction(level: str, teil: str) -> str:
    if level == "A1":
        if "Teil 1" in teil:
            return build_a1_exam_intro()
        if "Teil 2" in teil:
            return (
                "**A1 – Teil 2: Question and Answer**\n\n"
                "You will get a topic and a keyword. Your job: ask a question using the keyword, "
                "then answer it yourself. Example: Thema: Geschäft – Keyword: schließen → "
                "Wann schließt das Geschäft?\nLet's try one. Type 'Yes' in the chatbox so we start?"
            )
        if "Teil 3" in teil:
            return (
                "**A1 – Teil 3: Making a Request**\n\n"
                "You'll receive a prompt (e.g. 'Radio anmachen'). Write a polite request or imperative. "
                "Example: Können Sie bitte das Radio anmachen?\nReady? Type Yes in the chatbox so we start?"
            )
    if level == "A2":
        if "Teil 1" in teil:
            return (
                "**A2 – Teil 1: Fragen zu Schlüsselwörtern**\n\n"
                "You'll get a topic (e.g. 'Wohnort'). Ask a question, then answer it yourself. "
                "When you're ready, type 'Begin'."
            )
        if "Teil 2" in teil:
            return (
                "**A2 – Teil 2: Über das Thema sprechen**\n\n"
                "Talk about the topic in 3–4 sentences. I'll correct and give tips. Start when ready."
            )
        if "Teil 3" in teil:
            return (
                "**A2 – Teil 3: Gemeinsam planen**\n\n"
                "Let's plan something together. Respond and make suggestions. Start when ready."
            )
    if level == "B1":
        if "Teil 1" in teil:
            return (
                "**B1 – Teil 1: Gemeinsam planen**\n\n"
                "We'll plan an activity together (e.g., a trip or party). Give your ideas and answer questions."
            )
        if "Teil 2" in teil:
            return (
                "**B1 – Teil 2: Präsentation**\n\n"
                "Give a short presentation on the topic (about 2 minutes). I'll ask follow-up questions."
            )
        if "Teil 3" in teil:
            return (
                "**B1 – Teil 3: Feedback & Fragen stellen**\n\n"
                "Answer questions about your presentation. I'll give you feedback on your language and structure."
            )
    if level == "B2":
        if "Teil 1" in teil:
            return (
                "**B2 – Teil 1: Diskussion**\n\n"
                "We'll discuss a topic. Express your opinion and justify it."
            )
        if "Teil 2" in teil:
            return (
                "**B2 – Teil 2: Präsentation**\n\n"
                "Present a topic in detail. I'll challenge your points and help you improve."
            )
        if "Teil 3" in teil:
            return (
                "**B2 – Teil 3: Argumentation**\n\n"
                "Argue your perspective. I'll give feedback and counterpoints."
            )
    if level == "C1":
        if "Teil 1" in teil:
            return (
                "**C1 – Teil 1: Vortrag**\n\n"
                "Bitte halte einen kurzen Vortrag zum Thema. Ich werde anschließend Fragen stellen und deine Sprache bewerten."
            )
        if "Teil 2" in teil:
            return (
                "**C1 – Teil 2: Diskussion**\n\n"
                "Diskutiere mit mir über das gewählte Thema. Ich werde kritische Nachfragen stellen."
            )
        if "Teil 3" in teil:
            return (
                "**C1 – Teil 3: Bewertung**\n\n"
                "Bewerte deine eigene Präsentation. Was würdest du beim nächsten Mal besser machen?"
            )
    return ""


def build_exam_system_prompt(level: str, teil: str, student_code: str = "felixa1") -> str:
    rec_url = (
        "https://script.google.com/macros/s/AKfycbzMIhHuWKqM2ODaOCgtS7uZCikiZJRBhpqv2p6OyBmK1yAVba8HlmVC1zgTcGWSTfrsHA/exec"
        f"?code={student_code}"
    )
    record_line = (
        "IMPORTANT: After EVERY question, prompt, correction, or feedback, append this line on its own:\n"
        f"• 🎙️ **You can chat here for more ideas or Record your answer now**: [Open Sprechen Recorder]({rec_url})\n"
        f"If Markdown is not supported, show the raw URL: {rec_url}\n"
    )
    if level == "A1":
        if "Teil 1" in teil:
            return (
                "You are Herr Felix, a supportive A1 German examiner. Ask the student to introduce themselves using the keywords "
                "(Name, Land, Wohnort, Sprachen, Beruf, Hobby) and remind them that they may be asked to **Buchstabieren** ihren "
                "Namen.\n"
                "After their introduction, first show the corrected German sentence(s) and then explain each error in English. "
                "Clearly report which of the required keywords were covered and list any that were missed before moving on.\n"
                "Ask exactly these three follow-up questions in order, one at a time, with gentle encouragement after every reply:\n"
                "1. Haben Sie Geschwister?\n2. Wie alt ist deine Mutter?\n3. Bist du verheiratet?\n"
                "Finish with an encouraging summary plus a score out of 25 that explicitly states Pass or Not yet Pass.\n"
            + record_line
        )
        if "Teil 2" in teil:
            return (
                "You are Herr Felix, an encouraging A1 examiner. Give the student the Thema and Keyword, reminding them that "
                "**Buchstabieren** may be requested in the A1 exam. Guide them through exactly three rounds. In every round they "
                "must ask one question that uses the keyword and then answer it themselves.\n"
                "After each response, present the corrected German sentence(s) followed by English explanations of the mistakes, "
                "and confirm whether the keyword was used; if it was missing, prompt them to include it before continuing.\n"
                "Once the three rounds are complete, ask the same trio of follow-up questions as Teil 1 in the same order, keeping "
                "the tone warm and supportive. Conclude with a short summary plus a score out of 25 that clearly states Pass or "
                "Not yet Pass.\n"
            + record_line
        )
        if "Teil 3" in teil:
            return (
                "You are Herr Felix, a friendly A1 examiner. Provide a polite request prompt (e.g., 'Radio anmachen') and remind "
                "the student about **Buchstabieren** expectations for the speaking exam.\n"
                "Have them respond three times with appropriate polite requests or imperatives that include the key action from "
                "the prompt. After each reply, display the corrected German version first and then explain the errors in English, "
                "noting whether the prompt's keyword or action was fully covered.\n"
                "When the three attempts are done, ask exactly the same three follow-up questions used in Teil 1, keeping the "
                "delivery warm. Wrap up with motivating feedback plus a score out of 25 that clearly says Pass or Not yet Pass.\n"
            + record_line
        )
    if level == "A2":
        if "Teil 1" in teil:
            return (
                "You are Herr Felix, A2 examiner. Give a topic; student asks & answers one question per keyword (3 total). "
                "Correct in English, show correct version, then /25 score and pass/not yet at the end.\n"
                + record_line
            )
        if "Teil 2" in teil:
            return (
                "You are Herr Felix, A2 examiner. Student gives a short monologue; correct in English, ask 3 questions total, "
                "then /25 score with pass/not yet and why.\n"
                + record_line
            )
        if "Teil 3" in teil:
            return (
                "You are Herr Felix, A2 examiner. Plan together in 5 short prompts; correct errors; "
                "finish with /25 score and pass/not yet with explanation.\n"
                + record_line
            )
    if level == "B1":
        if "Teil 1" in teil:
            return (
                "You are Herr Felix, B1 examiner. Plan an activity. Keep replies short and encouraging. "
                "Ask 5 questions total, then give /25 with English explanation.\n"
                + record_line
            )
        if "Teil 2" in teil:
            return (
                "You are Herr Felix, B1 examiner. Student presents; ask 3 questions total, keep friendly, "
                "then give /25 with English explanation.\n"
                + record_line
            )
        if "Teil 3" in teil:
            return (
                "You are Herr Felix, B1 examiner. Ask 3 follow-up questions about their presentation, "
                "correct language and motivate, then /25 with English explanation.\n"
                + record_line
            )
    if level == "B2":
        if "Teil 1" in teil:
            return (
                "You are Herr Felix, B2 examiner. Hold a discussion, challenge their ideas, and keep it constructive.\n"
                + record_line
            )
        if "Teil 2" in teil:
            return (
                "You are Herr Felix, B2 examiner. The student presents a topic; ask probing questions and correct mistakes.\n"
                + record_line
            )
        if "Teil 3" in teil:
            return (
                "You are Herr Felix, B2 examiner. Debate their stance, offer counterpoints, and summarise feedback.\n"
                + record_line
            )
    if level == "C1":
        if "Teil 1" in teil:
            return (
                "You are Herr Felix, C1 examiner. Ask for an in-depth presentation, challenge their arguments, "
                "and assess structure and vocabulary.\n"
                + record_line
            )
        if "Teil 2" in teil:
            return (
                "You are Herr Felix, C1 examiner. Lead a critical discussion, ask for justifications, "
                "and provide nuanced corrections.\n"
                + record_line
            )
        if "Teil 3" in teil:
            return (
                "You are Herr Felix, C1 examiner. Help them reflect on their performance and give advanced suggestions.\n"
                + record_line
            )
    return record_line


def build_exam_prompts(
    level: str,
    teil: str,
    topic: Optional[str],
    keyword: Optional[str],
    student_code: str,
) -> ExamPrompts:
    base_prompt = build_exam_system_prompt(level, teil, student_code)
    system_prompt = base_prompt
    if topic:
        system_prompt = f"{system_prompt} Thema: {topic}."
        if keyword:
            system_prompt = f"{system_prompt} Keyword: {keyword}."
    return ExamPrompts(
        instruction=build_exam_instruction(level, teil),
        system_prompt=system_prompt,
    )


def _render_links(links: Iterable[Tuple[str, str]], *, box_color: str, text_color: str, title: str) -> None:
    st.markdown(
        "<div style='background:%s;border-radius:10px;padding:1.1em 1.4em;margin:1.2em 0;'>"
        "<span style='font-size:1.18em;color:%s;'><b>%s</b></span><br><br>"
        % (box_color, text_color, title),
        unsafe_allow_html=True,
    )
    for label, url in links:
        st.markdown(
            f"<a href=\"{url}\" target=\"_blank\" style=\"font-size:1.10em;color:{text_color};font-weight:600\">👉 {label}</a><br>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


@dataclass
class ExamSetupResult:
    teil: Optional[str]
    topic: Optional[str]
    keyword: Optional[str]
    started: bool


TeilOptions = Dict[str, Sequence[str]]


def render_exam_setup(
    *,
    level: Optional[str] = None,
    teil_options: Optional[TeilOptions] = None,
    reset_chat_flow: Optional[Callable[..., None]] = None,
    back_step: Optional[Callable[[], None]] = None,
    db=None,
) -> ExamSetupResult:
    """Render the exam setup screen and return the chosen topic information."""

    level = level or st.session_state.get("falowen_level", "A1")
    options: TeilOptions = teil_options or {
        "A1": [
            "Teil 1 – Basic Introduction",
            "Teil 2 – Question and Answer",
            "Teil 3 – Making A Request",
            "Lesen – Past Exam Reading",
            "Hören – Past Exam Listening",
        ],
        "A2": [
            "Teil 1 – Fragen zu Schlüsselwörtern",
            "Teil 2 – Über das Thema sprechen",
            "Teil 3 – Gemeinsam planen",
            "Lesen – Past Exam Reading",
            "Hören – Past Exam Listening",
        ],
        "B1": [
            "Teil 1 – Gemeinsam planen (Dialogue)",
            "Teil 2 – Präsentation (Monologue)",
            "Teil 3 – Feedback & Fragen stellen",
            "Lesen – Past Exam Reading",
            "Hören – Past Exam Listening",
        ],
        "B2": [
            "Teil 1 – Diskussion",
            "Teil 2 – Präsentation",
            "Teil 3 – Argumentation",
            "Lesen – Past Exam Reading",
            "Hören – Past Exam Listening",
        ],
        "C1": [
            "Teil 1 – Vortrag",
            "Teil 2 – Diskussion",
            "Teil 3 – Bewertung",
            "Lesen – Past Exam Reading",
            "Hören – Past Exam Listening",
        ],
    }

    st.subheader("Step 3: Choose Exam Part")
    teil = st.radio("Which exam part?", options[level], key="falowen_teil_center")

    if "Lesen" in teil or "Hören" in teil:
        if "Lesen" in teil:
            _render_links(lesen_links.get(level, []), box_color="#e1f5fe", text_color="#0277bd", title="📖 Past Exam: Lesen (Reading)")
        if "Hören" in teil:
            _render_links(hoeren_links.get(level, []), box_color="#ede7f6", text_color="#512da8", title="🎧 Past Exam: Hören (Listening)")

        if st.button("⬅️ Back", key="lesen_hoeren_back"):
            st.session_state["falowen_stage"] = 2
            st.session_state["falowen_messages"] = []
            rerun_without_toast()
        return ExamSetupResult(teil=teil, topic=None, keyword=None, started=False)

    teil_number = teil.split()[1] if "Teil" in teil else ""
    exam_df = load_exam_topics()
    exam_topics = exam_df[(exam_df["Level"] == level) & (exam_df["Teil"] == f"Teil {teil_number}")].copy()

    topics_list: List[str] = []
    if not exam_topics.empty:
        topic_vals = exam_topics["Topic/Prompt"].astype(str).str.strip()
        keyword_vals = exam_topics["Keyword/Subtopic"].astype(str).str.strip()
        topics_list = [f"{t} – {k}" if k else t for t, k in zip(topic_vals, keyword_vals) if t]

    search = st.text_input("🔍 Search topic or keyword...", "")
    filtered = [t for t in topics_list if search.lower() in t.lower()] if search else topics_list

    topic: Optional[str] = None
    keyword: Optional[str] = None

    if filtered:
        st.markdown("**Preview: Available Topics**")
        for item in filtered[:6]:
            st.markdown(f"- {item}")
        if len(filtered) > 6:
            with st.expander(f"See all {len(filtered)} topics"):
                col1, col2 = st.columns(2)
                for idx, item in enumerate(filtered):
                    container = col1 if idx % 2 == 0 else col2
                    with container:
                        st.markdown(f"- {item}")

        choice = st.selectbox("Pick your topic (or choose random):", ["(random)"] + filtered, key="topic_picker")
        chosen = random.choice(filtered) if choice == "(random)" else choice
        if " – " in chosen:
            topic, keyword = chosen.split(" – ", 1)
        else:
            topic, keyword = chosen, None

        if topic:
            st.session_state["falowen_exam_topic"] = topic
            st.session_state["falowen_exam_keyword"] = keyword
            keyword_suffix = f" – {keyword}" if keyword else ""
            st.success(f"**Your exam topic is:** {topic}{keyword_suffix}")
    else:
        st.info("No topics found. Try a different search.")

    col_mode, col_level, col_start = st.columns([1, 1, 2])
    with col_mode:
        if st.button("↩ Back to Mode", key="falowen_back_mode") and back_step:
            back_step()
    with col_level:
        if st.button("⬅️ Back", key="falowen_back_part"):
            st.session_state["falowen_stage"] = 2
            st.session_state["falowen_messages"] = []
            rerun_without_toast()
    with col_start:
        start_disabled = not topic
        if (
            st.button("Start Practice", key="falowen_start_practice", disabled=start_disabled)
            and topic
        ):
            st.session_state["falowen_teil"] = teil
            st.session_state["falowen_stage"] = 4
            if reset_chat_flow:
                reset_chat_flow()
            student_code = st.session_state.get("student_code")
            save_exam_progress(student_code, [{"level": level, "teil": teil, "topic": topic}], db=db)
            rerun_without_toast()
            return ExamSetupResult(teil=teil, topic=topic, keyword=keyword, started=True)

    if not topic:
        st.warning("Please select a topic before starting your practice session.")

    return ExamSetupResult(teil=teil, topic=topic, keyword=keyword, started=False)


__all__ = [
    "ExamPrompts",
    "ExamSetupResult",
    "lesen_links",
    "hoeren_links",
    "load_exam_topics",
    "save_exam_progress",
    "build_exam_instruction",
    "build_exam_system_prompt",
    "build_exam_prompts",
    "render_exam_setup",
]
