from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv

from sqlalchemy.orm import Session

import os
import traceback
import secrets

from app.database import get_db
from app.models import User
from app.auth import create_access_token


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_CALLBACK_URL = os.getenv("AUTH0_CALLBACK_URL")


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Auth0 Authentication"]
)


# =========================================================
# OAUTH CONFIGURATION
# =========================================================

oauth = OAuth()

oauth.register(
    name="auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,

    server_metadata_url=(
        f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration"
    ),

    client_kwargs={
        "scope": "openid profile email"
    }
)


# =========================================================
# HELPER - VALIDATE AUTH0 CONFIG
# =========================================================

def validate_auth0_config():

    if not AUTH0_DOMAIN:
        return "AUTH0_DOMAIN is not configured"

    if not AUTH0_CLIENT_ID:
        return "AUTH0_CLIENT_ID is not configured"

    if not AUTH0_CLIENT_SECRET:
        return "AUTH0_CLIENT_SECRET is not configured"

    if not AUTH0_CALLBACK_URL:
        return "AUTH0_CALLBACK_URL is not configured"

    return None


# =========================================================
# HELPER - CREATE / UPDATE SOCIAL USER
# =========================================================

def get_or_create_social_user(
    db: Session,
    name: str,
    email: str,
    provider: str
):

    if not email:
        return None

    # -----------------------------------------------------
    # FIND USER BY EMAIL
    # -----------------------------------------------------

    user = db.query(User).filter(
        User.email == email
    ).first()

    # -----------------------------------------------------
    # EXISTING USER
    # -----------------------------------------------------

    if user:

        if name and user.username != name:

            existing_username = db.query(User).filter(
                User.username == name,
                User.id != user.id
            ).first()

            if not existing_username:

                user.username = name

        db.commit()
        db.refresh(user)

        return user

    # -----------------------------------------------------
    # CREATE USERNAME
    # -----------------------------------------------------

    base_username = (
        name.strip()
        if name
        else email.split("@")[0]
    )

    base_username = base_username.replace(
        " ",
        "_"
    )

    if len(base_username) < 3:

        base_username = (
            "user_" + base_username
        )

    base_username = base_username[:45]

    username = base_username

    counter = 1

    while db.query(User).filter(
        User.username == username
    ).first():

        username = (
            f"{base_username[:40]}_{counter}"
        )

        counter += 1

    # -----------------------------------------------------
    # RANDOM PASSWORD FOR SOCIAL USER
    # -----------------------------------------------------

    random_password = secrets.token_urlsafe(32)

    # -----------------------------------------------------
    # CREATE USER
    # -----------------------------------------------------

    user = User(
        username=username,
        email=email,
        password=random_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# =========================================================
# AUTH0 STATUS
# =========================================================

@router.get("/auth0-status")
async def auth0_status():

    return {

        "auth0_domain_configured": bool(
            AUTH0_DOMAIN
        ),

        "auth0_client_id_configured": bool(
            AUTH0_CLIENT_ID
        ),

        "auth0_client_secret_configured": bool(
            AUTH0_CLIENT_SECRET
        ),

        "auth0_callback_configured": bool(
            AUTH0_CALLBACK_URL
        ),

        "callback_url": AUTH0_CALLBACK_URL
    }


# =========================================================
# GOOGLE LOGIN
# =========================================================

@router.get("/login/google")
async def login_google(
    request: Request
):

    try:

        config_error = validate_auth0_config()

        if config_error:

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": config_error
                }
            )

        print()
        print("========================================")
        print("AUTH0 GOOGLE LOGIN")
        print("DOMAIN:", AUTH0_DOMAIN)
        print("CLIENT ID:", AUTH0_CLIENT_ID)
        print("CALLBACK:", AUTH0_CALLBACK_URL)
        print("CONNECTION: google-oauth2")
        print("========================================")

        return await oauth.auth0.authorize_redirect(
            request,
            AUTH0_CALLBACK_URL,
            connection="google-oauth2"
        )

    except Exception as e:

        print()
        print("========================================")
        print("AUTH0 GOOGLE LOGIN ERROR")
        print("ERROR:", str(e))
        traceback.print_exc()
        print("========================================")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": (
                    "Google authentication "
                    "initialization failed"
                ),
                "error": str(e)
            }
        )


# =========================================================
# FACEBOOK LOGIN
# =========================================================

