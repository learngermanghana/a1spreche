import streamlit as st
import openai
import random
import pandas as pd
import tempfile

# ========== SCHOOL INFO & LOGIN ==========
SCHOOL_NAME = "Learn Language Education Academy"
BASE_URL = "https://api.whatsapp.com/message/EYMY3524WL6IC1?autoload=1&app_absent=0"
VOCAROO_URL = "https://vocaroo.com/1bW5U4NUiwmk"

def load_valid_codes():
    try:
        return pd.read_csv("student_codes.csv")["code"].tolist()
    except Exception:
        return []

def login_main():
    if 'student_code' not in st.session_state:
        code = st.text_input("Student Code:", type="password")
        if code:
            valid = load_valid_codes()
            if code in valid:
                st.session_state['student_code'] = code
            else:
                st.error("Invalid code. Please contact your teacher.")
                st.stop()
        else:
            st.info("Enter your student code to begin.")
            st.stop()
    return st.session_state['student_code']

openai.api_key = st.secrets["OPENAI_API_KEY"]

# ========== WHISPER TRANSCRIPTION ==========
def transcribe_audio(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
        tmpfile.write(file.read())
        tmpfile.flush()
        audio_file = open(tmpfile.name, "rb")
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
            language="de"
        )
        return transcript

def show_audio_upload_and_transcribe(key="audio"):
    st.markdown("**Or upload your answer as audio (mp3, wav, m4a):**")
    audio_file = st.file_uploader("Upload your recording", type=["mp3", "wav", "m4a"], key=key)
    transcript = ""
    if audio_file is not None:
        st.audio(audio_file)
        with st.spinner("Transcribing..."):
            try:
                transcript = transcribe_audio(audio_file)
                st.success("Transcription:")
                st.markdown(f"> {transcript}")
            except Exception as e:
                st.error(f"Transcription failed: {e}")
    return transcript

# ========== AI FEEDBACK FUNCTIONS ==========
def get_ai_intro_feedback(intro_text):
    prompt = f"""
You are a Goethe A1 examiner. The student just gave this introduction in German:
---
{intro_text}
---
1. Give feedback in **simple English** (not German), pointing out A1-level mistakes, missing points, and praise correct sentences.
2. Give a score out of 5 points (all 7 points = 5/5, deduct 1 for each missing/weak part).
3. Show a sample correct introduction in German.
Feedback first, then Score, then Example.
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )
    return response.choices[0].message.content.strip()

def get_ai_followup_feedback(q, a):
    prompt = f"""
You are a Goethe A1 examiner. The student answered this question:
Q: {q}
A: {a}
1. Give simple English feedback about correctness and A1-level mistakes. Correct and praise where possible.
2. Show a sample correct answer in German.
Feedback first, then Example.
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

def get_ai_teil2_feedback(topic, keyword, student_message):
    prompt = f"""
You are an A1 Goethe oral examiner. The student was told:
Topic: {topic}
Keyword: {keyword}
Student's message: {student_message}
1. Give feedback and correction in simple English (not German). Point out errors, praise good parts, and show a correct model answer in German.
2. Give 'Correct' or 'Incorrect' and 1/1 or 0/1 for this question.
Feedback first, then Score, then Example.
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=350
    )
    return response.choices[0].message.content.strip()

def get_ai_teil3_feedback(prompt_topic, student_message):
    prompt = f"""
You are a Goethe A1 examiner. The student had to write a polite request (e.g. 'Können Sie bitte ...?') and a suitable reply, both in German in one message:
Task: {prompt_topic}
Student's message: {student_message}
1. Give feedback in simple English and point out any mistakes.
2. Show a model correct answer in German.
Feedback first, then Example.
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=350
    )
    return response.choices[0].message.content.strip()

# ========== TEIL 1: CHAT ==========

TEIL1_KEYWORDS = ["Name", "Alter", "Land", "Wohnort", "Sprachen", "Beruf", "Hobby"]
TEIL1_FOLLOWUP = [
    "Wie buchstabieren Sie Ihren Namen?",
    "Sind Sie verheiratet? (Ja/Nein)",
    "Wie alt ist Ihre Mutter?",
    "Haben Sie Geschwister?",
    "Welche Sprachen sprechen Sie?",
    "Was machen Sie gern in Ihrer Freizeit?"
]

