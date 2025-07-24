GOOGLE_SHEET_CSV = "https://docs.google.com/spreadsheets/d/12NXf5FeVHr7JJT47mRHh7Jp-TC1yhPS7ZG6nzZVTt1U/gviz/tq?tqx=out:csv"

@st.cache_data
def load_student_data():
    # 1) Fetch CSV
    try:
        resp = requests.get(GOOGLE_SHEET_CSV, timeout=10)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text), dtype=str)
    except Exception:
        st.error("❌ Could not load student data.")
        st.stop()

    # 2) Strip whitespace
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    # 3) Drop rows missing a ContractEnd
    df = df[df["ContractEnd"].notna() & (df["ContractEnd"] != "")]

    # 4) Parse ContractEnd into datetime (two formats)
    df["ContractEnd_dt"] = pd.to_datetime(
        df["ContractEnd"], format="%m/%d/%Y", errors="coerce", dayfirst=False
    )
    # Fallback European format where needed
    mask = df["ContractEnd_dt"].isna()
    df.loc[mask, "ContractEnd_dt"] = pd.to_datetime(
        df.loc[mask, "ContractEnd"], format="%d/%m/%Y", errors="coerce", dayfirst=True
    )

    # 5) Sort by latest ContractEnd_dt and drop duplicates
    df = df.sort_values("ContractEnd_dt", ascending=False)
    df = df.drop_duplicates(subset=["StudentCode"], keep="first")

    # 6) Clean up helper column
    df = df.drop(columns=["ContractEnd_dt"])

    return df

def is_contract_expired(row):
    expiry_str = str(row.get("ContractEnd", "")).strip()
    # Debug lines removed

    if not expiry_str or expiry_str.lower() == "nan":
        return True

    # Try known formats
    expiry_date = None
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            expiry_date = datetime.strptime(expiry_str, fmt)
            break
        except ValueError:
            continue

    # Fallback to pandas auto-parse
    if expiry_date is None:
        parsed = pd.to_datetime(expiry_str, errors="coerce")
        if pd.isnull(parsed):
            return True
        expiry_date = parsed.to_pydatetime()

    today = datetime.now().date()
    # Debug lines removed

    return expiry_date.date() < today


# ---- Cookie & Session Setup ----
COOKIE_SECRET = os.getenv("COOKIE_SECRET") or st.secrets.get("COOKIE_SECRET")
if not COOKIE_SECRET:
    raise ValueError("COOKIE_SECRET environment variable not set")

cookie_manager = EncryptedCookieManager(prefix="falowen_", password=COOKIE_SECRET)
cookie_manager.ready()
if not cookie_manager.ready():
    st.warning("Cookies are not ready. Please refresh.")
    st.stop()

for key, default in [("logged_in", False), ("student_row", None), ("student_code", ""), ("student_name", "")]:
    st.session_state.setdefault(key, default)

code_from_cookie = cookie_manager.get("student_code") or ""
code_from_cookie = str(code_from_cookie).strip().lower()

# --- Auto-login via Cookie ---
if not st.session_state["logged_in"] and code_from_cookie:
    df_students = load_student_data()
    # Normalize for matching
    df_students["StudentCode"] = df_students["StudentCode"].str.lower().str.strip()
    df_students["Email"] = df_students["Email"].str.lower().str.strip()

    found = df_students[df_students["StudentCode"] == code_from_cookie]
    if not found.empty:
        student_row = found.iloc[0]
        if is_contract_expired(student_row):
            st.error("Your contract has expired. Please contact the office for renewal.")
            cookie_manager["student_code"] = ""
            cookie_manager.save()
            st.stop()
        st.session_state.update({
            "logged_in": True,
            "student_row": student_row.to_dict(),
            "student_code": student_row["StudentCode"],
            "student_name": student_row["Name"]
        })

