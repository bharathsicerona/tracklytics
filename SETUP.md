# Tracklytics – Setup Guide (Mac, SQLite)

No database server needed. SQLite is built into Python.

## Step 1 — Set up Python environment

Open Terminal and run:

```bash
cd ~/Claude/Projects/Tracklytics

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Your terminal prompt will show `(venv)` when active.

## Step 2 — Create your .env file

```bash
cp .env.example .env
```

Then open `.env` and fill in:

| Variable | What it is |
|---|---|
| `GMAIL_ADDRESS` | Gmail account used to send invite emails (e.g. tracklyticslabs@gmail.com) |
| `GMAIL_APP_PASSWORD` | 16-char App Password from Google account settings |
| `SECRET_KEY` | Any long random string — signs session cookies |
| `ADMIN_EMAIL` | Your personal email — the admin account is created with this |

> **How to get a Gmail App Password:** Go to [myaccount.google.com](https://myaccount.google.com) → Security → 2-Step Verification → App Passwords → Create one for "Mail".

## Step 3 — Initialize the database

```bash
python init_db.py
```

This creates `tracklytics.db` and prompts you to name the admin account.
You should see: `✅ Database ready! Add your habits, goals, and projects from the app.`

**Note:** Safe to re-run — existing data is not overwritten.

## Step 4 — Run the app

**Local only (just you):**
```bash
uvicorn app.main:app --reload
```
Open: **http://localhost:8000**

**WiFi / friends on same network:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0
```
Share your Mac's local IP — e.g. **http://192.168.1.10:8000**
(Find your IP: System Settings → Wi-Fi → Details)

---

Every time you want to run the app, use the startup scripts instead of typing the full command:

```bash
# Local access only (you + same WiFi)
bash ~/Claude/Projects/Tracklytics/start.sh

# With public tunnel (friends anywhere)
bash ~/Claude/Projects/Tracklytics/start_public.sh
```

`start_public.sh` starts both the app and the Cloudflare tunnel in one go. Press Ctrl+C to stop both.

---

## Step 5 — Share with friends anywhere (Cloudflare Quick Tunnel)

Friends in other cities can access the app via a free public URL using Cloudflare's quick tunnel. No account needed.

### One-time install

```bash
brew install cloudflared
```

### Every time you want to share

Open **two** Terminal windows:

**Window 1 — run the app:**
```bash
cd ~/Claude/Projects/Tracklytics
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Window 2 — start the tunnel:**
```bash
cloudflared tunnel --url http://localhost:8000
```

After a few seconds you'll see a line like:
```
Your quick Tunnel has been created! Visit it at:
https://random-words-here.trycloudflare.com
```

Share that URL with your friends. They can open it on any phone or browser.

> **Note:** The URL changes every time you restart the tunnel. For a permanent URL, a named Cloudflare tunnel is on the long-term roadmap.

---

## Multi-user

- You are the admin. Add friends from the **Admin** page inside the app.
- A temporary password is emailed to them automatically.
- They set their own password on first login.
- Each user's data is fully separate — habits, goals, and projects are never shared.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python3: command not found` | Install from python.org or run `brew install python@3.11` |
| `ModuleNotFoundError` | Make sure `(venv)` is active — run `source venv/bin/activate` |
| Port 8000 in use | Run `uvicorn app.main:app --reload --port 8001` |
| Email not sending | Check `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` in `.env`. Make sure 2FA is on in Google account. |
| Tunnel URL not appearing | Wait 10–15 seconds after running the cloudflared command |
