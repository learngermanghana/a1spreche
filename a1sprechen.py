# -*- coding: utf-8 -*-
# A1 Sprechen Streamlit App with Live Audio Recording
import streamlit as st
import pandas as pd
import random
import time
import urllib.parse


# School information
SCHOOL_NAME = "Learn Language Education Academy"
BASE_URL = "https://api.whatsapp.com/message/EYMY3524WL6IC1?autoload=1&app_absent=0"
VOCAROO_URL = "https://vocaroo.com/1bW5U4NUiwmk"

# --- Load valid student codes ---
def load_valid_codes():
    try:
        return pd.read_csv("student_codes.csv")["code"].tolist()
    except Exception:
        return []

# --- Login on main page (hidden input) ---
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

# --- Grammar check helpers ---
def is_w_question(text):
    word = text.strip().split()[0].lower() if text.split() else ""
    return word in ["was","wie","wo","wann","wer","wen","wem","warum","welche","welcher","welches"]

def is_verb_question(text):
    word = text.strip().split()[0].lower() if text.split() else ""
    return word in ["haben","sein","gehen","kommen","machen","sehen","sprechen","fahren","arbeiten","lesen"]

def check_question_structure(q):
    if not q.endswith("?"):
        return False, "Question must end with '?'"
    if not (is_w_question(q) or is_verb_question(q)):
        return False, "Question must start with a W-word or verb"
    return True, "Question format OK"

def check_answer_structure(a):
    if not a.endswith("."):
        return False, "Answer must end with '.'"
    if not a[0].isupper():
        return False, "Answer must start with a capital letter"
    if len(a.split()) < 2:
        return False, "Answer too short, use a full sentence"
    return True, "Answer format OK"

# --- Teil 1: Introduction ---
def teil1():
    st.header("Teil 1 – Introduction")
    st.markdown("**What to expect:** Introduce yourself with Name, Alter, Land, Wohnort, Sprachen, Beruf, Hobby.")
    st.text_input("Name:")
    st.text_input("Alter:")
    st.text_input("Land:")
    st.text_input("Wohnort:")
    st.text_input("Sprachen:")
    st.text_input("Beruf:")
    st.text_input("Hobby:")
    st.text_input("Wie buchstabieren Sie Ihren Namen?")
    st.text_input("Sind Sie verheiratet? (Ja/Nein)")
    st.text_input("Wie alt ist Ihre Mutter?")

    if 'intro_submitted' not in st.session_state:
        st.session_state['intro_submitted'] = False
    if st.button("🔵 Submit Introduction"):
        st.session_state['intro_submitted'] = True
        st.success("Introduction saved.")
        st.info("Now practice your introduction live. Grant mic access when prompted.")
    if st.session_state['intro_submitted']:
        webrtc_streamer(key="live_intro", media_stream_constraints={"audio": True, "video": False})
        if st.button("🔘 Done Recording Introduction"):
            st.success("Recording saved.")
            st.info("Don't forget to share your progress with your tutor.")
            st.markdown(f"[Send via WhatsApp]({BASE_URL})")
            # Restart and complete options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Restart"):
                    for k in ['t3_tasks','t3_sel','t3_idx','t3_score','t3_start','t3_sub','answers3','t3_done']:
                        session.pop(k, None)
                    st.rerun()
            with col2:
                if st.button("✅ Complete for today"):
                    st.success("Übung für heute abgeschlossen. Bis zum nächsten Mal!")
                    st.stop()