# --- Manual Login Form ---
if not st.session_state["logged_in"]:
    st.title("🔑 Student Login")
    login_input = st.text_input("Enter your Student Code or Email:", value=code_from_cookie).strip().lower()
    if st.button("Login"):
        df_students = load_student_data()
        df_students["StudentCode"] = df_students["StudentCode"].str.lower().str.strip()
        df_students["Email"]       = df_students["Email"].str.lower().str.strip()

        found = df_students[
            (df_students["StudentCode"] == login_input) |
            (df_students["Email"]       == login_input)
        ]
        if not found.empty:
            student_row = found.iloc[0]
            # Debug: show what we're checking
            st.write("DEBUG: raw ContractEnd for login:", repr(student_row["ContractEnd"]))
            if is_contract_expired(student_row):
                st.error("Your contract has expired. Please contact the office for renewal.")
                st.stop()
            st.session_state.update({
                "logged_in": True,
                "student_row": student_row.to_dict(),
                "student_code": student_row["StudentCode"],
                "student_name": student_row["Name"]
            })
            cookie_manager["student_code"] = student_row["StudentCode"]
            cookie_manager.save()
            st.success(f"Welcome, {student_row['Name']}! 🎉")
            st.rerun()
        else:
            st.error("Login failed. Please check your Student Code or Email.")

    # --- Add extra info for students below the login box ---
    st.markdown(
        """
        <div style='text-align:center; margin-top:20px; margin-bottom:12px;'>
            <span style='color:#ff9800;font-weight:600;'>
                🔒 <b>Data Privacy:</b> Your login details and activity are never shared. Only your teacher can see your learning progress.
            </span>
            <br>
            <span style='color:#1976d2;'>
                🆕 <b>Update:</b> New features have been added to help you prepare for your German exam! Practice as often as you want, within your daily quota.
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.stop()


# --- Logged In UI ---
st.write(f"👋 Welcome, **{st.session_state['student_name']}**")
if st.button("Log out"):
    cookie_manager["student_code"] = ""
    cookie_manager.save()
    for k in ["logged_in", "student_row", "student_code", "student_name"]:
        st.session_state[k] = False if k == "logged_in" else ""
    st.success("You have been logged out.")
    st.rerun()


# ======= Data Loading Functions =======
@st.cache_data
def load_student_data():
    SHEET_ID = "12NXf5FeVHr7JJT47mRHh7Jp-TC1yhPS7ZG6nzZVTt1U"
    SHEET_NAME = "Sheet1"
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip().str.replace(" ", "")
    return df

@st.cache_data
def load_stats_data():
    SHEET_ID = "1BRb8p3Rq0VpFCLSwL4eS9tSgXBo9hSWzfW_J_7W36NQ"
    SHEET_NAME = "Sheet1"
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    df = pd.read_csv(csv_url)
    # Clean columns for easier access
    df.columns = df.columns.str.strip().str.lower()
    return df

@st.cache_data
def load_reviews():
    SHEET_ID   = "137HANmV9jmMWJEdcA1klqGiP8nYihkDugcIbA-2V1Wc"
    SHEET_NAME = "Sheet1"
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    )
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip().str.lower()
    return df

import time
import matplotlib.pyplot as plt

# ======= Dashboard Code =======
# ======= Dashboard Code =======
if st.session_state.get("logged_in"):
    student_code = st.session_state.get("student_code", "").strip().lower()
    student_name = st.session_state.get("student_name", "")

    tab = st.radio(
        "How do you want to practice?",
        [
            "Dashboard",
            "Course Book",
            "My Results and Resources",
            "Exams Mode & Custom Chat",
            "Vocab Trainer",
            "Schreiben Trainer",
        ],
        key="main_tab_select"
    )

    if tab == "Dashboard":
        # 🏠 Compact Dashboard header
        st.markdown(
            '''
            <div style="
                padding: 8px 12px;
                background: #343a40;
                color: #ffffff;
                border-radius: 6px;
                text-align: center;
                margin-bottom: 8px;
                font-size: 1.3rem;
            ">
                📊 Student Dashboard
            </div>
            ''',
            unsafe_allow_html=True
        )
        st.divider()

        # --- Get student_row first ---
        df_students = load_student_data()
        matches = df_students[df_students["StudentCode"].str.lower() == student_code]
        student_row = matches.iloc[0].to_dict() if not matches.empty else {}

        display_name = student_row.get('Name') or student_name or "Student"
        first_name = str(display_name).strip().split()[0].title() if display_name else "Student"

        # --- Minimal, super-visible greeting for mobile ---
        st.success(f"Hello, {first_name}! 👋")
        st.info("Great to see you. Let's keep learning!")

        # --- Student Info & Balance ---
        st.markdown(f"### 👤 {student_row.get('Name','')}")
        st.markdown(
            f"- **Level:** {student_row.get('Level','')}\n"
            f"- **Code:** `{student_row.get('StudentCode','')}`\n"
            f"- **Email:** {student_row.get('Email','')}\n"
            f"- **Phone:** {student_row.get('Phone','')}\n"
            f"- **Location:** {student_row.get('Location','')}\n"
            f"- **Contract:** {student_row.get('ContractStart','')} ➔ {student_row.get('ContractEnd','')}\n"
            f"- **Enroll Date:** {student_row.get('EnrollDate','')}\n"
            f"- **Status:** {student_row.get('Status','')}"
        )
        try:
            bal = float(student_row.get("Balance", 0))
            if bal > 0:
                st.warning(f"💸 Balance to pay: ₵{bal:.2f}")
        except:
            pass

        # --- Announcements & Ads (auto-rotating, reduced size) ---
        st.markdown("### 🖼️ Announcements & Ads")
        ad_images = [
            "https://i.imgur.com/IjZl191.png",
            "https://i.imgur.com/2PzOOvn.jpg",
            "https://i.imgur.com/Q9mpvRY.jpg",
        ]
        ad_captions = [
            "New A2 Classes—Limited Seats!",
            "New B1 Classes—Limited Seats!",
            "Join our classes live in person or online!",
        ]
        if "ad_idx" not in st.session_state:
            st.session_state["ad_idx"] = 0
            st.session_state["ad_last_time"] = time.time()

        ROTATE_AD_SEC = 6
        now = time.time()
        if now - st.session_state["ad_last_time"] > ROTATE_AD_SEC:
            st.session_state["ad_idx"] = (st.session_state["ad_idx"] + 1) % len(ad_images)
            st.session_state["ad_last_time"] = now
            st.rerun()

        idx = st.session_state["ad_idx"]
        st.image(ad_images[idx], caption=ad_captions[idx], width=400)  # change width if needed

        # --- Simple Goethe Exam Section ---
        with st.expander("📅 Goethe Exam Dates & Fees", expanded=True):
            st.markdown(
                """
| Level | Date       | Fee (GHS) |
|-------|------------|-----------|
| A1    | 21.07.25   | 2,850     |
| A2    | 22.07.25   | 2,400     |
| B1    | 23.07.25   | 2,750     |
| B2    | 24.07.25   | 2,500     |
| C1    | 25.07.25   | 2,450     |

- [Register here](https://www.goethe.de/ins/gh/en/spr/prf/anm.html)
- After paying, send proof to registrations-accra@goethe.de
- Pay by Mobile Money or Ecobank (use your full name as reference)
                """,
                unsafe_allow_html=True
            )

        # --- Auto-Rotating Student Reviews ---
        st.markdown("### 🗣️ What Our Students Say")
        reviews = load_reviews()
        if reviews.empty:
            st.info("No reviews yet. Be the first to share your experience!")
        else:
            rev_list = reviews.to_dict("records")
            if "rev_idx" not in st.session_state:
                st.session_state["rev_idx"] = 0
                st.session_state["rev_last_time"] = time.time()

            ROTATE_REV_SEC = 8
            now = time.time()
            if now - st.session_state["rev_last_time"] > ROTATE_REV_SEC:
                st.session_state["rev_idx"] = (st.session_state["rev_idx"] + 1) % len(rev_list)
                st.session_state["rev_last_time"] = now
                st.rerun()

            r = rev_list[st.session_state["rev_idx"]]
            stars = "★" * int(r.get("rating", 5)) + "☆" * (5 - int(r.get("rating", 5)))
            st.markdown(
                f"> {r.get('review_text','')}\n"
                f"> — **{r.get('student_name','')}**  \n"
                f"> {stars}"
            )

