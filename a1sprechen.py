import streamlit as st
import requests
import random

API_TOKEN = "itdTVpCYfsZSCxm5jGMrmneReLzkGndD"
TABLE_ID = 597466

def fetch_all_baserow_rows():
    url = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/?user_field_names=true&size=200"
    headers = {"Authorization": f"Token {API_TOKEN}"}
    all_rows = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.error(f"Error fetching from Baserow: {response.status_code} - {response.text}")
            return []
        data = response.json()
        all_rows.extend(data.get("results", []))
        url = data.get("next", None)
    return all_rows

def build_vocab_lists(rows):
    lists = {}
    for row in rows:
        lvl = row.get("Level", "Unknown")
        ger = row.get("German", "").strip()
        eng = row.get("English", "").strip()
        if not (lvl and ger and eng):
            continue
        if lvl not in lists:
            lists[lvl] = []
        lists[lvl].append((ger, eng))
    return lists

def clean_text(text):
    return text.replace('the ', '').replace(',', '').replace('.', '').strip().lower()

def vocab_trainer_tab():
    rows = fetch_all_baserow_rows()
    st.write("DEBUG: RAW ROWS", rows[:3])  # Only show a sample for debugging

    VOCAB_LISTS = build_vocab_lists(rows)
    levels = list(VOCAB_LISTS.keys()) if VOCAB_LISTS else []

    if not levels:
        st.error("No vocab levels found! Please check your Baserow data and field names.")
        return

    st.title("Vocab Trainer")
    st.info("Practice your German vocabulary by level!")

    HERR_FELIX = "Herr Felix 👨‍🏫"
    defaults = {
        "vt_history": [],
        "vt_list": [],
        "vt_index": 0,
        "vt_score": 0,
        "vt_total": None,
    }
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)

    # Choose level
    level = st.selectbox("Choose level", levels, key="vt_level")
    vocab_items = VOCAB_LISTS.get(level, [])
    max_words = len(vocab_items)

    if max_words == 0:
        st.warning(f"No vocabulary available for level {level}.")
        st.stop()

    if st.button("🔁 Start New Practice", key="vt_reset"):
        for k in defaults:
            st.session_state[k] = defaults[k]

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
                ("assistant", f"Hallo! Ich bin {HERR_FELIX}. Let's start with {count} words!")
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

if __name__ == "__main__":
    vocab_trainer_tab()
