"""Authentication UI helpers for the Streamlit app."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4
from typing import Optional
import urllib.parse as _urllib
import secrets
import urllib.parse
import logging
import requests
import html  # noqa: F401

import bcrypt
import streamlit as st
from falowen.email_utils import send_reset_email, build_gas_reset_link
from falowen.sessions import create_session_token, destroy_session_token
from src.auth import persist_session_client
from src.contracts import is_contract_expired
from src.data_loading import load_student_data
from src.session_management import determine_level
from src.ui_helpers import qp_get, qp_clear
from src.services.contracts import contract_active
from src.utils.toasts import refresh_with_toast, toast_ok, toast_err


# Google OAuth configuration
GOOGLE_CLIENT_ID = st.secrets.get(
    "GOOGLE_CLIENT_ID",
    "180240695202-3v682khdfarmq9io9mp0169skl79hr8c.apps.googleusercontent.com",
)
GOOGLE_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET", "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")
REDIRECT_URI = st.secrets.get("GOOGLE_REDIRECT_URI", "https://www.falowen.app/")


def renew_session_if_needed() -> None:
    """Refresh session token and keep query parameters in sync."""
    token = st.session_state.get("session_token")
    if not token:
        return

    try:
        sess_module = __import__(
            "falowen.sessions",
            fromlist=["refresh_or_rotate_session_token", "validate_session_token"],
        )
        validate_session_token = sess_module.validate_session_token
        refresh_or_rotate_session_token = sess_module.refresh_or_rotate_session_token
        data = validate_session_token(token) or {}
        if not data:
            return
        new_token = refresh_or_rotate_session_token(token)
    except Exception:
        logging.exception("Session renewal failed")
        toast_err("Session renewal failed")
        return

    if new_token and new_token != token:
        st.session_state["session_token"] = new_token
        st.query_params["t"] = new_token
        token = new_token

    student_code = st.session_state.get("student_code") or data.get("student_code", "")
    persist_session_client(token, student_code)
    st.query_params["t"] = token


def render_signup_form() -> None:
    _renew = globals().get("renew_session_if_needed")
    if _renew:
        _renew()
    with st.form("signup_form", clear_on_submit=False):
        new_name = st.text_input("Full Name", key="ca_name")
        new_email = st.text_input(
            "Email (must match teacher’s record)",
            help="Use the school email your tutor added to the roster.",
            key="ca_email",
        ).strip().lower()
        new_code = st.text_input(
            "Student Code (from teacher)", help="Example: felixa2", key="ca_code"
        ).strip().lower()
        new_password = st.text_input("Choose a Password", type="password", key="ca_pass")
        signup_btn = st.form_submit_button("Create Account")

    if not signup_btn:
        return
    if not (new_name and new_email and new_code and new_password):
        st.error("Please fill in all fields.")
        return
    if len(new_password) < 8:
        st.error("Password must be at least 8 characters.")
        return

    df = load_student_data()
    if df is None:
        st.error("Student roster unavailable. Please try again later.")
        return
    df["StudentCode"] = df["StudentCode"].str.lower().str.strip()
    df["Email"] = df["Email"].str.lower().str.strip()
    valid = df[(df["StudentCode"] == new_code) & (df["Email"] == new_email)]
    if valid.empty:
        st.error("Your code/email aren’t registered. Use 'Request Access' first.")
        return

    doc_ref = st.session_state.get("db", None)
    if doc_ref is None:
        try:
            from falowen.sessions import get_db as _get_db
        except Exception:  # fall back to stubbed db
            from falowen.sessions import db as _db  # type: ignore

            _get_db = lambda: _db  # type: ignore
        doc_ref = _get_db()
    doc_ref = doc_ref.collection("students").document(new_code)
    if doc_ref.get().exists:
        st.error("An account with this student code already exists. Please log in instead.")
        return

    hashed_pw = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    doc_ref.set({"name": new_name, "email": new_email, "password": hashed_pw})
    st.success("Account created! Please log in on the Returning tab.")


def render_login_form(login_id: str, login_pass: str) -> bool:
    _renew = globals().get("renew_session_if_needed")
    if _renew:
        _renew()
    login_id = (login_id or "").strip().lower()
    login_pass = login_pass or ""
    if not (login_id and login_pass):
        st.error("Please enter both email and password.")
        return False

    df = load_student_data()
    if df is None:
        st.error("Student roster unavailable. Please try again later.")
        return False

    df["StudentCode"] = df["StudentCode"].str.lower().str.strip()
    df["Email"] = df["Email"].str.lower().str.strip()
    lookup = df[(df["StudentCode"] == login_id) | (df["Email"] == login_id)]
    if lookup.empty:
        st.error("No matching student code or email found.")
        return False
    if lookup.shape[0] > 1:
        st.error("Multiple matching accounts found. Please contact the office.")
        return False

    student_row = lookup.iloc[0]
    if is_contract_expired(student_row):
        st.error("Your contract has expired. Contact the office.")
        return False

    if not contract_active(student_row["StudentCode"], df):
        st.error("Outstanding balance past due. Contact the office.")
        return False

    try:
        from falowen.sessions import get_db  # avoid heavy import at module load
    except Exception:  # pragma: no cover - stubbed sessions
        from falowen.sessions import db  # type: ignore

        get_db = lambda: db  # type: ignore

    db = get_db()
    doc_ref = db.collection("students").document(student_row["StudentCode"])
    doc = doc_ref.get()
    if not doc.exists:
        st.error("Account not found. Please use 'Sign Up (Approved)' first.")
        return False

    data = doc.to_dict() or {}
    stored_pw = data.get("password", "")
    is_hash = stored_pw.startswith(("$2a$", "$2b$", "$2y$")) and len(stored_pw) >= 60

    try:
        ok = (
            bcrypt.checkpw(login_pass.encode("utf-8"), stored_pw.encode("utf-8"))
            if is_hash
            else stored_pw == login_pass
        )
        if ok and not is_hash:
            new_hash = bcrypt.hashpw(login_pass.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            doc_ref.update({"password": new_hash})
    except Exception:
        logging.exception("Password hash upgrade failed")
        toast_err("Login failed")
        ok = False

    if not ok:
        st.error("Incorrect password.")
        return False

    ua_hash = st.session_state.get("__ua_hash", "")
    prev_token = st.session_state.get("session_token", "")
    if prev_token:
        try:
            destroy_session_token(prev_token)
        except Exception:
            logging.exception("Logout warning (revoke)")
            toast_err("Logout failed")

    sess_token = create_session_token(student_row["StudentCode"], student_row["Name"], ua_hash=ua_hash)
    level = determine_level(student_row["StudentCode"], student_row)

    st.session_state.update(
        {
            "logged_in": True,
            "student_row": dict(student_row),
            "student_code": student_row["StudentCode"],
            "student_name": student_row["Name"],
            "session_token": sess_token,
            "student_level": level,
        }
    )
    st.query_params["t"] = sess_token
    persist_session_client(sess_token, student_row["StudentCode"])

    from streamlit.components.v1 import html as _html

    _html(
        f"<script>window.localStorage.setItem('falowen_token','{_urllib.quote(sess_token)}');</script>",
        height=0,
    )

    st.success(f"Welcome, {student_row['Name']}!")
    toast_ok(f"Welcome, {student_row['Name']}!")
    return True


def render_forgot_password_panel() -> None:
    _renew = globals().get("renew_session_if_needed")
    if _renew:
        _renew()
    st.markdown("##### Forgot password")
    email_for_reset = st.text_input("Registered email", key="reset_email")
    c3, c4 = st.columns([0.55, 0.45])
    with c3:
        send_btn = st.button(
            "Send reset link", key="send_reset_btn", use_container_width=True
        )
    with c4:
        back_btn = st.button(
            "Back to login", key="hide_reset_btn", use_container_width=True
        )

    if back_btn:
        st.session_state["show_reset_panel"] = False
        st.session_state["need_rerun"] = True

    if send_btn:
        if not email_for_reset:
            st.error("Please enter your email.")
        else:
            e = email_for_reset.lower().strip()
            try:
                from falowen.sessions import get_db  # local import
            except Exception:  # pragma: no cover - stubbed sessions
                from falowen.sessions import db  # type: ignore

                get_db = lambda: db  # type: ignore

            db = get_db()
            user_query = db.collection("students").where("email", "==", e).get()
            if not user_query:
                user_query = db.collection("students").where("Email", "==", e).get()
            if not user_query:
                st.error("No account found with that email.")
            else:
                token = uuid4().hex
                expires_at = datetime.now(UTC) + timedelta(hours=1)
                try:
                    reset_link = build_gas_reset_link(token)
                except Exception:
                    base_url = (
                        st.secrets.get("PUBLIC_BASE_URL", "https://falowen.app") or ""
                    ).rstrip("/")
                    reset_link = f"{base_url}/?token={_urllib.quote(token, safe='')}"
                db.collection("password_resets").document(token).set(
                    {
                        "email": e,
                        "created": datetime.now(UTC).isoformat(),
                        "expires_at": expires_at.isoformat(),
                    }
                )
                if send_reset_email(e, reset_link):
                    st.success("Reset link sent! Check your inbox (and spam).")
                else:
                    st.error("We couldn't send the email. Please try again later.")


def render_returning_login_area() -> bool:
    """Email/Password login + optional forgot-password panel. No Google button here."""
    _renew = globals().get("renew_session_if_needed")
    if _renew:
        _renew()
    with st.form("returning_login_form", clear_on_submit=False):
        st.markdown("#### Returning user login")
        login_id = st.text_input("Email or Student Code")
        login_pass = st.text_input("Password", type="password")
        c1, c2 = st.columns([0.6, 0.4])
        with c1:
            submitted = st.form_submit_button("Log in")
        with c2:
            forgot_toggle = st.form_submit_button(
                "Forgot password?", help="Reset via email"
            )

    if submitted and render_login_form(login_id, login_pass):
        return True

    if forgot_toggle:
        st.session_state["show_reset_panel"] = True

    if st.session_state.get("show_reset_panel"):
        render_forgot_password_panel()

    return False


def render_signup_request_banner() -> None:
    if not st.session_state.get("_signup_banner_css_done"):
        st.markdown(
            """
            <style>
              .inline-banner{
                background:#f5f9ff; border:1px solid rgba(30,64,175,.15);
                border-radius:12px; padding:12px 14px; margin:12px 0;
                box-shadow:0 4px 10px rgba(2,6,23,.04);
              }
              .inline-banner b{ color:#0f172a; }
              .inline-banner .note{ color:#475569; font-size:.95rem; margin-top:6px; }
              .inline-banner ul{ margin:6px 0 0 1.1rem; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state["_signup_banner_css_done"] = True

    st.markdown(
        """
        <div class="inline-banner">
          <div><b>Which option should I use?</b></div>
          <ul>
            <li><b>Sign Up (Approved):</b> For students already added by your tutor/office. Use your <b>Student Code</b> and <b>registered email</b> to create a password.</li>
            <li><b>Request Access:</b> New learner or not on the roster yet. Fill the form and we’ll set you up and email next steps.</li>
          </ul>
          <div class="note">Not sure? Choose <b>Request Access</b> — we’ll route you correctly.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _handle_google_oauth(code: str, state: str) -> None:
    df = load_student_data()
    if df is None:
        st.error("Student roster unavailable. Please try again later.")
        return
    df["Email"] = df["Email"].str.lower().str.strip()
    try:
        if st.session_state.get("_oauth_state") and state != st.session_state["_oauth_state"]:
            st.error("OAuth state mismatch. Please try again.")
            return
        if st.session_state.get("_oauth_code_redeemed") == code:
            return

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        resp = requests.post(token_url, data=data, timeout=10)
        if not resp.ok:
            st.error(f"Google login failed: {resp.status_code} {resp.text}")
            return

        token_data = resp.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        if not access_token:
            st.error("Google login failed: no access token.")
            return

        st.session_state["_oauth_code_redeemed"] = code
        st.session_state["access_token"] = access_token
        if refresh_token:
            st.session_state["refresh_token"] = refresh_token

        userinfo = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        ).json()

        email = (userinfo.get("email") or "").lower().strip()
        match = df[df["Email"] == email]
        if match.empty:
            st.error("No student account found for that Google email.")
            return

        student_row = match.iloc[0]
        if is_contract_expired(student_row):
            st.error("Your contract has expired. Contact the office.")
            return

        ua_hash = st.session_state.get("__ua_hash", "")
        prev_token = st.session_state.get("session_token", "")
        if prev_token:
            try:
                destroy_session_token(prev_token)
            except Exception:
                logging.exception("Logout warning (revoke)")
                toast_err("Logout failed")

        sess_token = create_session_token(
            student_row["StudentCode"], student_row["Name"], ua_hash=ua_hash
        )
        level = determine_level(student_row["StudentCode"], student_row)

        st.session_state.update(
            {
                "logged_in": True,
                "student_row": student_row.to_dict(),
                "student_code": student_row["StudentCode"],
                "student_name": student_row["Name"],
                "session_token": sess_token,
                "student_level": level,
            }
        )
        st.query_params["t"] = sess_token
        persist_session_client(sess_token, student_row["StudentCode"])
        from streamlit.components.v1 import html as _html

        _html(
            f"<script>window.localStorage.setItem('falowen_token','{_urllib.quote(sess_token)}');</script>",
            height=0,
        )

        qp_clear()
        st.success(f"Welcome, {student_row['Name']}!")
        refresh_with_toast("Logged in!")
        st.session_state["need_rerun"] = True

    except Exception as e:  # pragma: no cover - network errors
        logging.exception("Google OAuth error")
        st.error(f"Google OAuth error: {e}")
        toast_err("Google OAuth error")


def render_google_oauth(return_url: bool = True) -> Optional[str]:
    """Complete OAuth if ?code=... else return the Google Authorization URL."""
    def _qp_first(val):
        return val[0] if isinstance(val, list) else val

    qp = qp_get()
    code = _qp_first(qp.get("code")) if hasattr(qp, "get") else None
    state = _qp_first(qp.get("state")) if hasattr(qp, "get") else None
    if code:
        _handle_google_oauth(code, state)
        return None

    st.session_state["_oauth_state"] = secrets.token_urlsafe(24)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
        "state": st.session_state["_oauth_state"],
        "include_granted_scopes": "true",
        "access_type": "online",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return auth_url


def render_returning_login_form() -> bool:
    """Simplified returning-user login form used in tests."""
    _renew = globals().get("renew_session_if_needed")
    if _renew:
        _renew()
    with st.form("returning_login_form", clear_on_submit=False):
        login_id = st.text_input("Email or Student Code")
        login_pass = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
        forgot = st.form_submit_button("Forgot password?")
    if submitted:
        render_login_form(login_id, login_pass)
    if forgot:
        send_reset_email("test@example.com", "reset-link")
    return False


__all__ = [
    "render_signup_form",
    "render_login_form",
    "render_forgot_password_panel",
    "render_returning_login_area",
    "render_signup_request_banner",
    "render_google_oauth",
    "render_returning_login_form",
]
