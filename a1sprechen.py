import streamlit as st
import pandas as pd
import random
import requests
from streamlit_webrtc import webrtc_streamer

# ---- Helper: rerun for session reset ----
def rerun():
    st.experimental_rerun()

# ---- Settings ----
SCHOOL_NAME = "Learn Language Education Academy"
BASE_URL = "https://api.whatsapp.com/message/EYMY3524WL6IC1?autoload=1&app_absent=0"

# ---- Load valid student codes ----
def load_valid_codes():
    try:
        df = pd.read_csv("student_codes.csv")
        return df['code'].astype(str).tolist()
    except Exception:
        return []

def login_main():
    if 'student_code' not in st.session_state:
        code = st.text_input("Student Code:", type="password")
        if code:
            valid = load_valid_codes()
            if code in valid:
                st.session_state['student_code'] = code
                st.success("Login successful!")
            else:
                st.error("Invalid code. Please contact your teacher.")
                st.stop()
        else:
            st.info("Enter your student code to begin.")
            st.stop()
    return st.session_state['student_code']

# ---- LanguageTool HTTP API Grammar Check ----
def grammar_feedback(text):
    url = "https://api.languagetool.org/v2/check"
    data = {
        "text": text,
        "language": "de"
    }
    try:
        resp = requests.post(url, data=data, timeout=8)
        result = resp.json()
    except Exception:
        return False, "Error connecting to grammar server."
    matches = result.get("matches", [])
    if not matches:
        return True, "Correct! 🎉"
    else:
        feedbacks = []
        for m in matches:
            msg = m["message"]
            sug = ""
            if m.get('replacements'):
                sug = f" (Suggestion: {m['replacements'][0]['value']})"
            feedbacks.append(f"{msg}{sug}")
        return False, " | ".join(feedbacks)

# ---- Helper: Show vocab/prompt lists ----
def show_vocab_popup(vocab_list, label="See all vocab pairs (click to expand)"):
    with st.expander(label):
        df = pd.DataFrame(vocab_list, columns=["Topic", "Keyword"])
        st.dataframe(df, hide_index=True)

def show_prompts_popup(prompt_list, label="See all polite request prompts (click to expand)"):
    with st.expander(label):
        df = pd.DataFrame(prompt_list, columns=["Prompt"])
        st.dataframe(df, hide_index=True)

# ---- Teil 1: Introduction ----
def teil1():
    st.header("Teil 1 – Introduction")
    st.markdown("**What to expect:** Introduce yourself with Name, Age, Country, City, Languages, Job, Hobby.")

    fields = [
        ("Name", "Name:"),
        ("Age", "Age:"),
        ("Country", "Country:"),
        ("City", "City:"),
        ("Languages", "Languages:"),
        ("Job", "Job:"),
        ("Hobby", "Hobby:"),
        ("Spelling", "How do you spell your name?"),
        ("Married", "Are you married? (Yes/No)"),
        ("MotherAge", "How old is your mother?")
    ]

    responses = {}
    for key, label in fields:
        responses[key] = st.text_input(label)

    if 'intro_submitted' not in st.session_state:
        st.session_state['intro_submitted'] = False

    if st.button("🔵 Submit Introduction"):
        st.session_state['intro_submitted'] = True
        score = sum(bool(responses[k].strip()) for k, _ in fields)
        missing = [label for (k, label) in fields if not responses[k].strip()]
        st.session_state["teil1_score"] = score
        st.session_state.setdefault("summary", []).append(
            {**responses, "Score": score, "Max": len(fields)}
        )
        if missing:
            st.warning("Please fill in: " + ", ".join(missing))
        st.success(f"Introduction saved. Score: {score}/{len(fields)}")
        st.info("Now practice your introduction live. Grant mic access when prompted.")

    if st.session_state['intro_submitted']:
        webrtc_streamer(key="live_intro", media_stream_constraints={"audio": True, "video": False})
        if st.button("🔘 Done Recording Introduction"):
            st.success("Recording saved.")
            st.info("Don't forget to share your progress with your tutor.")
            st.markdown(f"[Send via WhatsApp]({BASE_URL})")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Restart"):
                    for k in [
                        'intro_submitted', 'teil1_score', 'summary'
                    ]:
                        st.session_state.pop(k, None)
                    rerun()
                    return
            with col2:
                if st.button("✅ Complete for today"):
                    st.success("Practice for today completed. See you next time!")
                    st.stop()

    if st.session_state.get("summary"):
        st.markdown("### Your Introduction Summary")
        df = pd.DataFrame(st.session_state.get("summary"))
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Introduction as CSV", csv, "teil1_intro.csv")

