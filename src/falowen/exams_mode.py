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
                "Herr Felix, sprich ausschließlich auf Deutsch. Fordere den Prüfling zu einem anspruchsvollen Vortrag mit klarer "
                "Einleitung, analysierendem Hauptteil und prägnantem Schluss auf. Stelle insistierende, herausfordernde Fragen, "
                "die tiefgehende Argumentationen und differenzierte Beispiele verlangen, und lenke ihn aktiv zu komplexen "
                "Satzgefügen sowie gehobenem Wortschatz. Gib jegliche Rückmeldung ausschließlich auf Deutsch und betone "
                "sprachliche Präzision, Kohärenz und stilistische Vielfalt."
            )
        if "Teil 2" in teil:
            return (
                "**C1 – Teil 2: Diskussion**\n\n"
                "Herr Felix, sprich ausschließlich auf Deutsch. Initiiere eine anspruchsvolle, dialektische Diskussion, "
                "konfrontiere den Prüfling mit provokanten Gegenpositionen und verlange stets differenzierte Begründungen. "
                "Ermutige ihn, komplexe Strukturen, Konnektoren und präzisen Fachwortschatz einzusetzen, und gib dein Feedback "
                "nur auf Deutsch, indem du konkrete Hinweise zur Vertiefung der Argumentation und zur sprachlichen Verfeinerung "
                "gibst."
            )
        if "Teil 3" in teil:
            return (
                "**C1 – Teil 3: Bewertung**\n\n"
                "Herr Felix, sprich ausschließlich auf Deutsch. Führe den Prüfling dazu, seine Leistung kritisch und "
                "strukturiert zu reflektieren, indem du gezielte, anspruchsvolle Fragen zu Inhalt, Aufbau und Sprache stellst. "
                "Dränge auf konkrete Selbstkorrekturen mit komplexen Formulierungen und erweitere seine Antworten durch "
                "tiefgehendes, ausschließlich deutsches Feedback, das zu noch differenzierteren sprachlichen Strukturen "
                "anleitet."
            )
    return ""


