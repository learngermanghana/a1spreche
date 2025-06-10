import streamlit as st
import openai
import random
import pandas as pd

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

# ========== OPENAI KEY SETUP ==========

openai.api_key = st.secrets["OPENAI_API_KEY"]

# ========== VOCABULARY LISTS ==========

VOCAB = [
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

# ========== AI FEEDBACK FUNCTIONS (ENGLISH FEEDBACK) ==========

def get_openai_feedback_teil1(inputs):
    prompt = f"""
You are a German teacher for A1 beginners. Check the student's self-introduction. Look for:
- Each answer is a simple, complete sentence.
- Word order, capitalization, and punctuation are correct.
- Use only A1 German words and grammar.

Return corrections and short feedback for each point IN ENGLISH. If there are mistakes, explain briefly in English, with a corrected example.

Student introduction:
Name: {inputs['name']}
Age: {inputs['age']}
Country: {inputs['country']}
Residence: {inputs['residence']}
Languages: {inputs['languages']}
Profession: {inputs['profession']}
Hobby: {inputs['hobby']}
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )
    return response.choices[0].message.content.strip()

def get_openai_feedback_teil2(thema, stichwort, frage, antwort):
    prompt = f"""
You are a German teacher for A1 beginners. Check the student's question and answer for the topic and keyword. Look for:
- Does the question start with a question word or a verb? Does it end with "?"?
- Is the answer a simple, complete sentence? Does it end with "."?
- Are capitalization and punctuation correct?

Give a short correction and feedback for both (question and answer) IN ENGLISH. If there are mistakes, explain briefly and show a corrected example.

Topic: {thema}
Keyword: {stichwort}
Question: {frage}
Answer: {antwort}
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

def get_openai_feedback_teil3(aufgabe, bitte, antwort):
    prompt = f"""
You are a German teacher for A1 beginners. Check the student's polite request and the reply for a given task. Look for:
- Is the request polite? Does it start with "Können Sie bitte..." or "Machen Sie bitte..." and end with "?"?
- Is the reply a simple, complete sentence and does it end with "."?
- Are capitalization and punctuation correct?

Give a short correction and feedback for both (request and reply) IN ENGLISH. If there are mistakes, explain briefly and give a corrected example.

Task: {aufgabe}
Request: {bitte}
Reply: {antwort}
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# ========== TEIL 1 ==========

def teil1():
    st.subheader("Teil 1: Self-introduction")
    st.info("Introduce yourself in German using simple, full sentences.")
    inputs = {}
    inputs['name'] = st.text_input("Name (sentence):", placeholder="Ich heiße ...")
    inputs['age'] = st.text_input("Age (sentence):", placeholder="Ich bin ... Jahre alt.")
    inputs['country'] = st.text_input("Country (sentence):", placeholder="Ich komme aus ...")
    inputs['residence'] = st.text_input("Residence (sentence):", placeholder="Ich wohne in ...")
    inputs['languages'] = st.text_input("Languages (sentence):", placeholder="Ich spreche ...")
    inputs['profession'] = st.text_input("Profession (sentence):", placeholder="Ich bin ... von Beruf.")
    inputs['hobby'] = st.text_input("Hobby (sentence):", placeholder="Mein Hobby ist ...")
    if st.button("Check introduction"):
        with st.spinner("Checking..."):
            feedback = get_openai_feedback_teil1(inputs)
            st.success("Feedback from your teacher:")
            st.markdown(feedback)
            st.session_state['teil1_feedback'] = feedback
    if 'teil1_feedback' in st.session_state:
        st.markdown("---")
        st.markdown("**Last feedback:**")
        st.markdown(st.session_state['teil1_feedback'])

# ========== TEIL 2 ==========

def teil2():
    st.subheader("Teil 2: Questions & Answers")
    if 't2_idx' not in st.session_state:
        st.session_state['t2_idx'] = 0
        st.session_state['t2_results'] = []
        st.session_state['t2_order'] = random.sample(VOCAB, len(VOCAB))
    if st.session_state['t2_idx'] < len(VOCAB):
        thema, stichwort = st.session_state['t2_order'][st.session_state['t2_idx']]
        st.info(f"Topic: **{thema}**  |  Keyword: **{stichwort}**")
        frage = st.text_input("Your question (ends with ?):", key=f"frage_{st.session_state['t2_idx']}")
        antwort = st.text_input("Your answer (ends with .):", key=f"antwort_{st.session_state['t2_idx']}")
        if st.button("Check answer", key=f"check2_{st.session_state['t2_idx']}"):
            with st.spinner("Checking..."):
                feedback = get_openai_feedback_teil2(thema, stichwort, frage, antwort)
                st.session_state['t2_results'].append({
                    "Topic": thema,
                    "Keyword": stichwort,
                    "Question": frage,
                    "Answer": antwort,
                    "Feedback": feedback
                })
                st.session_state['t2_idx'] += 1
                st.rerun()
    else:
        st.success("Teil 2 finished! Here is your feedback:")
        for res in st.session_state['t2_results']:
            st.write(f"**Topic:** {res['Topic']} | **Keyword:** {res['Keyword']}")
            st.write(f"**Question:** {res['Question']}")
            st.write(f"**Answer:** {res['Answer']}")
            st.markdown(f"**Feedback:**\n{res['Feedback']}")
            st.markdown("---")
        if st.button("Practice Teil 2 again"):
            for k in ['t2_idx', 't2_results', 't2_order']:
                st.session_state.pop(k, None)
            st.rerun()

# ========== TEIL 3 ==========

def teil3():
    st.subheader("Teil 3: Requests & Replies")
    if 't3_idx' not in st.session_state:
        st.session_state['t3_idx'] = 0
        st.session_state['t3_results'] = []
        st.session_state['t3_order'] = random.sample(BITTEN_PROMPTS, len(BITTEN_PROMPTS))
    if st.session_state['t3_idx'] < len(BITTEN_PROMPTS):
        aufgabe = st.session_state['t3_order'][st.session_state['t3_idx']]
        st.info(f"Task: {aufgabe}")
        bitte = st.text_input("Your request (ends with ?):", key=f"bitte_{st.session_state['t3_idx']}")
        antwort = st.text_input("Reply to the request (ends with .):", key=f"antwort3_{st.session_state['t3_idx']}")
        if st.button("Check reply", key=f"check3_{st.session_state['t3_idx']}"):
            with st.spinner("Checking..."):
                feedback = get_openai_feedback_teil3(aufgabe, bitte, antwort)
                st.session_state['t3_results'].append({
                    "Task": aufgabe,
                    "Request": bitte,
                    "Reply": antwort,
                    "Feedback": feedback
                })
                st.session_state['t3_idx'] += 1
                st.rerun()
    else:
        st.success("Teil 3 finished! Here is your feedback:")
        for res in st.session_state['t3_results']:
            st.write(f"**Task:** {res['Task']}")
            st.write(f"**Request:** {res['Request']}")
            st.write(f"**Reply:** {res['Reply']}")
            st.markdown(f"**Feedback:**\n{res['Feedback']}")
            st.markdown("---")
        if st.button("Practice Teil 3 again"):
            for k in ['t3_idx', 't3_results', 't3_order']:
                st.session_state.pop(k, None)
            st.rerun()

# ========== MAIN APP ==========

st.set_page_config(page_title=f"A1 Sprechen – {SCHOOL_NAME}", layout="wide")
st.title(f"A1 Sprechen – {SCHOOL_NAME}")

st.markdown(f"""
**School:** {SCHOOL_NAME}  
[Record your voice here (Vocaroo)]({VOCAROO_URL})  
[Send result to teacher (WhatsApp)]({BASE_URL})
""")

# Require login before using the app
_ = login_main()

tab = st.radio("Choose a part:", ["Teil 1: Self-introduction", "Teil 2: Questions & Answers", "Teil 3: Requests & Replies"])

if tab.startswith("Teil 1"):
    teil1()
elif tab.startswith("Teil 2"):
    teil2()
elif tab.startswith("Teil 3"):
    teil3()
