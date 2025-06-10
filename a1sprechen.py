import streamlit as st
import openai
import pandas as pd
import random
import tempfile
from fpdf import FPDF

# ====== SCHOOL INFO ======
SCHOOL_NAME = "Learn Language Education Academy"
BASE_URL = "https://api.whatsapp.com/message/EYMY3524WL6IC1?autoload=1&app_absent=0"
VOCAROO_URL = "https://vocaroo.com/1bW5U4NUiwmk"

# ====== LOGIN ======
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

# ====== OPENAI SETUP ======
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ====== VOCABULARY ======
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
BITTEN_PROMPTS = [
    "Radio anmachen", "Fenster zumachen", "Licht anschalten", "Tür aufmachen",
    "Tisch sauber machen", "Hausaufgaben schicken", "Buch bringen",
    "Handy ausmachen", "Stuhl nehmen", "Wasser holen", "Fenster öffnen",
    "Musik leiser machen", "Tafel sauber wischen", "Kaffee kochen",
    "Deutsch üben", "Auto waschen", "Kind abholen", "Tisch decken",
    "Termin machen", "Nachricht schreiben",
]

# ====== WHISPER TRANSCRIPTION ======
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

def show_audio_upload_and_transcribe():
    st.markdown("**Or upload your answer as audio (mp3, wav, m4a):**")
    audio_file = st.file_uploader("Upload your recording", type=["mp3", "wav", "m4a"], key=random.randint(0, 1000000))
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

# ====== AI FEEDBACK FUNCTIONS (ENGLISH FEEDBACK) ======
def get_openai_feedback_teil1(inputs, spoken_text=None):
    # If spoken_text is provided, analyze only that
    if spoken_text:
        intro_text = spoken_text
        intro_type = "spoken"
    else:
        intro_text = (
            f"Name: {inputs['name']}\n"
            f"Age: {inputs['age']}\n"
            f"Country: {inputs['country']}\n"
            f"Residence: {inputs['residence']}\n"
            f"Languages: {inputs['languages']}\n"
            f"Profession: {inputs['profession']}\n"
            f"Hobby: {inputs['hobby']}"
        )
        intro_type = "written"

    prompt = f"""
You are a German teacher for A1 beginners. Check this student's {intro_type} self-introduction. Look for:
- Each answer is a simple, complete sentence.
- Word order, capitalization, and punctuation are correct.
- Use only A1 German words and grammar.

Return corrections and short feedback for each point IN ENGLISH. If there are mistakes, explain briefly in English, with a corrected example.

Student introduction:
{intro_text}
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )
    return response.choices[0].message.content.strip()

def get_openai_feedback_teil2(thema, stichwort, answer):
    prompt = f"""
You are a German teacher for A1 beginners. Check the student's question and answer for the topic and keyword. Look for:
- Does the question start with a question word or a verb? Does it end with "?"?
- Is the answer a simple, complete sentence? Does it end with "."?
- Are capitalization and punctuation correct?

Give a short correction and feedback for both (question and answer) IN ENGLISH. If there are mistakes, explain briefly and show a corrected example.

ALSO, provide one good example question and answer in German for this topic and keyword, at the end, with the label 'Example:'.

Topic: {thema}
Keyword: {stichwort}
Student's message: {answer}
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700
    )
    return response.choices[0].message.content.strip()

