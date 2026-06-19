"""
main.py
-------
FastAPI application entry point for Tracklytics.

Auth middleware intercepts every request. Public paths (/login, /set-password,
/static) are exempt. All other routes require a valid session cookie.

Routers registered:
  /           → dashboard
  /habits     → routers/habits.py
  /learning   → routers/learning.py
  /projects   → routers/projects.py
  /history    → routers/history.py
  /admin      → routers/admin.py
  /login      → routers/auth_router.py
  /logout     → routers/auth_router.py
  /set-password → routers/auth_router.py

Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import date, timedelta

from app.routers import habits, learning, projects, auth_router, admin, history
from app.database import get_connection
from app.auth import get_user_id, get_current_user

app = FastAPI(title="Tracklytics")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ── AUTH MIDDLEWARE ──────────────────────────────────────────────────────────
# Paths that don't require a login
PUBLIC_PATHS = {"/login", "/set-password"}

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Redirect unauthenticated users to /login for all non-public routes.
    Static files are always allowed through.
    """
    path = request.url.path
    if path.startswith("/static") or path in PUBLIC_PATHS:
        return await call_next(request)
    if not get_user_id(request):
        return RedirectResponse("/login", status_code=302)
    return await call_next(request)

# ── ROUTERS ──────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(admin.router)
app.include_router(history.router)
app.include_router(habits.router,   prefix="/habits",   tags=["habits"])
app.include_router(learning.router, prefix="/learning", tags=["learning"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])


# ── DASHBOARD ────────────────────────────────────────────────────────────────
@app.get("/")
def dashboard(request: Request):
    """
    Main dashboard — aggregated summary for the logged-in user.
    Shows today's habits, last-7-day stats, this week's learning and project time.
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    today      = date.today()
    today_str  = str(today)
    week_start = str(today - timedelta(days=today.weekday()))
    seven_ago  = str(today - timedelta(days=6))

    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT h.id, h.name, h.icon,
                   COALESCE(hl.completed, 0) AS completed
            FROM habit h
            LEFT JOIN habit_log hl ON hl.habit_id = h.id AND hl.log_date = ?
            WHERE h.is_active = 1 AND h.user_id = ?
            ORDER BY h.id
        """, (today_str, user["id"]))
        today_habits = cur.fetchall()

        cur.execute("""
            SELECT h.name,
                   SUM(CASE WHEN hl.completed = 1 THEN 1 ELSE 0 END) AS completed_days
            FROM habit h
            LEFT JOIN habit_log hl ON hl.habit_id = h.id AND hl.log_date >= ?
            WHERE h.is_active = 1 AND h.user_id = ?
            GROUP BY h.id, h.name
            ORDER BY completed_days DESC
        """, (seven_ago, user["id"]))
        habit_stats = cur.fetchall()

        cur.execute("""
            SELECT lg.name,
                   COALESCE(SUM(CASE WHEN ls.session_date >= ? THEN ls.duration_minutes ELSE 0 END), 0) AS minutes_this_week,
                   lg.target_minutes_per_week
            FROM learning_goal lg
            LEFT JOIN learning_session ls ON ls.goal_id = lg.id
            WHERE lg.is_active = 1 AND lg.user_id = ?
            GROUP BY lg.id, lg.name, lg.target_minutes_per_week
            ORDER BY lg.name
        """, (week_start, user["id"]))
        learning_stats = cur.fetchall()

        cur.execute("""
            SELECT p.name,
                   COALESCE(SUM(CASE WHEN ps.session_date >= ? THEN ps.duration_minutes ELSE 0 END), 0) AS minutes_this_week
            FROM project p
            LEFT JOIN project_session ps ON ps.project_id = p.id
            WHERE p.status = 'active' AND p.user_id = ?
            GROUP BY p.id, p.name
            ORDER BY minutes_this_week DESC
        """, (week_start, user["id"]))
        project_stats = cur.fetchall()
    finally:
        conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request":        request,
        "user":           user,
        "today":          today.strftime("%A, %d %b %Y"),
        "today_date":     today_str,
        "today_habits":   today_habits,
        "habit_stats":    habit_stats,
        "learning_stats": learning_stats,
        "project_stats":  project_stats,
    })
