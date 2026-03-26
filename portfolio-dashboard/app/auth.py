"""
OAuth Google + gestion de sessions.
Chaque utilisateur a sa propre session isolée.
"""

import os
import json
import functools
from flask import Blueprint, redirect, url_for, session, request, jsonify, current_app
from authlib.integrations.flask_client import OAuth

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
oauth = OAuth()

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")


def init_oauth(app):
    """Initialise OAuth avec l'app Flask."""
    oauth.init_app(app)
    if GOOGLE_CLIENT_ID:
        oauth.register(
            name="google",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )


def login_required(f):
    """Décorateur: bloque si pas authentifié (sauf si OAuth pas configuré)."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # Si OAuth pas configuré, on laisse passer (mode dev/solo)
        if not GOOGLE_CLIENT_ID:
            return f(*args, **kwargs)
        if "user" not in session:
            return jsonify({"error": "Non authentifié", "login_url": "/auth/login"}), 401
        return f(*args, **kwargs)
    return decorated


def get_current_user() -> dict:
    """Retourne l'utilisateur courant (ou None si pas configuré)."""
    return session.get("user")


# ─── Routes OAuth ─────────────────────────────────────────

@auth_bp.route("/login")
def login():
    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "OAuth non configuré. Mode solo actif."})
    redirect_uri = url_for("auth.callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/callback")
def callback():
    if not GOOGLE_CLIENT_ID:
        return redirect("/")
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")
    if userinfo:
        session["user"] = {
            "email": userinfo.get("email"),
            "name": userinfo.get("name"),
            "picture": userinfo.get("picture"),
            "sub": userinfo.get("sub"),  # Google unique ID
        }
    return redirect("/")


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


@auth_bp.route("/me")
def me():
    user = get_current_user()
    if user:
        return jsonify({"authenticated": True, "user": user})
    return jsonify({"authenticated": False, "oauth_configured": bool(GOOGLE_CLIENT_ID)})