@router.get("/login/facebook")
async def login_facebook(
    request: Request
):

    try:

        config_error = validate_auth0_config()

        if config_error:

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": config_error
                }
            )

        print()
        print("========================================")
        print("AUTH0 FACEBOOK LOGIN")
        print("DOMAIN:", AUTH0_DOMAIN)
        print("CLIENT ID:", AUTH0_CLIENT_ID)
        print("CALLBACK:", AUTH0_CALLBACK_URL)
        print("CONNECTION: facebook")
        print("========================================")

        return await oauth.auth0.authorize_redirect(
            request,
            AUTH0_CALLBACK_URL,
            connection="facebook"
        )

    except Exception as e:

        print()
        print("========================================")
        print("AUTH0 FACEBOOK LOGIN ERROR")
        print("ERROR:", str(e))
        traceback.print_exc()
        print("========================================")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": (
                    "Facebook authentication "
                    "initialization failed"
                ),
                "error": str(e)
            }
        )


# =========================================================
# AUTH0 CALLBACK
# =========================================================

@router.get("/callback")
async def auth_callback(
    request: Request,
    db: Session = Depends(get_db)
):

    try:

        print()
        print("========================================")
        print("AUTH0 CALLBACK RECEIVED")
        print("URL:", str(request.url))
        print("========================================")

        # -------------------------------------------------
        # AUTH0 ERROR
        # -------------------------------------------------

        auth_error = request.query_params.get(
            "error"
        )

        if auth_error:

            error_description = (
                request.query_params.get(
                    "error_description"
                )
            )

            print(
                "AUTH0 ERROR:",
                auth_error
            )

            print(
                "AUTH0 ERROR DESCRIPTION:",
                error_description
            )

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Authentication failed",
                    "error": auth_error,
                    "error_description": (
                        error_description
                    )
                }
            )

        # -------------------------------------------------
        # AUTHORIZATION CODE
        # -------------------------------------------------

        code = request.query_params.get(
            "code"
        )

        if not code:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": (
                        "Authorization code is missing"
                    )
                }
            )

        # -------------------------------------------------
        # EXCHANGE CODE FOR AUTH0 TOKEN
        # -------------------------------------------------

        print(
            "Exchanging authorization code..."
        )

        token = await oauth.auth0.authorize_access_token(
            request
        )

        print(
            "AUTH0 TOKEN RECEIVED"
        )

        # -------------------------------------------------
        # GET USERINFO
        # -------------------------------------------------

        userinfo = token.get(
            "userinfo"
        )

        if not userinfo:

            print(
                "userinfo missing from token."
            )

            try:

                userinfo = await oauth.auth0.userinfo(
                    token=token
                )

            except Exception as userinfo_error:

                print(
                    "USERINFO ERROR:",
                    str(userinfo_error)
                )

        if not userinfo:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": (
                        "Authentication details "
                        "not received from Auth0"
                    )
                }
            )

        # -------------------------------------------------
        # EXTRACT USER INFORMATION
        # -------------------------------------------------

        name = userinfo.get(
            "name"
        )

        email = userinfo.get(
            "email"
        )

        provider = userinfo.get(
            "sub"
        )

        picture = userinfo.get(
            "picture"
        )

        print()
        print("========================================")
        print("AUTH0 LOGIN SUCCESS")
        print("NAME:", name)
        print("EMAIL:", email)
        print("PROVIDER:", provider)
        print("========================================")

        # -------------------------------------------------
        # EMAIL REQUIRED
        # -------------------------------------------------

        if not email:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": (
                        "Email address was not "
                        "provided by Auth0"
                    )
                }
            )

        # -------------------------------------------------
        # CREATE / UPDATE DATABASE USER
        # -------------------------------------------------

        user = get_or_create_social_user(
            db=db,
            name=name,
            email=email,
            provider=provider
        )

        if not user:

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": (
                        "Unable to create or update "
                        "user account"
                    )
                }
            )

        # -------------------------------------------------
        # CREATE OUR APPLICATION JWT
        # -------------------------------------------------

        access_token = create_access_token(
            data={
                "sub": user.username
            }
        )

        print(
            "APPLICATION JWT CREATED"
        )

        # -------------------------------------------------
        # REDIRECT TO DASHBOARD
        #
        # Token is placed in URL fragment (#).
        # Browser does not send fragment to server.
        # dashboard.js reads it and stores it.
        # -------------------------------------------------

        dashboard_url = (
            "/static/dashboard.html"
            "#access_token="
            + access_token
        )

        print(
            "REDIRECTING TO DASHBOARD"
        )

        return RedirectResponse(
            url=dashboard_url,
            status_code=302
        )

    except Exception as e:

        print()
        print("========================================")
        print("AUTH0 CALLBACK ERROR")
        print("ERROR:", str(e))
        traceback.print_exc()
        print("========================================")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Authentication failed",
                "error": str(e)
            }
        )