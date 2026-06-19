"""
config.py
---------
Loads environment variables from .env at the project root.
All sensitive credentials (Gmail, secret key) live in .env only — never in code.
"""

import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SECRET_KEY         = os.getenv("SECRET_KEY", "change-me-in-production")
ADMIN_EMAIL        = os.getenv("ADMIN_EMAIL")

# Session cookie settings
SESSION_COOKIE_NAME = "tracklytics_session"
SESSION_MAX_AGE     = 30 * 24 * 60 * 60  # 30 days in seconds