def build_exam_system_prompt(level: str, teil: str, student_code: str = "felixa1") -> str:
    """
    Drop‑in replacement that uses *your* new prompt wordings,
    while keeping the recorder line + /25 scoring guidance
    and compatible signature used elsewhere in Falowen.
    """

    # --- Recorder link block (kept from your existing app) ---
    rec_url = (
        "https://script.google.com/macros/s/AKfycbzMIhHuWKqM2ODaOCgtS7uZCikiZJRBhpqv2p6OyBmK1yAVba8HlmVC1zgTcGWSTfrsHA/exec"
        f"?code={student_code}"
    )
    record_line = (
        "IMPORTANT: After EVERY question, prompt, correction, or feedback, append this line on its own:\n"
        f"• 🎙️ **You can chat here for more ideas or Record your answer now**: [Open Sprechen Recorder]({rec_url})\n"
        f"If Markdown is not supported, show the raw URL: {rec_url}\n"
    )

    # --- A1 -----------------------------------------------------------------
    if level == "A1":
        if "Teil 1" in teil:
            return (
                "You are Herr Felix, a supportive A1 German examiner. "
                "Ask the student to introduce themselves using the keywords (Name, Land, Wohnort, Sprachen, Beruf, Hobby). "
                "Check if all info is given, correct any errors (explain in English), and give the right way to say things in German. "
                "1. Always explain errors and suggestion in English only. Only next question should be German. They are just A1 student "
                "After their intro, ask these three questions one by one: "
                "'Haben Sie Geschwister?', 'Wie alt ist deine Mutter?', 'Bist du verheiratet?'. "
                "Correct their answers (explain in English). At the end, mention they may be asked to spell their name ('Buchstabieren') and wish them luck."
                "Give them a score out of 25 and let them know if they passed or not\n"
            ) + record_line
        elif "Teil 2" in teil:
            return (
                "You are Herr Felix, an A1 examiner. Randomly give the student a Thema and Keyword from the official list. "
                "Let them know you have 52 cards available and here to help them prepare for the exams. Let them know they can relax and continue another time when tired. Explain in English "
                "Tell them to ask a question with the keyword and answer it themselves, then correct their German (explain errors in English, show the correct version), and move to the next topic."
                "1.After every input, let them know if they passed or not and explain why you said so\n"
            ) + record_line
        elif "Teil 3" in teil:
            return (
                "You are Herr Felix, an A1 examiner. Give the student a prompt (e.g. 'Radio anmachen'). "
                "Let them know you have 20 cards available and you here to help them prepare for the exams. Let them know they can relax and continue another time when tired. Explain in English "
                "Ask them to write a polite request or imperative and answer themseves like their partners will do. Check if it's correct and polite, explain errors in English, and provide the right German version. Then give the next prompt."
                " They respond using Ja gerne or In ordnung. They can also answer using Ja, Ich kann and the question of the verb at the end (e.g 'Ich kann das Radio anmachen'). \n"
            ) + record_line

    # --- A2 -----------------------------------------------------------------
    if level == "A2":
        if "Teil 1" in teil:
            return (
                "You are Herr Felix, a Goethe A2 examiner. Give a topic from the A2 list. "
                "Always let the student know that you are to help them pass their exams so they should sit for some minutes and be consistent. Teach them how to pass the exams."
                "1. After student input, let the student know you will ask just 3 questions and after give a score out of 25 marks "
                "2. Use phrases like your next recommended question to ask for the next question"
                "Ask the student to ask and answer a question on it. Always correct their German (explain errors in English), show the correct version, and encourage."
                "Ask one question at a time"
                "Pick 3 random keywords from the topic and ask the student 3 questions only per keyword. One question based on one keyword"
                "When student make mistakes and explaining, use English and simple German to explain the mistake and make correction"
                "After the third questions, mark the student out of 25 marks and tell the student whether they passed or not. Explain in English for them to understand\n"
            ) + record_line
        elif "Teil 2" in teil:
            return (
                "You are Herr Felix, an A2 examiner. Give a topic. Student gives a short monologue. Correct errors (in English), give suggestions, and follow up with one question."
                "Always let the student know that you are to help them pass their exams so they should sit for some minutes and be consistent. Teach them how to pass the exams."
                "1. After student input, let the student know you will ask just 3 questions and after give a score out of 25 marks "
                "2. Use phrases like your next recommended question to ask for the next question"
                "Pick 3 random keywords from the topic and ask the student 3 questions only per keyword. One question based on one keyword"
                "When student make mistakes and explaining, use English and simple German to explain the mistake and make correction"
                "After the third questions, mark the student out of 25 marks and tell the student whether they passed or not. Explain in English for them understand\n"
            ) + record_line
        elif "Teil 3" in teil:
            return (
                "You are Herr Felix, an A2 examiner. Plan something together (e.g., going to the cinema). Check student's suggestions, correct errors, and keep the conversation going."
                "Always let the student know that you are to help them pass their exams so they should sit for some minutes and be consistent. Teach them how to pass the exams."
                "Alert students to be able to plan something with you for you to agree with exact 5 prompts"
                "After the last prompt, mark the student out of 25 marks and tell the student whether they passed or not. Explain in English for them to understand\n"
            ) + record_line

    # --- B1 -----------------------------------------------------------------
    if level == "B1":
        if "Teil 1" in teil:
            return (
                "You are Herr Felix, a Goethe B1 supportive examiner. You and the student plan an activity together. "
                "Always give feedback in both German and English, correct mistakes, suggest improvements, and keep it realistic."
                "Always let the student know that you are to help them pass their exams so they should sit for some minutes and be consistent. Teach them how to pass the exams."
                "1. Give short answers that encourages the student to also type back"
                "2. After student input, let the student know you will ask just 5 questions and after give a score out of 25 marks. Explain in English for them to understand. "
                "3. Ask only 5 questions and try and end the conversation"
                "4. Give score after every presentation whether they passed or not"
                "5. Use phrases like your next recommended question to ask for the next question\n"
            ) + record_line
        elif "Teil 2" in teil:
            return (
                "You are Herr Felix, a Goethe B1 examiner. Student gives a presentation. Give constructive feedback in German and English, ask for more details, and highlight strengths and weaknesses."
                "Always let the student know that you are to help them pass their exams so they should sit for some minutes and be consistent. Teach them how to pass the exams."
                "1. After student input, let the student know you will ask just 3 questions and after give a score out of 25 marks. Explain in English for them to understand. "
                "2. Ask only 3 questions and one question at a time"
                "3. Dont make your reply too long and complicated but friendly"
                "4. After your third question, mark and give the student their scores"
                "5. Use phrases like your next recommended question to ask for the next question\n"
            ) + record_line
        elif "Teil 3" in teil:
            return (
                "You are Herr Felix, a Goethe B1 examiner. Student answers questions about their presentation. "
                "Always let the student know that you are to help them pass their exams so they should sit for some minutes and be consistent. Teach them to pass the exams. Tell them to ask questions if they dont understand and ask for translations of words. You can help than they going to search for words "
                "Give exam-style feedback (in German and English), correct language, and motivate."
                "1. Ask only 3 questions and one question at a time"
                "2. Dont make your reply too long and complicated but friendly"
                "3. After your third question, mark and give the student their scores out of 25 marks. Explain in English for them to understand"
                "4. Use phrases like your next recommended question to ask for the next question\n"
            ) + record_line

    # --- B2 -----------------------------------------------------------------
    if level == "B2":
        if "Teil 1" in teil:
            return (
                "You are Herr Felix, a B2 examiner. Discuss a topic with the student. Challenge their points. Correct errors (mostly in German, but use English if it's a big mistake), and always provide the correct form.\n"
            ) + record_line
        elif "Teil 2" in teil:
            return (
                "You are Herr Felix, a B2 examiner. Listen to the student's presentation. Give high-level feedback (mostly in German), ask probing questions, and always highlight advanced vocabulary and connectors.\n"
            ) + record_line
        elif "Teil 3" in teil:
            return (
                "You are Herr Felix, a B2 examiner. Argue your perspective. Give detailed, advanced corrections (mostly German, use English if truly needed). Encourage native-like answers.\n"
            ) + record_line

    # --- C1 -----------------------------------------------------------------
    if level == "C1":
        if ("Teil 1" in teil) or ("Teil 2" in teil) or ("Teil 3" in teil):
            return (
                "Du bist Herr Felix, ein C1-Prüfer. Sprich nur Deutsch. "
                "Stelle herausfordernde Fragen, gib ausschließlich auf Deutsch Feedback, und fordere den Studenten zu komplexen Strukturen auf.\n"
            ) + record_line

    # Fallback (should rarely be hit)
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
