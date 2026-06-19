"""
routers/admin.py
----------------
Admin panel — accessible only to users with is_admin=1 (Bharath).

Routes:
  GET  /admin       – render admin panel (list of users)
  POST /admin/create-user – create a new user account and email temp password
  POST /admin/delete-user/{id} – delete a user and all their data
"""

import random
import string

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import get_connection
from app.auth import require_user, hash_password
from app.email_utils import send_temp_password_email

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _generate_temp_password(length: int = 10) -> str:
    """Generate a readable random temporary password (letters + digits, no ambiguous chars)."""
    chars = string.ascii_letters + string.digits
    # Remove visually ambiguous characters
    chars = chars.translate(str.maketrans("", "", "0OIl1"))
    return "".join(random.choices(chars, k=length))


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    """
    Render the admin panel.
    Only accessible to admin users — others are redirected to dashboard.
    """
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    if not user["is_admin"]:
        return RedirectResponse("/", status_code=302)

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, email, must_change_password, is_admin, created_at FROM user ORDER BY created_at"
        )
        users = cur.fetchall()
    finally:
        conn.close()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user":    user,
        "users":   users,
        "message": None,
        "error":   None,
    })


@router.post("/admin/create-user")
def create_user(
    request: Request,
    name:    str = Form(...),
    email:   str = Form(...),
):
    """
    Create a new user account and email them a temporary password.

    Steps:
      1. Check email is not already registered
      2. Generate a random 10-char temp password
      3. Hash and store it with must_change_password=1
      4. Send welcome email with the temp password
    """
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    if not user["is_admin"]:
        return RedirectResponse("/", status_code=302)

    email = email.strip().lower()
    name  = name.strip()

    conn = get_connection()
    try:
        # Check if email already exists
        cur = conn.cursor()
        cur.execute("SELECT id FROM user WHERE email = ?", (email,))
        if cur.fetchone():
            users = conn.execute(
                "SELECT id, name, email, must_change_password, is_admin, created_at FROM user ORDER BY created_at"
            ).fetchall()
            return templates.TemplateResponse("admin.html", {
                "request": request,
                "user":    user,
                "users":   users,
                "message": None,
                "error":   f"{email} is already registered.",
            })

        # Generate temp password and create account
        temp_password = _generate_temp_password()
        conn.execute(
            "INSERT INTO user (name, email, hashed_password, must_change_password) VALUES (?, ?, ?, 1)",
            (name, email, hash_password(temp_password))
        )
        conn.commit()
    finally:
        conn.close()

    # Send welcome email — if it fails, the account is still created
    try:
        app_url = str(request.base_url).rstrip("/")
        send_temp_password_email(email, name, temp_password, app_url)
        message = f"Account created for {name} ({email}). Welcome email sent!"
    except Exception as e:
        message = f"Account created for {name} ({email}). Email failed — share password manually: {temp_password}"

    conn = get_connection()
    try:
        users = conn.execute(
            "SELECT id, name, email, must_change_password, is_admin, created_at FROM user ORDER BY created_at"
        ).fetchall()
    finally:
        conn.close()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user":    user,
        "users":   users,
        "message": message,
        "error":   None,
    })


@router.post("/admin/delete-user/{user_id}")
def delete_user(request: Request, user_id: int):
    """
    Delete a user account and all their data (habits, goals, projects, sessions).
    Admin cannot delete their own account.
    """
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    if not user["is_admin"]:
        return RedirectResponse("/", status_code=302)
    if user["id"] == user_id:
        return RedirectResponse("/admin", status_code=302)  # can't delete self

    conn = get_connection()
    try:
        conn.execute("DELETE FROM user WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse("/admin", status_code=302)
