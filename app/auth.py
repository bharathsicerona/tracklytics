"""
auth.py
-------
Session management and authentication utilities.

Sessions:
  - A signed cookie (itsdangerous) stores the logged-in user's ID.
  - Cookies are valid for 30 days (SESSION_MAX_AGE).
  - Tampering with the cookie value invalidates the session.

Password hashing:
  - bcrypt via passlib. Passwords are never stored in plain text.

Helper functions used by all routers:
  - get_user_id(request)   → Optional[int]
  - get_current_user(request) → Optional[sqlite3.Row]
  - require_user(request)  → redirects to /login if not authenticated
"""

from typing import Optional

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from passlib.context import CryptContext
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.config import SECRET_KEY, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from app.database import get_connection

# Bcrypt context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Serializer for signing/verifying session cookies
_serializer = URLSafeTimedSerializer(SECRET_KEY)


# ── PASSWORD UTILITIES ───────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    return pwd_context.verify(plain, hashed)


# ── SESSION UTILITIES ────────────────────────────────────────

def create_session_token(user_id: int) -> str:
    """Create a signed token encoding the user_id. Stored in a cookie."""
    return _serializer.dumps(user_id)


def get_user_id(request: Request) -> Optional[int]:
    """
    Read and verify the session cookie.
    Returns the user_id if valid and not expired, otherwise None.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    try:
        return _serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def get_current_user(request: Request):
    """
    Fetch the full user row for the logged-in user.
    Returns None if the session is missing or invalid.
    """
    user_id = get_user_id(request)
    if not user_id:
        return None
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, email, must_change_password, is_admin FROM user WHERE id = ?",
            (user_id,)
        )
        return cur.fetchone()
    finally:
        conn.close()


def require_user(request: Request):
    """
    Returns the current user or redirects to /login.
    Use at the top of any route that requires authentication.

    Usage:
        user = require_user(request)
        if isinstance(user, RedirectResponse):
            return user
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    # Force password change on first login
    if user["must_change_password"] and request.url.path != "/set-password":
        return RedirectResponse("/set-password", status_code=302)
    return user
