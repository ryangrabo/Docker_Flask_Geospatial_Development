# auth.py
import os
import uuid
import msal
from flask import Blueprint, session, redirect, url_for, request
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

auth_bp = Blueprint("auth", __name__)

CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/getAToken"
SCOPE = []

def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )

def _build_auth_url(scopes=None, state=None):
    msal_app = _build_msal_app()
    return msal_app.get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=url_for("auth.getAToken", _external=True)
    )

@auth_bp.route("/login")
def login():
    # Save state in session to mitigate CSRF attacks
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=SCOPE, state=session["state"])
    return redirect(auth_url)

@auth_bp.route(REDIRECT_PATH)
def getAToken():
    # Verify state to protect against CSRF
    if request.args.get("state") != session.get("state"):
        return redirect(url_for("main.index"))
    
    # Handle error returned by Azure
    if "error" in request.args:
        error_desc = request.args.get("error_description", "No description provided")
        return f"Authentication error: {error_desc}"
    
    # Exchange the auth code for tokens if provided
    if "code" in request.args:
        msal_app = _build_msal_app()
        result = msal_app.acquire_token_by_authorization_code(
            request.args["code"],
            scopes=SCOPE,
            redirect_uri=url_for("auth.getAToken", _external=True)
        )
        if "id_token_claims" in result:
            session["user"] = result["id_token_claims"]
    return redirect(url_for("main.index"))

@auth_bp.route("/logout")
def logout():
    # Clear session and redirect to Azure's logout endpoint
    session.clear()
    logout_url = f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={url_for('main.index', _external=True)}"
    return redirect(logout_url)
