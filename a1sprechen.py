# ===============================
#         STAGE 1: IMPORTS, CONSTANTS, ALL TOPIC LISTS
# ===============================

import os
import io
import re
import random
import tempfile
from datetime import date

import pandas as pd
import streamlit as st
from openai import OpenAI

# --- General constants ---
CODES_FILE = "student_codes.csv"
DAILY_LIMIT = 25
MAX_TURNS = 6

# ========== A1 TEIL 1 ==========
A1_TEIL1_KEYWORDS = ["Name", "Alter", "Land", "Wohnort", "Sprachen", "Beruf", "Hobby"]
A1_TEIL1_FOLLOWUP = [
    "Wie buchstabieren Sie Ihren Namen?",
    "Sind Sie verheiratet? (Ja/Nein)",
    "Wie alt ist Ihre Mutter?",
    "Haben Sie Geschwister?",
    "Welche Sprachen sprechen Sie?",
    "Was machen Sie gern in Ihrer Freizeit?"
]
# ========== A1 TEIL 2 ==========
A1_VOCAB_TEIL2 = [
    ("Geschäft", "schließen"), ("Uhr", "Uhrzeit"), ("Arbeit", "Kollege"),
    ("Hausaufgabe", "machen"), ("Küche", "kochen"), ("Freizeit", "lesen"),
    ("Telefon", "anrufen"), ("Reise", "Hotel"), ("Auto", "fahren"),
    ("Einkaufen", "Obst"), ("Schule", "Lehrer"), ("Geburtstag", "Geschenk"),
    ("Essen", "Frühstück"), ("Arzt", "Termin"), ("Zug", "Abfahrt"),
    ("Wetter", "Regen"), ("Buch", "lesen"), ("Computer", "E-Mail"),
    ("Kind", "spielen"), ("Wochenende", "Plan"), ("Bank", "Geld"),
    ("Sport", "laufen"), ("Abend", "Fernsehen"), ("Freunde", "Besuch"),
    ("Bahn", "Fahrkarte"), ("Straße", "Stau"), ("Essen gehen", "Restaurant"),
    ("Hund", "Futter"), ("Familie", "Kinder"), ("Post", "Brief"),
    ("Nachbarn", "laut"), ("Kleid", "kaufen"), ("Büro", "Chef"),
    ("Urlaub", "Strand"), ("Kino", "Film"), ("Internet", "Seite"),
    ("Bus", "Abfahrt"), ("Arztpraxis", "Wartezeit"), ("Kuchen", "backen"),
    ("Park", "spazieren"), ("Bäckerei", "Brötchen"), ("Geldautomat", "Karte"),
    ("Buchladen", "Roman"), ("Fernseher", "Programm"), ("Tasche", "vergessen"),
    ("Stadtplan", "finden"), ("Ticket", "bezahlen"), ("Zahnarzt", "Schmerzen"),
    ("Museum", "Öffnungszeiten"), ("Handy", "Akku leer"),
]
# ========== A1 TEIL 3 ==========
A1_BITTEN_PROMPTS = [
    "Radio anmachen", "Fenster zumachen", "Licht anschalten", "Tür aufmachen",
    "Tisch sauber machen", "Hausaufgaben schicken", "Buch bringen",
    "Handy ausmachen", "Stuhl nehmen", "Wasser holen", "Fenster öffnen",
    "Musik leiser machen", "Tafel sauber wischen", "Kaffee kochen",
    "Deutsch üben", "Auto waschen", "Kind abholen", "Tisch decken",
    "Termin machen", "Nachricht schreiben",
]

# ======= B2 (28 TOPICS) =======
B2_TEIL1_THEMEN = [
    "Mediennutzung", "Globalisierung", "Kulturelle Vielfalt", "Umweltschutz", "Technologischer Fortschritt",
    "Arbeitswelt", "Mobilität", "Gesundheitswesen", "Familienmodelle", "Bildungssysteme",
    "Ehrenamtliches Engagement", "Migration", "Integration", "Freizeitgestaltung", "Konsumgesellschaft",
    "Tourismus", "Digitalisierung", "Soziale Netzwerke", "Berufswahl", "Ernährungstrends",
    "Sport und Gesellschaft", "Kunst und Kultur", "Recht und Gerechtigkeit", "Wissenschaft und Forschung",
    "Klimawandel", "Wohnen in der Stadt", "Traditionen und Feste", "Gleichberechtigung",
    "Politische Partizipation"
]

