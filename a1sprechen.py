import streamlit as st
import openai
import random
import pandas as pd

# ------------------ SCHOOL INFO & LOGIN ------------------
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

# ------------------ OPENAI KEY SETUP ------------------
openai.api_key = st.secrets["OPENAI_API_KEY"]  # or use os.environ['OPENAI_API_KEY']

# ------------------ VOCABULARY LISTS ------------------
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

# ------------------ AI FEEDBACK FUNCTIONS ------------------
def get_openai_feedback_teil1(inputs):
    prompt = f"""
Du bist ein Deutschlehrer für das Niveau A1. Überprüfe die Selbstvorstellung eines Schülers. Achte auf:
- Jede Antwort ist ein einfacher, vollständiger Satz.
- Wortstellung, Großschreibung und Zeichensetzung sind korrekt.
- Nutze nur einfaches Deutsch (A1).
Gib für jeden Punkt eine kurze Korrektur und eine Rückmeldung auf Deutsch (A1-Niveau).

Vorstellung des Schülers:
Name: {inputs['name']}
Alter: {inputs['age']}
Land: {inputs['country']}
Wohnort: {inputs['residence']}
Sprachen: {inputs['languages']}
Beruf: {inputs['profession']}
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
Du bist ein Deutschlehrer für das Niveau A1. Überprüfe die Frage und Antwort eines Schülers zu einem Thema. Achte auf:
- Frage beginnt mit Fragewort/Verb? Endet mit „?“?
- Antwort ist ein einfacher, vollständiger Satz und endet mit „.“?
- Großschreibung und Zeichensetzung korrekt?
Gib für beide eine kurze Korrektur und Rückmeldung auf Deutsch (A1-Niveau).

Thema: {thema}
Stichwort: {stichwort}
Frage: {frage}
Antwort: {antwort}
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

def get_openai_feedback_teil3(aufgabe, bitte, antwort):
    prompt = f"""
Du bist ein Deutschlehrer für das Niveau A1. Überprüfe die Bitte und Antwort eines Schülers zu einer Aufgabe. Achte auf:
- Bitte höflich formuliert? Z.B. „Können Sie bitte ...?“ oder „Machen Sie bitte ...?“ Endet mit „?“
- Antwort ist ein einfacher, vollständiger Satz, endet mit „.“?
- Großschreibung und Zeichensetzung korrekt?
Gib für beide eine kurze Korrektur und Rückmeldung auf Deutsch (A1-Niveau).

Aufgabe: {aufgabe}
Bitte: {bitte}
Antwort: {antwort}
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# ------------------ TEIL 1 ------------------
def teil1():
    st.subheader("Teil 1: Selbstvorstellung")
    st.info("Stelle dich mit vollständigen Sätzen auf Deutsch vor.")
    inputs = {}
    inputs['name'] = st.text_input("Name (Satz):", placeholder="Ich heiße ...")
    inputs['age'] = st.text_input("Alter (Satz):", placeholder="Ich bin ... Jahre alt.")
    inputs['country'] = st.text_input("Land (Satz):", placeholder="Ich komme aus ...")
    inputs['residence'] = st.text_input("Wohnort (Satz):", placeholder="Ich wohne in ...")
    inputs['languages'] = st.text_input("Sprachen (Satz):", placeholder="Ich spreche ...")
    inputs['profession'] = st.text_input("Beruf (Satz):", placeholder="Ich bin ... von Beruf.")
    inputs['hobby'] = st.text_input("Hobby (Satz):", placeholder="Mein Hobby ist ...")
    if st.button("Vorstellung prüfen"):
        with st.spinner("Wird geprüft..."):
            feedback = get_openai_feedback_teil1(inputs)
            st.success("Rückmeldung von deinem Deutschlehrer:")
            st.markdown(feedback)
            st.session_state['teil1_feedback'] = feedback
    if 'teil1_feedback' in st.session_state:
        st.markdown("---")
        st.markdown("**Letztes Feedback:**")
        st.markdown(st.session_state['teil1_feedback'])

