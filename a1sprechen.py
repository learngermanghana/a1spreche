import streamlit as st
import requests
import random
from datetime import date

# ==== BASEROW CONFIG ====
API_TOKEN = "itdTVpCYfsZSCxm5jGMrmneReLzkGndD"

# Table for vocabulary
VOCAB_TABLE_ID = 597466
LEVEL_FIELD = "Level"        # field name (not ID) as Baserow returns user_field_names
GERMAN_FIELD = "German"
ENGLISH_FIELD = "English"

# Table for progress
PROGRESS_TABLE_ID = 597671
STUDENT_FIELD = "field_4838052"      # Student Code
VOCAB_FIELD = "field_4838053"        # Practiced Vocab (as CSV)
ATTEMPTED_FIELD = "field_4838054"    # Attempted (number)
CORRECT_FIELD = "field_4838057"      # Correct (number)
# Add a date field if you want to save the date as well

# ==== LOAD VOCAB FROM BASEROW ====
@st.cache_data
def load_vocab_lists_baserow():
    url = f"https://api.baserow.io/api/database/rows/table/{VOCAB_TABLE_ID}/"
    headers = {"Authorization": f"Token {API_TOKEN}"}
    params = {"user_field_names": True, "size": 200}
    rows = []
    # Paging: get all records in batches of 200
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            st.error(f"Baserow error {response.status_code}: {response.text}")
            return {}
        data = response.json()
        rows.extend(data.get("results", []))
        url = data.get("next")  # None if done
        params = {}  # only needed for the first request
    lists = {}
    for row in rows:
        lvl = row.get(LEVEL_FIELD, "Unknown")
        ger = row.get(GERMAN_FIELD, "")
        eng = row.get(ENGLISH_FIELD, "")
        if lvl and ger and eng:
            lists.setdefault(lvl, []).append((ger, eng))
    return lists

def clean_text(text):
    return text.replace('the ', '').replace(',', '').replace('.', '').strip().lower()

def save_progress_to_baserow(student_code, practiced_vocab_list, num_attempted, num_correct):
    url = f"https://api.baserow.io/api/database/rows/table/{PROGRESS_TABLE_ID}/"
    headers = {
        "Authorization": f"Token {API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        STUDENT_FIELD: student_code,
        VOCAB_FIELD: ",".join(practiced_vocab_list),
        ATTEMPTED_FIELD: num_attempted,
        CORRECT_FIELD: num_correct,
        # If you have a date field, add it here, e.g.
        # "field_xxxxxxxx": str(date.today()),
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in (200, 201):
        return True
    else:
        st.warning(f"Failed to save progress! {response.status_code}: {response.text}")
        return False

# ==== VOCAB TRAINER TAB ====
def vocab_trainer_tab():
    st.header("Vocab Trainer")

    # -- Load Vocab Lists --
    VOCAB_LISTS = load_vocab_lists_baserow()
    levels = list(VOCAB_LISTS.keys()) if VOCAB_LISTS else []

    if not levels:
        st.error("No vocab levels found! Please check your Baserow data and field IDs.")
        return

    defaults = {
        "vt_history": [],
        "vt_list": [],
        "vt_index": 0,
        "vt_score": 0,
        "vt_total": None,
        "vt_saved_to_baserow": False,
    }
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)

    # --- Level select ---
    level = st.selectbox("Choose level", levels, key="vt_level")
    vocab_items = VOCAB_LISTS.get(level, [])
    max_words = len(vocab_items)
    if max_words == 0:
        st.warning(f"No vocabulary available for level {level}. Please add entries in your Baserow table.")
        st.stop()

    if st.button("🔁 Start New Practice", key="vt_reset"):
        for k in defaults:
            st.session_state[k] = defaults[k]
        st.session_state["vt_saved_to_baserow"] = False

    st.info(f"There are {max_words} words available in {level}.")

    # Step 1: ask how many words to practice
    if st.session_state.vt_total is None:
        count = st.number_input(
            "How many words can you practice today?",
            min_value=1,
            max_value=max_words,
            value=min(7, max_words),
            key="vt_count"
        )
        if st.button("Start Practice", key="vt_start"):
            shuffled = vocab_items.copy()
            random.shuffle(shuffled)
            st.session_state.vt_list = shuffled[:int(count)]
            st.session_state.vt_total = int(count)
            st.session_state.vt_index = 0
            st.session_state.vt_score = 0
            st.session_state.vt_history = [
                ("assistant", f"Let's start with {count} words!")
            ]

    # Display chat history
    if st.session_state.vt_history:
        st.markdown("### 🗨️ Practice Chat")
        for who, message in st.session_state.vt_history:
            align = "left" if who == "assistant" else "right"
            bgcolor = "#FAFAFA" if who == "assistant" else "#D2F8D2"
            label = "Herr Felix" if who == "assistant" else "You"
            st.markdown(
                f"<div style='text-align:{align}; background:{bgcolor}; padding:10px; border-radius:8px;'>"
                f"<b>{label}:</b> {message}</div>",
                unsafe_allow_html=True
            )

    # Practice loop
    total = st.session_state.vt_total
    idx = st.session_state.vt_index
    if isinstance(total, int) and idx < total:
        word, answer = st.session_state.vt_list[idx]
        user_input = st.text_input(f"{word} = ?", key=f"vt_input_{idx}")
        if user_input and st.button("Check", key=f"vt_check_{idx}"):
            st.session_state.vt_history.append(("user", user_input))
            given = clean_text(user_input)
            correct = clean_text(answer)
            if given == correct:
                st.session_state.vt_score += 1
                fb = f"✅ Correct! '{word}' = '{answer}'"
            else:
                fb = f"❌ Not quite. '{word}' = '{answer}'"
            st.session_state.vt_history.append(("assistant", fb))
            st.session_state.vt_index += 1

    # Show results when done
    if isinstance(total, int) and idx >= total:
        score = st.session_state.vt_score
        st.markdown(f"### 🏁 Finished! You got {score}/{total} correct.")

        # Practice Again button resets everything
        if st.button("Practice Again", key="vt_again"):
            for k in defaults:
                st.session_state[k] = defaults[k]
            st.session_state["vt_saved_to_baserow"] = False

        if "vt_saved_to_baserow" not in st.session_state:
            st.session_state["vt_saved_to_baserow"] = False

        if not st.session_state["vt_saved_to_baserow"]:
            student_code = st.session_state.get("student_code", "unknown")
            practiced_vocab = [item[0] for item in st.session_state.vt_list]
            update_success = save_progress_to_baserow(
                student_code=student_code,
                practiced_vocab_list=practiced_vocab,
                num_attempted=total,
                num_correct=score
            )
            if update_success:
                st.success("✅ Your progress was saved!")
                st.session_state["vt_saved_to_baserow"] = True
            else:
                st.warning("⚠️ Progress could not be saved. Please try again later.")

# ==== MAIN APP ====
if __name__ == "__main__" or True:
    vocab_trainer_tab()