B2_TEIL2_PRESENTATION = [
    "Diskutiere Vor- und Nachteile der Digitalisierung.",
    "Beschreibe eine Erfahrung mit interkultureller Kommunikation.",
    "Erkläre die Bedeutung nachhaltiger Lebensweise.",
    "Erörtere Chancen und Risiken von sozialen Netzwerken.",
    "Präsentiere Argumente für und gegen Fast Fashion.",
    "Stelle dar, wie sich Mobilität auf den Alltag auswirkt.",
    "Diskutiere Auswirkungen des Klimawandels auf die Gesellschaft.",
    "Präsentiere Vorteile von Homeoffice.",
    "Stelle einen aktuellen Ernährungstrend vor.",
    "Erkläre die Rolle ehrenamtlicher Arbeit.",
    "Beschreibe das Bildungssystem in deinem Land.",
    "Präsentiere deine Meinung zum Thema Integration.",
    "Diskutiere, wie Digitalisierung die Arbeitswelt verändert.",
    "Erörtere die Bedeutung von Gleichberechtigung.",
    "Beschreibe Vor- und Nachteile von Tourismus.",
    "Präsentiere einen Trend in Kunst oder Kultur.",
    "Diskutiere, warum Sport wichtig für die Gesellschaft ist.",
    "Beschreibe Traditionen und Feste in deinem Land.",
    "Erkläre die Rolle von Medien in der heutigen Zeit.",
    "Stelle Möglichkeiten vor, umweltfreundlich zu leben.",
    "Diskutiere Herausforderungen im Gesundheitswesen.",
    "Erkläre, wie politische Partizipation gefördert werden kann.",
    "Präsentiere eine berühmte Persönlichkeit aus Wissenschaft oder Forschung.",
    "Diskutiere das Thema Konsumverhalten.",
    "Erörtere das Thema Wohnen in der Stadt.",
    "Beschreibe ein Beispiel für soziale Gerechtigkeit.",
    "Diskutiere aktuelle Entwicklungen in der Kunstwelt.",
    "Beschreibe die Bedeutung von Familie heute."
]

B2_TEIL3_ARGUMENTATION = [
    "Argumentieren Sie für oder gegen das Homeoffice.",
    "Diskutieren Sie die Auswirkungen des Klimawandels auf die Gesellschaft.",
    "Sollten alle Schüler eine Schuluniform tragen?",
    "Ist eine vegetarische Ernährung besser für die Umwelt?",
    "Sind soziale Netzwerke Fluch oder Segen?",
    "Sollte das Autofahren in Großstädten eingeschränkt werden?",
    "Brauchen wir mehr Frauen in Führungspositionen?",
    "Ist das Ehrenamt in Gefahr?",
    "Sollte man schon in der Schule Programmieren lernen?",
    "Sind traditionelle Familienmodelle überholt?",
    "Ist Fast Fashion ein Problem?",
    "Braucht jede Stadt ein Fahrradverleihsystem?",
    "Sollte Plastiktüten verboten werden?",
    "Darf man Kunstwerke digitalisieren und frei zugänglich machen?",
    "Ist Tourismus gut für die Wirtschaft?",
    "Braucht man für Erfolg ein Studium?",
    "Sind Noten in der Schule wichtig?",
    "Sollten Haustiere in Mietwohnungen erlaubt sein?",
    "Sollte der Sonntag ein Ruhetag bleiben?",
    "Ist vegetarisches Leben gesünder?",
    "Sollte das Recht auf Homeoffice gesetzlich garantiert sein?",
    "Sind große Sportereignisse sinnvoll?",
    "Darf Werbung für ungesunde Lebensmittel verboten werden?",
    "Sollte es mehr Bürgerbeteiligung in der Politik geben?",
    "Ist Fernsehen heute noch zeitgemäß?",
    "Sollten Einwegprodukte verboten werden?",
    "Ist das Leben auf dem Land besser als in der Stadt?",
    "Sollte Wissenschaft besser finanziert werden?"
]