# --- Teil 2: Frage & Antwort ---
def teil2(session):
    st.header("Teil 2 – Frage & Antwort")
    st.markdown("**What to expect:** Ask and answer one question-answer pair on a single line. The question should end with '?' and the answer with '.'.")
    vocab = [
        ("Geschäft","schließen"),("Uhr","Uhrzeit"),("Arbeit","Kollege"),("Hausaufgabe","machen"),
        ("Küche","kochen"),("Freizeit","lesen"),("Telefon","anrufen"),("Reise","Hotel"),
        ("Auto","fahren"),("Einkaufen","Obst"),("Schule","Lehrer"),("Geburtstag","Geschenk"),
        ("Essen","Frühstück"),("Arzt","Termin"),("Zug","Abfahrt"),("Wetter","Regen"),
        ("Buch","lesen"),("Computer","E-Mail"),("Kind","spielen"),("Wochenende","Plan"),
        ("Bank","Geld"),("Sport","laufen"),("Abend","Fernsehen"),("Freunde","Besuch"),
        ("Bahn","Fahrkarte"),("Straße","Stau"),("Essen gehen","Restaurant"),("Hund","Futter"),
        ("Familie","Kinder"),("Post","Brief"),("Nachbarn","laut"),("Kleid","kaufen"),
        ("Büro","Chef"),("Urlaub","Strand"),("Kino","Film"),("Internet","Seite"),
        ("Bus","Abfahrt"),("Arztpraxis","Wartezeit"),("Kuchen","backen"),("Park","spazieren"),
        ("Bäckerei","Brötchen"),("Geldautomat","Karte"),("Buchladen","Roman"),("Fernseher","Programm"),
        ("Tasche","vergessen"),("Stadtplan","finden"),("Ticket","bezahlen"),("Zahnarzt","Schmerzen"),
        ("Museum","Öffnungszeiten"),("Handy","Akku leer")
    ]
    if session.get('t2_tasks', 0) == 0:
        num = st.number_input("Wie viele Q&A?", 1, len(vocab), len(vocab))
        if st.button("▶️ Start Teil 2"):
            session.update({'t2_tasks': num, 't2_sel': random.sample(vocab, num),
                            't2_idx': 0, 't2_score': 0, 't2_start': time.time(),
                            't2_sub': [False]*num, 'answers2': []})
            st.rerun()
        return
    idx, num = session['t2_idx'], session['t2_tasks']
    rem = max(0, num*60 - (time.time() - session['t2_start']))
    st.write(f"⏱ Zeit übrig: {int(rem)}s")
    st.progress(int(idx/num*100))
    if rem <= 0:
        session['t2_idx'] = num
    if idx < num:
        thema, wort = session['t2_sel'][idx]
        st.subheader(f"{idx+1}/{num}: Thema – {thema}, Stichwort – {wort}")
        qa = st.text_input("Frage und Antwort:", key=f"qa{idx}")
        if not session['t2_sub'][idx] and st.button("Antwort einreichen", key=f"s2_{idx}"):
            parts = qa.split('?')
            q = parts[0].strip() + '?' if len(parts)>1 else ''
            a = parts[1].strip() if len(parts)>1 else ''
            ok_q,_ = check_question_structure(q)
            ok_a,_ = check_answer_structure(a)
            sc = 1 if (ok_q and ok_a) else 0
            session['t2_score'] += sc
            session['answers2'].append({'q':q,'a':a,'score':sc})
            session['t2_sub'][idx] = True
        if session['t2_sub'][idx] and st.button("Nächste Frage", key=f"n2_{idx}"):
            session['t2_idx'] += 1
            st.rerun()
    else:
        st.success(f"Teil 2 abgeschlossen! Punkte: {session['t2_score']}/{num}")
        if not session.get('t2_done', False):
            session.setdefault('summary', []).extend(session['answers2'])
            session['t2_done'] = True
        st.info("Now practice your Teil 2 summary live. Grant mic access.")
        webrtc_streamer(key="live2", media_stream_constraints={"audio": True, "video": False})
        if st.button("Done Recording", key="done2"):
            st.success("Aufnahme gespeichert.")
            st.info("Vergiss nicht, Deinen Fortschritt mit Deinem Tutor zu teilen.")
            st.markdown(f"[Sende über WhatsApp]({BASE_URL})")
            # Neustart und Beenden Optionen
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Restart"):
                    for k in ['t2_tasks','t2_sel','t2_idx','t2_score','t2_start','t2_sub','answers2','t2_done']:
                        session.pop(k, None)
                    st.rerun()
            with col2:
                if st.button("✅ Complete for today"):
                    st.success("Übung für heute abgeschlossen. Bis zum nächsten Mal!")
                    st.stop()

