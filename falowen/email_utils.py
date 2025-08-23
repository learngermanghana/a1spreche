"""Email utilities for Falowen."""

import smtplib
import urllib.parse as _urllib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st

EMAIL_ADDRESS = st.secrets.get("SMTP_FROM", "learngermanghana@gmail.com")
EMAIL_PASSWORD = st.secrets.get("SMTP_PASSWORD", "mwxlxvvtnrcxqdml")


def send_reset_email(to_email: str, reset_link: str) -> bool:
    """Send a password reset email.

    Returns True on success, False otherwise.
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = "Falowen Password Reset"

        html = f"""
        <p>Hello,</p>
        <p>You requested to reset your password. Click below to continue:</p>
        <p><a href=\"{reset_link}\">{reset_link}</a></p>
        <p>This link will expire in 1 hour.</p>
        <br>
        <p>– Falowen Team</p>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, [to_email], msg.as_string())
        return True
    except Exception as e:  # pragma: no cover - streamlit UI feedback
        st.error(f"❌ Failed to send reset email: {e}")
        return False


GAS_RESET_URL = st.secrets.get(
    "GAS_RESET_URL",
    "https://script.google.com/macros/s/AKfycbwdgYJtya39qzBZaXdUqkk1i2_LIHna5CN-lHYveq7O1yG46KghKZWKNKqGYlh_xyZU/exec?token=<THE_TOKEN>",
)


def build_gas_reset_link(token: str) -> str:
    """Build a valid Apps Script reset link with ?token= support."""
    url = GAS_RESET_URL.strip()
    if "<THE_TOKEN>" in url:
        return url.replace("<THE_TOKEN>", _urllib.quote(token, safe=""))

    parts = _urllib.urlparse(url)
    qs = dict(_urllib.parse_qsl(parts.query, keep_blank_values=True))
    qs["token"] = token
    new_query = _urllib.urlencode(qs, doseq=True)
    return _urllib.urlunparse(parts._replace(query=new_query))
