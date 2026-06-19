"""
email_utils.py
--------------
Sends emails via Gmail SMTP using the app-specific password in .env.

Only one function is exposed: send_temp_password_email().
Called when Bharath creates a new user account from the admin panel.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


def send_temp_password_email(to_email: str, name: str, temp_password: str, app_url: str = ""):
    """
    Send a welcome email with a temporary password to a new user.

    Args:
        to_email:      Recipient's email address
        name:          Recipient's display name
        temp_password: Plain-text temporary password (shown once, then discarded)
        app_url:       Base URL of the app (e.g. https://tracklytics.example.com)
                       Shown in the email so the user knows where to log in.
    """
    msg = MIMEMultipart()
    msg["From"]    = f"Tracklytics <{GMAIL_ADDRESS}>"
    msg["To"]      = to_email
    msg["Subject"] = "Welcome to Tracklytics — your login details"

    login_url = f"{app_url}/login" if app_url else "/login"

    body = f"""Hi {name},

Bharath has set up a Tracklytics account for you!

Tracklytics helps you track daily habits, learning goals, and projects.

─────────────────────────────
Login:             {to_email}
Temporary password: {temp_password}
─────────────────────────────

Open the app here: {login_url}

You'll be asked to set your own password after your first login.

– Tracklytics
"""
    msg.attach(MIMEText(body, "plain"))

    # Send via Gmail SMTP over SSL (port 465)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