# --- Teil 3: Anfragen & Antworten ---
def teil3(session):
    st.header("Teil 3 – Anfragen & Antworten")
    st.markdown("**What to expect:** Formulate a polite request and its reply on a single line. The request should end with '?' and the reply with '.'.")
    prompts = [
        "Radio anmachen","Fenster zum machen","Licht anschalten","Tür aufmachen","Tisch sauber machen",
        "Hausaufgaben schicken","Buch bringen","Handy ausmachen","Stuhl nehmen","Wasser holen",
        "Fenster öffnen","Musik leiser machen","Tafel sauber wischen","Kaffee kochen","Deutsch üben",
        "Auto waschen","Kind abholen","Tisch decken","Termin machen","Nachricht schreiben"
    ]
    if session.get('t3_tasks', 0) == 0:
        num = st.number_input("How many requests?", 1, len(prompts), len(prompts))
        if st.button("▶️ Start Teil 3"):
            session.update({
                't3_tasks': num,
                't3_sel': random.sample(prompts, num),
                't3_idx': 0,
                't3_score': 0,
                't3_start': time.time(),
                't3_sub': [False]*num,
                'answers3': []
            })
            st.rerun()
        return
    idx, num = session['t3_idx'], session['t3_tasks']
    rem = max(0, num*45 - (time.time() - session['t3_start']))
    st.write(f"⏱ Time left: {int(rem)}s")
    st.progress(int(idx/num*100))
    if rem <= 0:
        session['t3_idx'] = num
    if idx < num:
        task = session['t3_sel'][idx]
        st.subheader(f"{idx+1}/{num}: {task}")
        rr = st.text_input("Req+Reply:", key=f"rr{idx}")
        if not session['t3_sub'][idx] and st.button("Submit Reply", key=f"s3_{idx}"):
            parts = rr.split('?')
            req = parts[0].strip() + '?' if len(parts)>1 else ''
            rep = parts[1].strip() if len(parts)>1 else ''
            ok = req.endswith('?') and rep.endswith('.')
            sc = 1 if ok else 0
            session['t3_score'] += sc
            session['answers3'].append({'req':req,'rep':rep,'score':sc})
            session['t3_sub'][idx] = True
        if session['t3_sub'][idx] and st.button("Next", key=f"n3_{idx}"):
            session['t3_idx'] += 1
            st.rerun()
    else:
        st.success(f"Done Teil 3! Score: {session['t3_score']}/{num}")
        if not session.get('t3_done', False):
            session.setdefault('summary', []).extend(session['answers3'])
            session['t3_done'] = True
        st.info("Now practice your Teil 3 summary live. Grant mic access.")
        webrtc_streamer(key="live3", media_stream_constraints={"audio": True, "video": False})
        if st.button("Done Recording", key="done3"):
            st.success("Recording saved. Please share via WhatsApp.")
            st.info("Don't forget to share your progress with your tutor.")
            st.markdown(f"[Send via WhatsApp]({BASE_URL})")

# --- Main App & Summary ---
def main():
    st.set_page_config(page_title=f"A1 Sprechen – {SCHOOL_NAME}", layout="wide")
    st.title(f"A1 Sprechen – {SCHOOL_NAME}")
    _ = login_main()
    if 'summary' not in st.session_state:
        st.session_state['summary'] = []
    part = st.radio("Select section:", ["Teil 1","Teil 2","Teil 3"], horizontal=True)
    if part == "Teil 1":
        teil1()
    elif part == "Teil 2":
        teil2(st.session_state)
    else:
        teil3(st.session_state)
    st.markdown("---")
    if st.session_state['summary']:
        df = pd.DataFrame(st.session_state['summary'])
        st.header("Session Summary")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "summary.csv")
        text = urllib.parse.quote(df.to_string(index=False))
        st.markdown(f"[Share via WhatsApp]({BASE_URL}&text={text})")

if __name__ == "__main__":
    main()