# ---- Teil 2 vocab ----
TEIL2_VOCAB = [
    ("Geschäft", "schließen"), ("Uhr", "Uhrzeit"), ("Arbeit", "Kollege"), ("Hausaufgabe", "machen"),
    ("Küche", "kochen"), ("Freizeit", "lesen"), ("Telefon", "anrufen"), ("Reise", "Hotel"),
    ("Auto", "fahren"), ("Einkaufen", "Obst"), ("Schule", "Lehrer"), ("Geburtstag", "Geschenk"),
    ("Essen", "Frühstück"), ("Arzt", "Termin"), ("Zug", "Abfahrt"), ("Wetter", "Regen"),
    ("Buch", "lesen"), ("Computer", "E-Mail"), ("Kind", "spielen"), ("Wochenende", "Plan"),
    ("Bank", "Geld"), ("Sport", "laufen"), ("Abend", "Fernsehen"), ("Freunde", "Besuch"),
    ("Bahn", "Fahrkarte"), ("Straße", "Stau"), ("Essen gehen", "Restaurant"), ("Hund", "Futter"),
    ("Familie", "Kinder"), ("Post", "Brief"), ("Nachbarn", "laut"), ("Kleid", "kaufen"),
    ("Büro", "Chef"), ("Urlaub", "Strand"), ("Kino", "Film"), ("Internet", "Seite"),
    ("Bus", "Abfahrt"), ("Arztpraxis", "Wartezeit"), ("Kuchen", "backen"), ("Park", "spazieren"),
    ("Bäckerei", "Brötchen"), ("Geldautomat", "Karte"), ("Buchladen", "Roman"), ("Fernseher", "Programm"),
    ("Tasche", "vergessen"), ("Stadtplan", "finden"), ("Ticket", "bezahlen"), ("Zahnarzt", "Schmerzen"),
    ("Museum", "Öffnungszeiten"), ("Handy", "Akku leer"), ("Fenster", "offen"), ("Auto", "Reparatur"),
    ("Supermarkt", "einkaufen"), ("Frühstück", "Kaffee"), ("Apotheke", "Medikament"), ("Flughafen", "Flug"),
    ("Berg", "steigen"), ("Spielplatz", "spielen"), ("See", "schwimmen"), ("Baum", "klettern"),
    ("Straßenbahn", "Fahrkarte"), ("Schwimmbad", "schwimmen"), ("Zirkus", "Clown"), ("Garten", "Blumen"),
    ("Markt", "Gemüse"), ("Bibliothek", "Buch"), ("Restaurant", "Tisch reservieren"), ("Polizei", "Anzeige")
]

def teil2():
    st.header("Teil 2 – Question & Answer Practice")
    st.markdown(
        "A topic and a keyword will appear. Make a **German question** (with '?') and answer (with '.') using both words. "
        "Each correct Q&A is 1 point."
    )
    show_vocab_popup(TEIL2_VOCAB)

    if 't2_total' not in st.session_state:
        st.session_state['t2_total'] = 1
    t2_total = st.number_input(
        "How many Q&A do you want to practice?", 1, len(TEIL2_VOCAB), st.session_state['t2_total']
    )
    st.session_state['t2_total'] = t2_total

    if st.button("Start new Teil 2 session"):
        for k in ['t2_idxs', 't2_idx', 't2_score', 't2_history']:
            st.session_state.pop(k, None)
        rerun()
        return

    if 't2_idxs' not in st.session_state:
        st.session_state['t2_idxs'] = random.sample(range(len(TEIL2_VOCAB)), t2_total)
        st.session_state['t2_idx'] = 0
        st.session_state['t2_score'] = 0
        st.session_state['t2_history'] = []

    idx = st.session_state['t2_idx']
    if idx < t2_total:
        i = st.session_state['t2_idxs'][idx]
        thema, wort = TEIL2_VOCAB[i]
        st.subheader(f"Q&A {idx + 1} of {t2_total}")
        st.write(f"**Topic:** {thema}   |   **Keyword:** {wort}")
        q = st.text_input("Your question (must end with '?')", key=f"q2_{idx}")
        a = st.text_input("Your answer (must end with '.')", key=f"a2_{idx}")

        if st.button("Submit Q&A", key=f"submit2_{idx}"):
            if not q.strip().endswith("?"):
                ok_q, msg_q = False, "Question must end with a question mark (?)"
            else:
                ok_q, msg_q = grammar_feedback(q)
            if not a.strip().endswith("."):
                ok_a, msg_a = False, "Answer must end with a period (.)"
            else:
                ok_a, msg_a = grammar_feedback(a)
            sc = 1 if (ok_q and ok_a) else 0
            st.session_state['t2_score'] += sc
            st.session_state['t2_history'].append({
                "Topic": thema, "Keyword": wort, "Question": q, "Answer": a, "Correct": sc,
                "Q Feedback": msg_q, "A Feedback": msg_a
            })
            if sc:
                st.success("Correct! Well done.")
            else:
                if not ok_q:
                    st.error(f"Question error: {msg_q}")
                if not ok_a:
                    st.error(f"Answer error: {msg_a}")
            st.session_state['t2_idx'] += 1
            rerun()
            
    else:
        st.success(f"Your score: {st.session_state['t2_score']} out of {t2_total} in Teil 2.")
        df = pd.DataFrame(st.session_state['t2_history'])
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download results as CSV", csv, "Teil2_results.csv")
        if st.button("Restart Teil 2"):
            for k in ['t2_idxs', 't2_idx', 't2_score', 't2_history']:
                st.session_state.pop(k, None)
            rerun()
            return