def get_openai_feedback_teil3(prompt_topic, answer):
    prompt = f"""
You are a German teacher for A1 beginners. The student must write a polite request (e.g. 'Können Sie bitte ...?') and a suitable reply, both in one message. Check:
- Is the request polite, does it end with '?'?
- Is the reply a simple, complete sentence and does it end with '.'?
- Are capitalization and punctuation correct?

Give correction/feedback IN ENGLISH. Show a corrected example if needed.

ALSO, provide one good example request and reply in German for this task, at the end, with the label 'Example:'.

Task: {prompt_topic}
Student's message: {answer}
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700
    )
    return response.choices[0].message.content.strip()

# ====== TEIL 1 ======
def teil1():
    st.subheader("Teil 1: Self-introduction")
    st.info("Introduce yourself in German, using simple full sentences. Then, try to record and upload your spoken introduction for extra feedback.")
    inputs = {}
    inputs['name'] = st.text_input("Name (sentence):", placeholder="Ich heiße ...")
    inputs['age'] = st.text_input("Age (sentence):", placeholder="Ich bin ... Jahre alt.")
    inputs['country'] = st.text_input("Country (sentence):", placeholder="Ich komme aus ...")
    inputs['residence'] = st.text_input("Residence (sentence):", placeholder="Ich wohne in ...")
    inputs['languages'] = st.text_input("Languages (sentence):", placeholder="Ich spreche ...")
    inputs['profession'] = st.text_input("Profession (sentence):", placeholder="Ich bin ... von Beruf.")
    inputs['hobby'] = st.text_input("Hobby (sentence):", placeholder="Mein Hobby ist ...")

    # Written feedback
    if st.button("Check Written Introduction"):
        with st.spinner("Checking..."):
            feedback = get_openai_feedback_teil1(inputs)
            st.success("Feedback (written):")
            st.markdown(feedback)
            st.session_state['teil1_feedback_written'] = feedback

    if 'teil1_feedback_written' in st.session_state:
        st.markdown("---")
        st.markdown("**Last Written Feedback:**")
        st.markdown(st.session_state['teil1_feedback_written'])

    # Audio feedback
    st.markdown("---")
    st.markdown("### Optional: Record/Upload your spoken introduction for feedback")
    transcript = show_audio_upload_and_transcribe()
    if transcript:
        if st.button("Check Spoken Introduction"):
            with st.spinner("Checking..."):
                feedback = get_openai_feedback_teil1(inputs, spoken_text=transcript)
                st.success("Feedback (spoken):")
                st.markdown(feedback)
                st.session_state['teil1_feedback_spoken'] = feedback
    if 'teil1_feedback_spoken' in st.session_state:
        st.markdown("**Last Spoken Feedback:**")
        st.markdown(st.session_state['teil1_feedback_spoken'])

# ====== TEIL 2 CHAT MODE ======
def get_next_vocab(used, n=1):
    available = [pair for pair in VOCAB_TEIL2 if pair not in used]
    return random.sample(available, min(len(available), n)) if available else []

def teil2_chat():
    st.header("Teil 2 – Fragen & Antworten (Chat Mode)")
    st.markdown("Practice exam-style 'Question & Answer' with your AI German oral trainer. You may type or upload audio for each prompt.")

    if "t2_chat_history" not in st.session_state:
        st.session_state.t2_chat_history = []
        st.session_state.t2_vocabs_used = []
        st.session_state.t2_rounds_total = None
        st.session_state.t2_rounds_done = 0
        st.session_state.t2_waiting_for_count = True
        st.session_state.t2_current_vocab = None
        st.session_state.t2_chat_history.append({
            "role": "assistant",
            "content": (
                "Welcome to Teil 2: Fragen & Antworten!\n\n"
                "In this part, you will practice making questions and answers in German, just like in the real exam. "
                "Here’s how it works:\n"
                "- You will receive a Topic and a Keyword (e.g., Thema: Uhr, Stichwort: Uhrzeit).\n"
                "- Write a question about them in German (ending with ?) and then a suitable answer (ending with .), both in **one message**.\n"
                "You will get instant correction and tips after each answer.\n\n"
                "How many questions do you want to practice today? (Enter a number from 1 to 5)"
            )
        })

    for msg in st.session_state.t2_chat_history:
        align = "user" if msg["role"] == "user" else "assistant"
        st.chat_message(align).write(msg["content"])

    if st.session_state.t2_waiting_for_count:
        user_input = st.chat_input("Enter a number (1-5):")
        if user_input:
            try:
                n = int(user_input.strip())
                if 1 <= n <= 5:
                    st.session_state.t2_rounds_total = n
                    st.session_state.t2_rounds_done = 0
                    st.session_state.t2_chat_history.append({"role": "user", "content": user_input})
                    vocab = get_next_vocab(st.session_state.t2_vocabs_used)
                    st.session_state.t2_current_vocab = vocab[0]
                    st.session_state.t2_vocabs_used.append(vocab[0])
                    st.session_state.t2_waiting_for_count = False
                    t, k = vocab[0]
                    ai_msg = (
                        f"Great! Here is your first prompt:\n\n"
                        f"**Topic:** {t}\n**Keyword:** {k}\n\n"
                        "Write a question in German about these (ending with '?') and then answer it in German (ending with '.'), both in one message. Or upload an audio answer below."
                    )
                    st.session_state.t2_chat_history.append({"role": "assistant", "content": ai_msg})
                    st.rerun()
                else:
                    st.session_state.t2_chat_history.append({
                        "role": "assistant",
                        "content": "Please enter a number between 1 and 5."
                    })
                    st.rerun()
            except ValueError:
                st.session_state.t2_chat_history.append({
                    "role": "assistant",
                    "content": "Please enter a valid number (1-5)."
                })
                st.rerun()
        return

    if st.session_state.t2_rounds_done < st.session_state.t2_rounds_total:
        # Typed answer
        user_input = st.chat_input("Type your question and answer (both in German, one message):")
        # Audio answer
        transcript = show_audio_upload_and_transcribe()
        if user_input or transcript:
            reply = user_input if user_input else transcript
            st.session_state.t2_chat_history.append({"role": "user", "content": reply})
            t, k = st.session_state.t2_current_vocab
            feedback = get_openai_feedback_teil2(t, k, reply)
            st.session_state.t2_chat_history.append({"role": "assistant", "content": feedback})
            st.session_state.t2_rounds_done += 1
            if st.session_state.t2_rounds_done < st.session_state.t2_rounds_total:
                vocab = get_next_vocab(st.session_state.t2_vocabs_used)
                if vocab:
                    st.session_state.t2_current_vocab = vocab[0]
                    st.session_state.t2_vocabs_used.append(vocab[0])
                    t, k = vocab[0]
                    ai_msg = (
                        f"Next prompt:\n\n"
                        f"**Topic:** {t}\n**Keyword:** {k}\n\n"
                        "Write a question and answer in German, or upload audio."
                    )
                    st.session_state.t2_chat_history.append({"role": "assistant", "content": ai_msg})
            else:
                st.session_state.t2_chat_history.append({
                    "role": "assistant",
                    "content": "Well done! That's all for today. Review your corrections and try again for more practice!"
                })
            st.rerun()
    else:
        st.chat_input(disabled=True)
        st.info("Session finished! You can refresh to start again or move to another part.")

# ====== TEIL 3 CHAT MODE ======
def get_next_bitten(used, n=1):
    available = [b for b in BITTEN_PROMPTS if b not in used]
    return random.sample(available, min(len(available), n)) if available else []

def teil3_chat():
    st.header("Teil 3 – Bitten & Antworten (Chat Mode)")
    st.markdown("Practice making polite requests and suitable replies in German. You may type or upload audio for each prompt.")

    if "t3_chat_history" not in st.session_state:
        st.session_state.t3_chat_history = []
        st.session_state.t3_prompts_used = []
        st.session_state.t3_rounds_total = None
        st.session_state.t3_rounds_done = 0
        st.session_state.t3_waiting_for_count = True
        st.session_state.t3_current_prompt = None
        st.session_state.t3_chat_history.append({
            "role": "assistant",
            "content": (
                "Welcome to Teil 3: Bitten & Antworten!\n\n"
                "In this part, you will practice writing polite requests (e.g., 'Können Sie bitte ...?') and suitable replies in German, both in one message. "
                "You will get correction and feedback for each answer.\n\n"
                "How many tasks do you want to practice today? (Enter a number from 1 to 5)"
            )
        })

    for msg in st.session_state.t3_chat_history:
        align = "user" if msg["role"] == "user" else "assistant"
        st.chat_message(align).write(msg["content"])

    if st.session_state.t3_waiting_for_count:
        user_input = st.chat_input("Enter a number (1-5):")
        if user_input:
            try:
                n = int(user_input.strip())
                if 1 <= n <= 5:
                    st.session_state.t3_rounds_total = n
                    st.session_state.t3_rounds_done = 0
                    st.session_state.t3_chat_history.append({"role": "user", "content": user_input})
                    prompt = get_next_bitten(st.session_state.t3_prompts_used)
                    st.session_state.t3_current_prompt = prompt[0]
                    st.session_state.t3_prompts_used.append(prompt[0])
                    st.session_state.t3_waiting_for_count = False
                    ai_msg = (
                        f"Great! Here is your first prompt:\n\n"
                        f"**Task:** {prompt[0]}\n\n"
                        "Write a polite request in German (ending with '?') and a suitable reply (ending with '.'), both in one message. Or upload audio."
                    )
                    st.session_state.t3_chat_history.append({"role": "assistant", "content": ai_msg})
                    st.rerun()
                else:
                    st.session_state.t3_chat_history.append({
                        "role": "assistant",
                        "content": "Please enter a number between 1 and 5."
                    })
                    st.rerun()
            except ValueError:
                st.session_state.t3_chat_history.append({
                    "role": "assistant",
                    "content": "Please enter a valid number (1-5)."
                })
                st.rerun()
        return

    if st.session_state.t3_rounds_done < st.session_state.t3_rounds_total:
        user_input = st.chat_input("Type your request and reply (both in German, one message):")
        transcript = show_audio_upload_and_transcribe()
        if user_input or transcript:
            reply = user_input if user_input else transcript
            st.session_state.t3_chat_history.append({"role": "user", "content": reply})
            task = st.session_state.t3_current_prompt
            feedback = get_openai_feedback_teil3(task, reply)
            st.session_state.t3_chat_history.append({"role": "assistant", "content": feedback})
            st.session_state.t3_rounds_done += 1
            if st.session_state.t3_rounds_done < st.session_state.t3_rounds_total:
                prompt = get_next_bitten(st.session_state.t3_prompts_used)
                if prompt:
                    st.session_state.t3_current_prompt = prompt[0]
                    st.session_state.t3_prompts_used.append(prompt[0])
                    ai_msg = (
                        f"Next task:\n\n"
                        f"**Task:** {prompt[0]}\n\n"
                        "Write a polite request and a reply in German, or upload audio."
                    )
                    st.session_state.t3_chat_history.append({"role": "assistant", "content": ai_msg})
            else:
                st.session_state.t3_chat_history.append({
                    "role": "assistant",
                    "content": "Well done! That's all for today. Review your corrections and try again for more practice!"
                })
            st.rerun()
    else:
        st.chat_input(disabled=True)
        st.info("Session finished! You can refresh to start again or move to another part.")

# ====== MAIN APP ======
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
    teil1()
elif tab.startswith("Teil 2"):
    teil2_chat()
elif tab.startswith("Teil 3"):
    teil3_chat()
