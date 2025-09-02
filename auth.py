# auth.py
from datetime import timedelta
from flask import Blueprint, request, jsonify, make_response

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

MAX_AGE = 60 * 60 * 24 * 30  # 30 days

@auth_bp.post("/login")
def login():
    user_id = request.json.get("user_id")
    # TODO: validate user_id against your user store
    resp = make_response(jsonify({"status": "ok"}))
    resp.set_cookie(
        "session",
        user_id,
        max_age=MAX_AGE,
        httponly=True,
        secure=True,
        samesite="Strict",
    )
    return resp

@auth_bp.get("/refresh")
def refresh():
    token = request.cookies.get("session")
    if not token:
        return jsonify({"status": "missing"}), 401
    # Optionally verify the token here before resetting expiry
    resp = make_response(jsonify({"status": "refreshed"}))
    resp.set_cookie(
        "session",
        token,
        max_age=MAX_AGE,
        httponly=True,
        secure=True,
        samesite="Strict",
    )
    return resp