# ======= C1 (28 TOPICS) =======
C1_TEIL1_THEMEN = [
    "Arbeitswelt der Zukunft", "Künstliche Intelligenz", "Ethik in der Wissenschaft", "Migration",
    "Umwelt- und Klimapolitik", "Globalisierung", "Chancengleichheit", "Digitalisierung und Datenschutz",
    "Gesellschaftlicher Wandel", "Demografischer Wandel", "Gender und Diversität", "Bildungsgerechtigkeit",
    "Fake News und Medienkompetenz", "Internationale Beziehungen", "Nachhaltige Entwicklung",
    "Kulturelle Identität", "Literatur und Gesellschaft", "Innovation und Unternehmertum",
    "Gesundheitssysteme im internationalen Vergleich", "Lebenslanges Lernen", "Wissenschaftskommunikation",
    "Soziale Ungleichheit", "Kritische Medienanalyse", "Populismus und Demokratie",
    "Werte in der modernen Gesellschaft", "Wirtschaftsethik", "Interkulturelle Kommunikation",
    "Forschungsethik", "Urbanisierung"
]

C1_TEIL2_PRESENTATION = [
    "Halten Sie einen Vortrag über Chancen und Risiken von Social Media.",
    "Diskutieren Sie ethische Fragen der Genforschung.",
    "Analysieren Sie die Rolle von Migration in modernen Gesellschaften.",
    "Präsentieren Sie einen aktuellen Trend in der Arbeitswelt.",
    "Erörtern Sie die Herausforderungen der Digitalisierung im Alltag.",
    "Diskutieren Sie die Bedeutung von Nachhaltigkeit in Unternehmen.",
    "Reflektieren Sie die Auswirkungen des demografischen Wandels.",
    "Erklären Sie die Bedeutung von Medienkompetenz.",
    "Präsentieren Sie die Rolle von Kunst und Literatur für die Gesellschaft.",
    "Erörtern Sie das Thema Wertewandel.",
    "Stellen Sie Herausforderungen im Bildungssystem dar.",
    "Diskutieren Sie globale Probleme des Gesundheitssystems.",
    "Präsentieren Sie einen wissenschaftlichen Durchbruch.",
    "Reflektieren Sie über interkulturelle Kommunikation.",
    "Erörtern Sie aktuelle Herausforderungen in der internationalen Politik.",
    "Analysieren Sie die Wirkung von Fake News.",
    "Diskutieren Sie Populismus und Demokratie.",
    "Präsentieren Sie Lösungsansätze für soziale Ungleichheit.",
    "Erörtern Sie Innovation und Unternehmertum.",
    "Diskutieren Sie Chancen und Risiken künstlicher Intelligenz.",
    "Reflektieren Sie den Einfluss von Urbanisierung.",
    "Analysieren Sie den Zusammenhang zwischen Wirtschaft und Ethik.",
    "Diskutieren Sie Forschungsethik am Beispiel eines konkreten Falls.",
    "Erörtern Sie den Wert lebenslangen Lernens.",
    "Präsentieren Sie den Wandel kultureller Identität.",
    "Diskutieren Sie internationale Zusammenarbeit beim Klimaschutz.",
    "Analysieren Sie gesellschaftliche Herausforderungen durch Digitalisierung.",
    "Präsentieren Sie einen aktuellen gesellschaftlichen Diskurs."
]

C1_TEIL3_DISKUSSION = [
    "Reflektieren Sie über die Verantwortung von Wissenschaftlern.",
    "Diskutieren Sie über die Bedeutung lebenslangen Lernens.",
    "Sollte künstliche Intelligenz reguliert werden?",
    "Sind Quotenregelungen sinnvoll?",
    "Welche Bedeutung hat Literatur heute?",
    "Brauchen wir mehr politische Bildung an Schulen?",
    "Wie kann Nachhaltigkeit im Alltag umgesetzt werden?",
    "Welche Rolle spielt Diversität in Unternehmen?",
    "Sollten Fake News strafbar sein?",
    "Sind Grenzen der Meinungsfreiheit notwendig?",
    "Welche Herausforderungen bringt die Globalisierung?",
    "Ist Populismus eine Gefahr für Demokratien?",
    "Wie kann Forschungsethik sichergestellt werden?",
    "Sollten Unternehmen mehr Verantwortung für die Gesellschaft übernehmen?",
    "Wie wichtig ist internationale Zusammenarbeit für den Klimaschutz?",
    "Welche Risiken birgt Digitalisierung für die Privatsphäre?",
    "Wie kann soziale Ungleichheit bekämpft werden?",
    "Sollten ältere Menschen länger arbeiten dürfen?",
    "Welche Rolle spielt kulturelle Identität in der Globalisierung?",
    "Ist Urbanisierung eine Chance oder ein Problem?",
    "Wie kann man Innovation fördern?",
    "Sind traditionelle Medien noch relevant?",
    "Wie können Werte in der Gesellschaft gestärkt werden?",
    "Sollte Wissenschaft für alle zugänglich sein?",
    "Wie kann man gesellschaftlichen Wandel gestalten?",
    "Ist lebenslanges Lernen eine Pflicht?",
    "Wie kann Demokratie im digitalen Zeitalter gesichert werden?",
    "Welche Bedeutung hat Forschung für die Zukunft?"
]