def examiner_intro(name):
    return (
        f"Welcome, {name}! I am your examiner for the Goethe A1 speaking exam.\n\n"
        "First, please introduce yourself in German in **one message**, using these points:\n"
        "- Name\n- Alter\n- Land\n- Wohnort\n- Sprachen\n- Beruf\n- Hobby\n\n"
        "When you finish, I'll give you feedback and ask you 3 more questions."
    )

def teil1_chat():
    st.header("Teil 1: Self-Introduction (Exam Simulation)")
    if "teil1_chat" not in st.session_state:
        st.session_state.teil1_chat = []
        st.session_state.teil1_name = ""
        st.session_state.teil1_intro_done = False
        st.session_state.teil1_qidx = 0
        st.session_state.teil1_score = None
        st.session_state.teil1_followups = random.sample(TEIL1_FOLLOWUP, 3)

    # Student enters name first
    if not st.session_state.teil1_name:
        name = st.text_input("Enter your name for the examiner to greet you:")
        if name:
            st.session_state.teil1_name = name
            st.session_state.teil1_chat.append({"role": "examiner", "content": examiner_intro(name)})
            st.rerun()
        return

    for msg in st.session_state.teil1_chat:
        st.chat_message("assistant" if msg["role"] == "examiner" else "user").write(msg["content"])

    # Step 1: Self-intro
    if not st.session_state.teil1_intro_done:
        student_input = st.chat_input("Type your German introduction (all in one message):")
        transcript = show_audio_upload_and_transcribe(key="teil1_audio")
        reply = student_input or transcript
        if reply:
            st.session_state.teil1_chat.append({"role": "student", "content": reply})
            feedback = get_ai_intro_feedback(reply)
            st.session_state.teil1_chat.append({"role": "examiner", "content": feedback})
            st.session_state.teil1_intro_done = True
            st.rerun()
        return

    # Step 2: Follow-up
    if st.session_state.teil1_qidx < 3:
        q = st.session_state.teil1_followups[st.session_state.teil1_qidx]
        st.session_state.teil1_chat.append({"role": "examiner", "content": f"Frage {st.session_state.teil1_qidx+1}: {q}"})
        student_input = st.chat_input("Antwort auf Deutsch:")
        transcript = show_audio_upload_and_transcribe(key=f"teil1q{st.session_state.teil1_qidx}_audio")
        reply = student_input or transcript
        if reply:
            st.session_state.teil1_chat.append({"role": "student", "content": reply})
            feedback = get_ai_followup_feedback(q, reply)
            st.session_state.teil1_chat.append({"role": "examiner", "content": feedback})
            st.session_state.teil1_qidx += 1
            st.rerun()
        return

    # Step 3: Closing
    if st.session_state.teil1_score is None:
        st.session_state.teil1_score = "Examiner: Your Teil 1 practice is complete! Review your feedback above. Try again for a better score next time."
        st.session_state.teil1_chat.append({"role": "examiner", "content": st.session_state.teil1_score})
    st.chat_input("Teil 1 complete. Restart to try again.", disabled=True)

# ========== TEIL 2 CHAT ==========