# ---- Teil 3 prompts ----
TEIL3_PROMPTS = [
    "Radio anmachen", "Fenster zumachen", "Licht anschalten", "Tür aufmachen", "Tisch sauber machen",
    "Hausaufgaben schicken", "Buch bringen", "Handy ausmachen", "Stuhl nehmen", "Wasser holen",
    "Fenster öffnen", "Musik leiser machen", "Tafel sauber wischen", "Kaffee kochen", "Deutsch üben",
    "Auto waschen", "Kind abholen", "Tisch decken", "Termin machen", "Nachricht schreiben", "Rauchen verboten"
]

def teil3():
    st.header("Teil 3 – Polite Request & Reply Practice")
    st.markdown(
        "A request prompt will appear. Write a **German polite request** (with '?') and a reply (with '.') for each. "
        "Each correct pair is 1 point."
    )
    show_prompts_popup([[p] for p in TEIL3_PROMPTS])

    if 't3_total' not in st.session_state:
        st.session_state['t3_total'] = 1
    t3_total = st.number_input(
        "How many requests do you want to practice?", 1, len(TEIL3_PROMPTS), st.session_state['t3_total']
    )
    st.session_state['t3_total'] = t3_total

    if st.button("Start new Teil 3 session"):
        for k in ['t3_idxs', 't3_idx', 't3_score', 't3_history']:
            st.session_state.pop(k, None)
        rerun()
        return

    if 't3_idxs' not in st.session_state:
        st.session_state['t3_idxs'] = random.sample(range(len(TEIL3_PROMPTS)), t3_total)
        st.session_state['t3_idx'] = 0
        st.session_state['t3_score'] = 0
        st.session_state['t3_history'] = []

    idx = st.session_state['t3_idx']
    if idx < t3_total:
        i = st.session_state['t3_idxs'][idx]
        prompt = TEIL3_PROMPTS[i]
        st.subheader(f"Request {idx + 1} of {t3_total}")
        st.write(f"**Prompt:** {prompt}")
        req = st.text_input("Your request (must end with '?')", key=f"req3_{idx}")
        rep = st.text_input("Your reply (must end with '.')", key=f"rep3_{idx}")

        if st.button("Submit Request & Reply", key=f"submit3_{idx}"):
            if not req.strip().endswith("?"):
                ok_req, msg_req = False, "Request must end with a question mark (?)"
            else:
                ok_req, msg_req = grammar_feedback(req)
            if not rep.strip().endswith("."):
                ok_rep, msg_rep = False, "Reply must end with a period (.)"
            else:
                ok_rep, msg_rep = grammar_feedback(rep)
            sc = 1 if (ok_req and ok_rep) else 0
            st.session_state['t3_score'] += sc
            st.session_state['t3_history'].append({
                "Prompt": prompt, "Request": req, "Reply": rep, "Correct": sc,
                "Request Feedback": msg_req, "Reply Feedback": msg_rep
            })
            if sc:
                st.success("Correct! Well done.")
            else:
                if not ok_req:
                    st.error(f"Request error: {msg_req}")
                if not ok_rep:
                    st.error(f"Reply error: {msg_rep}")
            st.session_state['t3_idx'] += 1
            rerun()
            return
    else:
        st.success(f"Your score: {st.session_state['t3_score']} out of {t3_total} in Teil 3.")
        df = pd.DataFrame(st.session_state['t3_history'])
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download results as CSV", csv, "Teil3_results.csv")
        if st.button("Restart Teil 3"):
            for k in ['t3_idxs', 't3_idx', 't3_score', 't3_history']:
                st.session_state.pop(k, None)
            rerun()
            return

# ---- Main App ----
def main():
    st.title(f"A1 Sprechen – {SCHOOL_NAME}")
    login_main()
    st.markdown("---")
    part = st.radio("Choose a section:", ["Teil 1", "Teil 2", "Teil 3"], horizontal=True)
    if part == "Teil 1":
        teil1()
    elif part == "Teil 2":
        teil2()
    elif part == "Teil 3":
        teil3()

    # ---- Show total summary and score if any parts done ----
    show_score = False
    scores = []
    if st.session_state.get("teil1_score") is not None:
        scores.append(st.session_state.get("teil1_score"))
        show_score = True
    if st.session_state.get("t2_score") is not None:
        scores.append(st.session_state.get("t2_score"))
        show_score = True
    if st.session_state.get("t3_score") is not None:
        scores.append(st.session_state.get("t3_score"))
        show_score = True

    if show_score:
        total = sum(scores)
        st.markdown("---")
        st.info(
            f"**Total Score so far:** {total} "
            f"(Teil 1: {st.session_state.get('teil1_score',0)}, "
            f"Teil 2: {st.session_state.get('t2_score',0)}, "
            f"Teil 3: {st.session_state.get('t3_score',0)})"
        )

if __name__ == "__main__":
    main()
