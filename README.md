# 📊 Tracklytics

A personal productivity and activity analytics platform for tracking daily habits, learning goals, and projects — with meaningful insights into consistency and progress.

Built with **FastAPI + SQLite + Jinja2**, designed to run on a home Mac and be accessible from any device via browser.

---

## Features

- **Habit Tracking** — Daily check-ins with 7-day history and completion rates
- **Learning Goals** — Track study sessions with weekly targets and progress bars
- **Project Tracking** — Log work sessions against active projects with milestones
- **History Page** — View and edit any past date's entries
- **Multi-user** — Invite-only accounts with fully isolated data per user
- **Auth** — Email + password login with 30-day sessions
- **Mobile Responsive** — Works on phone browsers with a collapsible nav
- **Remote Access** — Cloudflare Tunnel support for access anywhere

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Database | SQLite (via `sqlite3`) |
| Templates | Jinja2 |
| Frontend | HTMX + vanilla CSS |
| Auth | passlib (bcrypt) + itsdangerous (signed cookies) |
| Email | Gmail SMTP (smtplib) |
| Tunnel | Cloudflare Quick Tunnel |

---

## Project Structure

```
Tracklytics/
├── app/
│   ├── main.py              # FastAPI app, auth middleware, dashboard
│   ├── auth.py              # Session management, password hashing
│   ├── config.py            # Environment variable loading
│   ├── database.py          # SQLite connection helper
│   ├── email_utils.py       # Gmail SMTP for invite emails
│   ├── routers/
│   │   ├── auth_router.py   # /login, /logout, /set-password
│   │   ├── admin.py         # /admin — user management
│   │   ├── habits.py        # /habits — CRUD + daily toggle
│   │   ├── learning.py      # /learning — goals + sessions
│   │   ├── projects.py      # /projects — projects + sessions
│   │   └── history.py       # /history — past date view + edit
│   └── templates/           # Jinja2 HTML templates
├── static/
│   └── style.css            # All styles
├── init_db.py               # DB initialisation + admin account creation
├── schema.sql               # SQLite schema reference (docs only)
├── requirements.txt
├── .env.example
└── SETUP.md
```

---

## Getting Started

See **[SETUP.md](SETUP.md)** for full setup instructions.

Quick version:

```bash
# 1. Install dependencies
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Fill in GMAIL_ADDRESS, GMAIL_APP_PASSWORD, SECRET_KEY, ADMIN_EMAIL

# 3. Initialise database
python init_db.py

# 4. Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser.

---

## Environment Variables

| Variable | Description |
|---|---|
| `GMAIL_ADDRESS` | Gmail account for sending invite emails |
| `GMAIL_APP_PASSWORD` | 16-char Google App Password |
| `SECRET_KEY` | Random string for signing session cookies |
| `ADMIN_EMAIL` | Your email — used to create the admin account |

---

## Roadmap

**Short-term**
- [ ] Auto-start on Mac boot (LaunchAgent)

**Long-term**
- [ ] Named Cloudflare Tunnel (permanent URL)
- [ ] Analytics dashboard (streaks, charts, trends)
- [ ] Weekly digest email
- [ ] Reminders and nudges
- [ ] PWA — installable on phone home screen
- [ ] Calendar view for history

---

## License

Private project — not open for public use.