# ------------------ TEIL 2 ------------------
def teil2():
    st.subheader("Teil 2: Fragen & Antworten")
    if 't2_idx' not in st.session_state:
        st.session_state['t2_idx'] = 0
        st.session_state['t2_results'] = []
        st.session_state['t2_order'] = random.sample(VOCAB, len(VOCAB))
    if st.session_state['t2_idx'] < len(VOCAB):
        thema, stichwort = st.session_state['t2_order'][st.session_state['t2_idx']]
        st.info(f"Thema: **{thema}**  |  Stichwort: **{stichwort}**")
        frage = st.text_input("Deine Frage (mit ?):", key=f"frage_{st.session_state['t2_idx']}")
        antwort = st.text_input("Deine Antwort (mit .):", key=f"antwort_{st.session_state['t2_idx']}")
        if st.button("Antwort prüfen", key=f"check2_{st.session_state['t2_idx']}"):
            with st.spinner("Wird geprüft..."):
                feedback = get_openai_feedback_teil2(thema, stichwort, frage, antwort)
                st.session_state['t2_results'].append({
                    "Thema": thema,
                    "Stichwort": stichwort,
                    "Frage": frage,
                    "Antwort": antwort,
                    "Feedback": feedback
                })
                st.session_state['t2_idx'] += 1
                st.experimental_rerun()
    else:
        st.success("Teil 2 abgeschlossen! Rückmeldung:")
        for res in st.session_state['t2_results']:
            st.write(f"**Thema:** {res['Thema']} | **Stichwort:** {res['Stichwort']}")
            st.write(f"**Frage:** {res['Frage']}")
            st.write(f"**Antwort:** {res['Antwort']}")
            st.markdown(f"**Feedback:**\n{res['Feedback']}")
            st.markdown("---")
        if st.button("Nochmal üben (Teil 2)"):
            for k in ['t2_idx', 't2_results', 't2_order']:
                st.session_state.pop(k, None)
            st.rerun()

# ------------------ TEIL 3 ------------------
def teil3():
    st.subheader("Teil 3: Bitten & Antworten")
    if 't3_idx' not in st.session_state:
        st.session_state['t3_idx'] = 0
        st.session_state['t3_results'] = []
        st.session_state['t3_order'] = random.sample(BITTEN_PROMPTS, len(BITTEN_PROMPTS))
    if st.session_state['t3_idx'] < len(BITTEN_PROMPTS):
        aufgabe = st.session_state['t3_order'][st.session_state['t3_idx']]
        st.info(f"**Aufgabe:** {aufgabe}")
        bitte = st.text_input("Deine Bitte (mit ?):", key=f"bitte_{st.session_state['t3_idx']}")
        antwort = st.text_input("Antwort auf die Bitte (mit .):", key=f"antwort3_{st.session_state['t3_idx']}")
        if st.button("Antwort prüfen", key=f"check3_{st.session_state['t3_idx']}"):
            with st.spinner("Wird geprüft..."):
                feedback = get_openai_feedback_teil3(aufgabe, bitte, antwort)
                st.session_state['t3_results'].append({
                    "Aufgabe": aufgabe,
                    "Bitte": bitte,
                    "Antwort": antwort,
                    "Feedback": feedback
                })
                st.session_state['t3_idx'] += 1
                st.experimental_rerun()
    else:
        st.success("Teil 3 abgeschlossen! Rückmeldung:")
        for res in st.session_state['t3_results']:
            st.write(f"**Aufgabe:** {res['Aufgabe']}")
            st.write(f"**Bitte:** {res['Bitte']}")
            st.write(f"**Antwort:** {res['Antwort']}")
            st.markdown(f"**Feedback:**\n{res['Feedback']}")
            st.markdown("---")
        if st.button("Nochmal üben (Teil 3)"):
            for k in ['t3_idx', 't3_results', 't3_order']:
                st.session_state.pop(k, None)
            st.experimental_rerun()

# ------------------ MAIN APP ------------------
st.set_page_config(page_title=f"A1 Sprechen – {SCHOOL_NAME}", layout="wide")
st.title(f"A1 Sprechen – {SCHOOL_NAME}")

# Show school info
st.markdown(f"""
**Schule:** {SCHOOL_NAME}  
[Sprich hier auf Vocaroo]({VOCAROO_URL}) | [Ergebnis an Lehrer senden (WhatsApp)]({BASE_URL})
""")

# Require login before any part
_ = login_main()

tab = st.radio("Wähle einen Teil:", ["Teil 1: Selbstvorstellung", "Teil 2: Fragen & Antworten", "Teil 3: Bitten & Antworten"])

if tab.startswith("Teil 1"):
    teil1()
elif tab.startswith("Teil 2"):
    teil2()
elif tab.startswith("Teil 3"):
    teil3()
