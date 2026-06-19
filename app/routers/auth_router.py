"""
routers/auth_router.py
----------------------
Handles login, logout, and first-login password change.

Routes:
  GET  /login          – render login form
  POST /login          – verify credentials, set session cookie
  GET  /logout         – clear session cookie, redirect to /login
  GET  /set-password   – render set-new-password form (first login only)
  POST /set-password   – update password, clear must_change_password flag
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import get_connection
from app.auth import (
    verify_password, hash_password,
    create_session_token, get_current_user,
    SESSION_COOKIE_NAME, SESSION_MAX_AGE
)
from app.config import SESSION_COOKIE_NAME, SESSION_MAX_AGE

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Show login form. Redirect to dashboard if already logged in."""
    if get_current_user(request):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login(
    request:  Request,
    email:    str = Form(...),
    password: str = Form(...),
):
    """
    Verify email + password against the database.
    On success: set a signed session cookie and redirect to dashboard.
    On failure: re-render login form with an error message.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, hashed_password, must_change_password FROM user WHERE email = ?",
            (email.strip().lower(),)
        )
        user = cur.fetchone()
    finally:
        conn.close()

    if not user or not verify_password(password, user["hashed_password"]):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error":   "Invalid email or password."
        })

    # Create signed session token
    token = create_session_token(user["id"])

    # Redirect destination: force password change if first login
    redirect_to = "/set-password" if user["must_change_password"] else "/"
    response = RedirectResponse(redirect_to, status_code=302)

    # Set cookie with 30-day expiry (remember me)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,   # not accessible via JavaScript
        samesite="lax",  # CSRF protection
    )
    return response


@router.get("/logout")
def logout():
    """Clear the session cookie and redirect to login."""
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@router.get("/set-password", response_class=HTMLResponse)
def set_password_page(request: Request):
    """Show the set-new-password form. Only accessible after first login."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("set_password.html", {"request": request, "error": None})


@router.post("/set-password")
def set_password(
    request:          Request,
    new_password:     str = Form(...),
    confirm_password: str = Form(...),
):
    """
    Update the user's password and clear the must_change_password flag.
    Validates that passwords match and meet minimum length (8 chars).
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    if new_password != confirm_password:
        return templates.TemplateResponse("set_password.html", {
            "request": request,
            "error":   "Passwords do not match."
        })

    if len(new_password) < 8:
        return templates.TemplateResponse("set_password.html", {
            "request": request,
            "error":   "Password must be at least 8 characters."
        })

    conn = get_connection()
    try:
        conn.execute(
            "UPDATE user SET hashed_password = ?, must_change_password = 0 WHERE id = ?",
            (hash_password(new_password), user["id"])
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse("/", status_code=302)