VOCAB_TEIL2 = [
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

def get_next_vocab(used, n=1):
    available = [pair for pair in VOCAB_TEIL2 if pair not in used]
    return random.sample(available, min(len(available), n)) if available else []

def examiner_teil2_intro(name, n_rounds):
    return (
        f"Welcome, {name}! This is Teil 2 of the A1 oral exam (Questions & Answers).\n"
        "I will give you a topic and a keyword. Please write a question about them in German (ending with '?') and answer it (ending with '.') in the same message.\n"
        f"We will do {n_rounds} questions. Let’s start!"
    )

def teil2_chat():
    st.header("Teil 2: Questions & Answers (Exam Simulation)")
    if "teil2_chat" not in st.session_state:
        st.session_state.teil2_chat = []
        st.session_state.teil2_name = ""
        st.session_state.teil2_rounds_total = None
        st.session_state.teil2_rounds_done = 0
        st.session_state.teil2_vocabs_used = []
        st.session_state.teil2_current_vocab = None

    # Student name
    if not st.session_state.teil2_name:
        name = st.text_input("Enter your name for the examiner to greet you:", key="teil2name")
        if name:
            st.session_state.teil2_name = name
            st.session_state.teil2_chat.append({"role": "examiner", "content": f"Welcome, {name}! How many questions do you want to practice for Teil 2? (1-5)"})
            st.rerun()
        return

    for msg in st.session_state.teil2_chat:
        st.chat_message("assistant" if msg["role"] == "examiner" else "user").write(msg["content"])

    # Get how many rounds
    if st.session_state.teil2_rounds_total is None:
        user_input = st.chat_input("How many questions? (1-5):")
        if user_input:
            try:
                n = int(user_input.strip())
                if 1 <= n <= 5:
                    st.session_state.teil2_rounds_total = n
                    st.session_state.teil2_rounds_done = 0
                    st.session_state.teil2_chat.append({"role": "student", "content": user_input})
                    st.session_state.teil2_chat.append({"role": "examiner", "content": examiner_teil2_intro(st.session_state.teil2_name, n)})
                    vocab = get_next_vocab(st.session_state.teil2_vocabs_used)
                    st.session_state.teil2_current_vocab = vocab[0]
                    st.session_state.teil2_vocabs_used.append(vocab[0])
                    st.rerun()
                else:
                    st.session_state.teil2_chat.append({"role": "examiner", "content": "Please enter a number between 1 and 5."})
                    st.rerun()
            except ValueError:
                st.session_state.teil2_chat.append({"role": "examiner", "content": "Please enter a valid number (1-5)."})
                st.rerun()
        return

    # Each question round
    if st.session_state.teil2_rounds_done < st.session_state.teil2_rounds_total:
        t, k = st.session_state.teil2_current_vocab
        st.session_state.teil2_chat.append({"role": "examiner", "content": f"Topic: {t}\nKeyword: {k}\nWrite your question (ends with '?') and answer (ends with '.') in one German message."})
        student_input = st.chat_input("Type your German question + answer here:")
        transcript = show_audio_upload_and_transcribe(key=f"teil2q{st.session_state.teil2_rounds_done}_audio")
        reply = student_input or transcript
        if reply:
            st.session_state.teil2_chat.append({"role": "student", "content": reply})
            feedback = get_ai_teil2_feedback(t, k, reply)
            st.session_state.teil2_chat.append({"role": "examiner", "content": feedback})
            st.session_state.teil2_rounds_done += 1
            if st.session_state.teil2_rounds_done < st.session_state.teil2_rounds_total:
                vocab = get_next_vocab(st.session_state.teil2_vocabs_used)
                if vocab:
                    st.session_state.teil2_current_vocab = vocab[0]
                    st.session_state.teil2_vocabs_used.append(vocab[0])
            else:
                st.session_state.teil2_chat.append({"role": "examiner", "content": "Examiner: Teil 2 finished! Review your feedback. Try again for more practice!"})
            st.rerun()
        return

    st.chat_input("Teil 2 complete. Restart to try again.", disabled=True)

# ========== TEIL 3 CHAT ==========

BITTEN_PROMPTS = [
    "Radio anmachen", "Fenster zumachen", "Licht anschalten", "Tür aufmachen",
    "Tisch sauber machen", "Hausaufgaben schicken", "Buch bringen",
    "Handy ausmachen", "Stuhl nehmen", "Wasser holen", "Fenster öffnen",
    "Musik leiser machen", "Tafel sauber wischen", "Kaffee kochen",
    "Deutsch üben", "Auto waschen", "Kind abholen", "Tisch decken",
    "Termin machen", "Nachricht schreiben",
]

def get_next_bitten(used, n=1):
    available = [b for b in BITTEN_PROMPTS if b not in used]
    return random.sample(available, min(len(available), n)) if available else []

def examiner_teil3_intro(name, n_rounds):
    return (
        f"Welcome, {name}! This is Teil 3 of the A1 oral exam (Requests & Replies).\n"
        "I will give you a task. Please write a polite request in German (ending with '?') and a suitable reply (ending with '.') in the same message.\n"
        f"We will do {n_rounds} requests. Let’s start!"
    )

def teil3_chat():
    st.header("Teil 3: Requests & Replies (Exam Simulation)")
    if "teil3_chat" not in st.session_state:
        st.session_state.teil3_chat = []
        st.session_state.teil3_name = ""
        st.session_state.teil3_rounds_total = None
        st.session_state.teil3_rounds_done = 0
        st.session_state.teil3_prompts_used = []
        st.session_state.teil3_current_prompt = None

    # Student name
    if not st.session_state.teil3_name:
        name = st.text_input("Enter your name for the examiner to greet you:", key="teil3name")
        if name:
            st.session_state.teil3_name = name
            st.session_state.teil3_chat.append({"role": "examiner", "content": f"Welcome, {name}! How many requests do you want to practice for Teil 3? (1-5)"})
            st.rerun()
        return

    for msg in st.session_state.teil3_chat:
        st.chat_message("assistant" if msg["role"] == "examiner" else "user").write(msg["content"])

    # Get how many rounds
    if st.session_state.teil3_rounds_total is None:
        user_input = st.chat_input("How many requests? (1-5):")
        if user_input:
            try:
                n = int(user_input.strip())
                if 1 <= n <= 5:
                    st.session_state.teil3_rounds_total = n
                    st.session_state.teil3_rounds_done = 0
                    st.session_state.teil3_chat.append({"role": "student", "content": user_input})
                    st.session_state.teil3_chat.append({"role": "examiner", "content": examiner_teil3_intro(st.session_state.teil3_name, n)})
                    prompt = get_next_bitten(st.session_state.teil3_prompts_used)
                    st.session_state.teil3_current_prompt = prompt[0]
                    st.session_state.teil3_prompts_used.append(prompt[0])
                    st.rerun()
                else:
                    st.session_state.teil3_chat.append({"role": "examiner", "content": "Please enter a number between 1 and 5."})
                    st.rerun()
            except ValueError:
                st.session_state.teil3_chat.append({"role": "examiner", "content": "Please enter a valid number (1-5)."})
                st.rerun()
        return

    # Each round
    if st.session_state.teil3_rounds_done < st.session_state.teil3_rounds_total:
        prompt = st.session_state.teil3_current_prompt
        st.session_state.teil3_chat.append({"role": "examiner", "content": f"Task: {prompt}\nWrite a polite request (ends with '?') and reply (ends with '.') in German, both in one message."})
        student_input = st.chat_input("Type your German request + reply here:")
        transcript = show_audio_upload_and_transcribe(key=f"teil3q{st.session_state.teil3_rounds_done}_audio")
        reply = student_input or transcript
        if reply:
            st.session_state.teil3_chat.append({"role": "student", "content": reply})
            feedback = get_ai_teil3_feedback(prompt, reply)
            st.session_state.teil3_chat.append({"role": "examiner", "content": feedback})
            st.session_state.teil3_rounds_done += 1
            if st.session_state.teil3_rounds_done < st.session_state.teil3_rounds_total:
                newprompt = get_next_bitten(st.session_state.teil3_prompts_used)
                if newprompt:
                    st.session_state.teil3_current_prompt = newprompt[0]
                    st.session_state.teil3_prompts_used.append(newprompt[0])
            else:
                st.session_state.teil3_chat.append({"role": "examiner", "content": "Examiner: Teil 3 finished! Review your feedback. Try again for more practice!"})
            st.rerun()
        return

    st.chat_input("Teil 3 complete. Restart to try again.", disabled=True)

# ========== MAIN APP ==========
st.set_page_config(page_title=f"A1 Sprechen – {SCHOOL_NAME}", layout="wide")
st.title(f"A1 Sprechen – {SCHOOL_NAME}")

st.markdown(f"""
**School:** {SCHOOL_NAME}  
[Record your voice here (Vocaroo)]({VOCAROO_URL})  
[Send result to teacher (WhatsApp)]({BASE_URL})
""")

_ = login_main()

tab = st.radio("Choose a part:", ["Teil 1: Self-introduction", "Teil 2: Questions & Answers (Chat)", "Teil 3: Requests & Replies (Chat)"])

if tab.startswith("Teil 1"):
    teil1_chat()
elif tab.startswith("Teil 2"):
    teil2_chat()
elif tab.startswith("Teil 3"):
    teil3_chat()