# ===============================
#         STAGE 2: Helper Functions and UI Setup
# ===============================

def load_codes():
    if os.path.exists(CODES_FILE):
        df = pd.read_csv(CODES_FILE)
        if "code" not in df.columns:
            df = pd.DataFrame(columns=["code"])
        df["code"] = df["code"].astype(str).str.strip().str.lower()
    else:
        df = pd.DataFrame(columns=["code"])
    return df

def safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        pass

def setup_ui_and_state():
    st.set_page_config(
        page_title="Falowen – Your AI Conversation Partner",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    st.markdown(
        """
        <div style='display:flex;align-items:center;gap:18px;margin-bottom:22px;'>
            <img src='https://cdn-icons-png.flaticon.com/512/6815/6815043.png' width='54' style='border-radius:50%;border:2.5px solid #51a8d2;box-shadow:0 2px 8px #cbe7fb;'/>
            <div>
                <span style='font-size:2.1rem;font-weight:bold;color:#17617a;letter-spacing:2px;'>Falowen</span><br>
                <span style='font-size:1.08rem;color:#268049;'>Your personal German speaking coach (Sir Felix)</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    for var, default in [
        ("step", 1), ("student_code", ""), ("daily_usage", {}), ("messages", []),
        ("corrections", []), ("turn_count", 0)
    ]:
        if var not in st.session_state:
            st.session_state[var] = default
# ===============================
#         STAGE 3: Student Login, Welcome, and Mode Selection
# ===============================

def stage_3_login_and_mode():
    # ------ Stage 1: Student Login ------
    if st.session_state["step"] == 1:
        st.title("Student Login")
        code = st.text_input("🔑 Enter your student code to begin:")
        if st.button("Next ➡️", key="stage1_next"):
            code_clean = code.strip().lower()
            df_codes = load_codes()
            if code_clean in df_codes["code"].dropna().tolist():
                st.session_state["student_code"] = code_clean
                st.session_state["step"] = 2
            else:
                st.error("This code is not recognized. Please check with your tutor.")

    # ------ Stage 2: Welcome ------
    elif st.session_state["step"] == 2:
        fun_facts = [
            "🇬🇭 Sir Felix was born in Ghana and mastered German up to C1 level!",
            "🎓 Sir Felix studied International Management at IU International University in Germany.",
            "🏫 He founded Learn Language Education Academy to help students pass Goethe exams.",
            "💡 Sir Felix used to run a record label and produce music before becoming a language coach!",
            "🥇 He loves making language learning fun, personal, and exam-focused.",
            "📚 Sir Felix speaks English, German, and loves teaching in both.",
            "🚀 Sometimes Sir Felix will throw in a real Goethe exam question—are you ready?",
            "🤖 Sir Felix built this app himself—so every session is personalized!"
        ]
        st.success(f"**Did you know?** {random.choice(fun_facts)}")
        st.markdown(
            "<h2 style='font-weight:bold;margin-bottom:0.5em'>🧑‍🏫 Welcome to Falowen – Your Friendly German Tutor, Sir Felix!</h2>",
            unsafe_allow_html=True,
        )
        st.markdown("> Practice your German speaking or writing. Get simple AI feedback and audio answers!")
        st.info(
            """
            🎤 **This is not just chat—it's your personal exam preparation bootcamp!**
            Every time you talk to Sir Felix, imagine you are **in the exam hall**.
            Expect realistic A1, B2, C1 speaking questions, surprise prompts, and real exam tips—sometimes, you’ll even get questions from last year’s exam!
            **Want to prepare for a class presentation or your next homework?**
            👉 You can also enter your **own question or topic** at any time—perfect for practicing real classroom situations or special assignments!
            Let’s make exam training engaging, surprising, and impactful.  
            **Are you ready? Let’s go! 🚀**
            """, icon="💡"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", key="stage2_back"):
                st.session_state["step"] = 1
        with col2:
            if st.button("Next ➡️", key="stage2_next"):
                st.session_state["step"] = 3

    # ------ Stage 3: Mode Selection ------
    elif st.session_state["step"] == 3:
        st.header("Wie möchtest du üben? (How would you like to practice?)")
        mode = st.radio(
            "Choose your practice mode:",
            [
                "Geführte Prüfungssimulation (Exam Mode)",
                "Eigenes Thema/Frage (Custom Topic Chat)",
                "Präsentationstraining (Presentation Practice)"
            ],
            index=0,
            key="mode_selector"
        )
        st.session_state["selected_mode"] = mode

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", key="stage3_back"):
                st.session_state["step"] = 2
        with col2:
            if st.button("Next ➡️", key="stage3_next"):
                st.session_state["messages"] = []
                st.session_state["turn_count"] = 0
                st.session_state["corrections"] = []
                if mode == "Geführte Prüfungssimulation (Exam Mode)":
                    st.session_state["step"] = 4
                elif mode == "Eigenes Thema/Frage (Custom Topic Chat)":
                    st.session_state["step"] = 5
                elif mode == "Präsentationstraining (Presentation Practice)":
                    st.session_state["step"] = 7
# ===============================
#         STAGE 4: Exam Part Selection & AI Prompt
# ===============================

def stage_4_exam_part():
    if st.session_state["step"] != 4:
        return

    # Level detection from login step
    user_level = st.session_state.get("user_level", "A1")
    st.header("Prüfungsteil wählen / Choose exam part")
    # Dynamic level options
    levels = ["A1", "B2", "C1"]
    # Don't allow A1 to change level here
    exam_level = user_level

    # Teil options by level
    if exam_level == "A1":
        teil_options = [
            "Teil 1 – Persönliche Fragen",
            "Teil 2 – Fragen und Antworten zu Alltagsthemen",
            "Teil 3 – Bitten formulieren"
        ]
    elif exam_level == "B2":
        teil_options = [
            "Teil 1 – Diskussion eines Themas",
            "Teil 2 – Präsentation",
            "Teil 3 – Argumentation/Diskussion"
        ]
    else:  # C1
        teil_options = [
            "Teil 1 – Textanalyse",
            "Teil 2 – Präsentation",
            "Teil 3 – Diskussion/Reflexion"
        ]

    teil = st.selectbox(
        "Welchen Teil möchtest du üben?",
        teil_options,
        key="exam_teil_select"
    )
    st.session_state["selected_teil"] = teil
    st.session_state["selected_exam_level"] = exam_level

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage4_back"):
            st.session_state["step"] = 3
    with col2:
        if st.button("Start Chat ➡️", key="stage4_start"):
            # Pick a random prompt for the chosen teil and level, and let AI start
            if exam_level == "A1":
                if teil.startswith("Teil 1"):
                    prompt = (
                        "Bitte beantworten Sie folgende Fragen zu sich: " +
                        ", ".join(A1_TEIL1_KEYWORDS) +
                        ".\n" + random.choice(A1_TEIL1_FOLLOWUP)
                    )
                elif teil.startswith("Teil 2"):
                    vocab = random.choice(A1_VOCAB_TEIL2)
                    prompt = f"Stellen Sie eine Frage und antworten Sie zum Thema: {vocab[0]} – {vocab[1]}."
                else:
                    prompt = f"Formulieren Sie eine höfliche Bitte: {random.choice(A1_BITTEN_PROMPTS)}."
            elif exam_level == "B2":
                if teil.startswith("Teil 1"):
                    prompt = f"Diskutieren Sie das Thema: {random.choice(B2_TEIL1_THEMEN)}."
                elif teil.startswith("Teil 2"):
                    prompt = random.choice(B2_TEIL2_PRESENTATION)
                else:
                    prompt = random.choice(B2_TEIL3_ARGUMENTATION)
            else:  # C1
                if teil.startswith("Teil 1"):
                    prompt = f"Analysieren Sie das Thema: {random.choice(C1_TEIL1_THEMEN)}."
                elif teil.startswith("Teil 2"):
                    prompt = random.choice(C1_TEIL2_PRESENTATION)
                else:
                    prompt = random.choice(C1_TEIL3_DISKUSSION)
            # --- AI starts chat! ---
            st.session_state["messages"] = [{"role": "assistant", "content": prompt}]
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            st.session_state["step"] = 5
# ===============================
#         STAGE 5: Live Chat, Correction, and Styled UI
# ===============================

def stage_5_chat():
    if st.session_state.get("step") != 5:
        return

    today_str = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key = f"{student_code}_{today_str}"
    st.session_state.setdefault("daily_usage", {})
    st.session_state["daily_usage"].setdefault(usage_key, 0)

    st.markdown(
        f"<div style='margin-bottom:0.5em'>"
        f"<span style='background:#bee3f8;border-radius:0.5em;padding:0.3em 0.8em;'>"
        f"Student code: <b>{student_code}</b> &nbsp; | &nbsp; Today's practice: {st.session_state['daily_usage'][usage_key]}/{DAILY_LIMIT}"
        f"</span></div>",
        unsafe_allow_html=True
    )

    # Render chat bubbles
    def show_formatted_ai_reply(ai_reply):
        lines = [l.strip() for l in ai_reply.split('\n') if l.strip()]
        answer, correction, explanation, followup = '', '', '', ''
        curr = 'answer'
        for line in lines:
            header = line.lower()
            if 'correction:' in header:
                curr = 'correction'
                line = line.split(':', 1)[-1].strip()
            elif 'grammar tip:' in header or 'explanation:' in header or 'tip:' in header:
                curr = 'explanation'
                line = line.split(':', 1)[-1].strip()
            elif 'next question:' in header or 'follow-up' in header:
                curr = 'followup'
                line = line.split(':', 1)[-1].strip()
            if curr == 'answer':
                answer += line + ' '
            elif curr == 'correction':
                correction += line + ' '
            elif curr == 'explanation':
                explanation += line + ' '
            elif curr == 'followup':
                followup += line + ' '

        if answer.strip():
            st.markdown(f"<div style='font-size:1.05em;line-height:1.6'><b>Answer:</b><br>{answer.strip()}</div>", unsafe_allow_html=True)
        if correction.strip():
            st.markdown(f"<div style='color:#ea574b'><b>Correction (English):</b><br>{correction.strip()}</div>", unsafe_allow_html=True)
        if explanation.strip():
            st.markdown(f"<div style='color:#375be3'><b>Explanation (English):</b><br>{explanation.strip()}</div>", unsafe_allow_html=True)
        if followup.strip():
            st.markdown(f"<div style='color:#32a852'><b>Next Question:</b><br>{followup.strip()}</div>", unsafe_allow_html=True)

    def render_chat():
        for msg in st.session_state["messages"]:
            if msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🧑‍🏫"):
                    st.markdown("""
                    <div style='display:flex;flex-direction:row-reverse;align-items:flex-end;'>
                      <div style='background:linear-gradient(90deg,#bee3f8,#98f5e1);color:#174562;padding:1em 1.2em;margin:6px 0 6px 64px;border-radius:1.1em 1.1em 0.1em 1.1em;max-width:65vw;min-width:110px;box-shadow:0 1px 6px #d9ecfa;'>
                        <b>Sir Felix</b><br>
                        """, unsafe_allow_html=True)
                    show_formatted_ai_reply(msg["content"])
                    st.markdown("</div></div>", unsafe_allow_html=True)
            else:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown("""
                    <div style='display:flex;flex-direction:row;align-items:flex-end;'>
                      <div style='background:#f1f1f1;color:#181818;padding:1em 1.2em;margin:6px 64px 6px 0;border-radius:1.1em 1.1em 1.1em 0.1em;max-width:65vw;min-width:110px;box-shadow:0 1px 4px #e5e5e5;'>
                        <b>Student</b><br>
                    """, unsafe_allow_html=True)
                    st.markdown(msg["content"])
                    st.markdown("</div></div>", unsafe_allow_html=True)

    render_chat()

    # Input form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Type your reply or exam answer here...", height=70)
        submitted = st.form_submit_button("Send")

    session_ended = st.session_state["turn_count"] >= MAX_TURNS
    used_today = st.session_state["daily_usage"][usage_key]

    # AI reply logic
    if submitted and user_input and not session_ended:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["turn_count"] += 1
        st.session_state["daily_usage"][usage_key] += 1

        with st.spinner("Sir Felix is typing..."):
            exam_level = st.session_state["selected_exam_level"]
            # SYSTEM PROMPT
            if exam_level == "A1":
                system_prompt = (
                    "You are Sir Felix, a strict but friendly A1 examiner. "
                    "ALWAYS give corrections and grammar explanations in ENGLISH. "
                    "Reply in very simple German (A1), maximum 2–3 sentences. "
                    "Show the correction and a grammar tip in ENGLISH, then end with a next question or prompt in German."
                )
            elif exam_level == "B2":
                system_prompt = (
                    "You are Sir Felix, a strict but supportive Goethe B2 examiner. "
                    "ALWAYS give corrections and grammar explanations in ENGLISH. "
                    "Respond in fluent, advanced German (B2 level). "
                    "Correct mistakes and explain them in ENGLISH. "
                    "Guide the student to present arguments, analyze, and discuss as required for the B2 exam."
                )
            else:  # C1
                system_prompt = (
                    "You are Sir Felix, a C1-level examiner. "
                    "Always respond in advanced, academic German (C1 level), but always correct and explain in ENGLISH. "
                    "Encourage critical thinking, interpretation, and sophisticated language use as in the C1 exam."
                )
            conversation = [
                {"role": "system", "content": system_prompt},
                st.session_state["messages"][-1]
            ]
            try:
                client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation
                )
                ai_reply = resp.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response."
                st.error(str(e))
            st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
            st.experimental_rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage5_back"):
            st.session_state["reset_stage5"] = True
            st.session_state["step"] = 4
            st.experimental_rerun()
    with col2:
        if session_ended and st.button("Next ➡️ (Summary)", key="stage5_summary"):
            st.session_state["step"] = 6

# ===============================
#         STAGE 6: Session Summary & Restart
# ===============================

def stage_6_summary():
    if st.session_state.get("step") != 6:
        return
    st.title("🎉 Congratulations!")
    st.markdown(
        "<h3 style='color:#33691e;'>Session completed!</h3>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"**You completed {st.session_state['turn_count']} turns.**<br>"
        "Start again or choose another mode?",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Start New Session", key="stage6_restart"):
            st.session_state["step"] = 1
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            st.session_state["custom_topic"] = ""
    with col2:
        if st.button("⬅️ Back to Mode Selection", key="stage6_back"):
            st.session_state["step"] = 3
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []

# ===============================
#         STAGE 7: Presentation Practice Module (B2/C1)
# ===============================

def stage_7_presentation():
    if st.session_state.get("step") != 7:
        return

    user_level = st.session_state.get("user_level", "B2")
    # Only B2 and C1 can use this stage
    if user_level not in ["B2", "C1"]:
        st.warning("Presentation Practice is only available for B2 and C1.")
        if st.button("⬅️ Back", key="stage7_back"):
            st.session_state["step"] = 3
        return

    if "presentation_stage" not in st.session_state:
        st.session_state["presentation_stage"] = 0
        st.session_state["presentation_topic"] = ""
        st.session_state["presentation_messages"] = []
        st.session_state["presentation_turn_count"] = 0

    # Stage 0: Choose Teil
    if st.session_state["presentation_stage"] == 0:
        if user_level == "B2":
            teil_options = [
                "Teil 1 – Diskussion eines Themas",
                "Teil 2 – Präsentation",
                "Teil 3 – Argumentation/Diskussion"
            ]
        else:
            teil_options = [
                "Teil 1 – Textanalyse",
                "Teil 2 – Präsentation",
                "Teil 3 – Diskussion/Reflexion"
            ]
        teil = st.selectbox("Wähle den Präsentationsteil", teil_options)
        if st.button("Weiter zur Themenauswahl"):
            st.session_state["presentation_teil"] = teil
            st.session_state["presentation_stage"] = 1
            st.session_state["presentation_messages"] = []
            st.session_state["presentation_turn_count"] = 0
            st.experimental_rerun()
        return

    # Stage 1: Choose/enter topic
    if st.session_state["presentation_stage"] == 1:
        if user_level == "B2":
            if st.session_state["presentation_teil"].startswith("Teil 1"):
                topics = B2_TEIL1_THEMEN
            elif st.session_state["presentation_teil"].startswith("Teil 2"):
                topics = B2_TEIL2_PRESENTATION
            else:
                topics = B2_TEIL3_ARGUMENTATION
        else:  # C1
            if st.session_state["presentation_teil"].startswith("Teil 1"):
                topics = C1_TEIL1_THEMEN
            elif st.session_state["presentation_teil"].startswith("Teil 2"):
                topics = C1_TEIL2_PRESENTATION
            else:
                topics = C1_TEIL3_DISKUSSION

        random_topic = random.choice(topics)
        topic = st.text_input(
            "Präsentationsthema auswählen oder eigenes Thema eingeben:",
            value=random_topic
        )
        if st.button("Start Präsentations-Chat"):
            st.session_state["presentation_topic"] = topic
            # Let AI start!
            st.session_state["presentation_messages"] = [
                {"role": "assistant", "content": f"Bitte halte eine kurze Präsentation oder beginne mit dem Thema:\n\n<b>{topic}</b>"}
            ]
            st.session_state["presentation_stage"] = 2
            st.experimental_rerun()
        return

    # Stage 2: Chat Loop
    if st.session_state["presentation_stage"] == 2:
        # Chat bubbles
        for msg in st.session_state["presentation_messages"]:
            if msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🧑‍🏫"):
                    st.markdown(f"<div style='background:linear-gradient(90deg,#bee3f8,#98f5e1);color:#174562;padding:1em 1.2em;border-radius:1.1em;max-width:65vw;min-width:110px;'><b>Sir Felix</b><br>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(f"<div style='background:#f1f1f1;color:#181818;padding:1em 1.2em;border-radius:1.1em;max-width:65vw;min-width:110px;'><b>Student</b><br>{msg['content']}</div>", unsafe_allow_html=True)

        # Input
        user_input = st.chat_input("Schreibe deinen Präsentationsteil oder deine Antwort...")
        if user_input:
            st.session_state["presentation_messages"].append({"role": "user", "content": user_input})
            st.session_state["presentation_turn_count"] += 1

            # AI SYSTEM PROMPT
            system_prompt = (
                f"You are Sir Felix, a {'B2' if user_level == 'B2' else 'C1'} presentation examiner. "
                f"ALWAYS correct and explain in ENGLISH. "
                f"Respond in exam-appropriate German. "
                f"Encourage argumentation, critical thinking, and structure, but always give corrections/explanations in ENGLISH."
            )
            conversation = [
                {"role": "system", "content": system_prompt},
                st.session_state["presentation_messages"][-1]
            ]
            with st.spinner("Sir Felix is typing..."):
                try:
                    client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                    resp = client.chat.completions.create(
                        model="gpt-4o",
                        messages=conversation
                    )
                    ai_reply = resp.choices[0].message.content
                except Exception as e:
                    ai_reply = "Sorry, there was a problem generating a response."
                    st.error(str(e))
                st.session_state["presentation_messages"].append({"role": "assistant", "content": ai_reply})
                st.experimental_rerun()

        st.markdown(f"**Takes completed:** {st.session_state['presentation_turn_count']}/12")
        if st.session_state["presentation_turn_count"] >= 12:
            st.success("Presentation practice complete!")
            if st.button("🔁 Neue Präsentation beginnen"):
                for k in ["presentation_stage", "presentation_topic", "presentation_messages", "presentation_turn_count"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.experimental_rerun()
        if st.button("⬅️ Zurück zum Modus-Menü", key="stage7_back_to_menu"):
            for k in ["presentation_stage", "presentation_topic", "presentation_messages", "presentation_turn_count"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state["step"] = 3
            st.experimental_rerun()
# ===============================
#         MAIN APP RUNNER
# ===============================

# Setup page, state, and header
setup_ui_and_state()

# Show stages according to step
stage_3_login_and_mode()
stage_4_exam_part()
stage_5_chat()
stage_6_summary()
stage_7_presentation()
