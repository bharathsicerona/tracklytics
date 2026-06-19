"""
routers/history.py
------------------
History page — view and edit any past date's data.

Routes:
  GET /history          – render history page for a given date (defaults to today)
  POST /history/toggle  – toggle a habit for the selected date
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from app.database import get_connection
from app.auth import require_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request, date: str = None):
    """
    Render a full-day view for any date.

    Query param: ?date=YYYY-MM-DD  (defaults to today if omitted)

    Fetches:
      - All active habits with completion status for that date
      - All learning sessions logged for that date
      - All project sessions logged for that date
    Allows toggling habits and editing/deleting sessions inline.
    """
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user

    # Default to today if no date param
    selected_date = date or str(__import__('datetime').date.today())

    conn = get_connection()
    try:
        cur = conn.cursor()

        # Habits — all active, with completion status for selected date
        cur.execute("""
            SELECT h.id, h.name, h.icon, h.category,
                   date(h.created_at) AS start_date,
                   COALESCE(hl.completed, 0) AS completed,
                   hl.notes AS log_notes
            FROM habit h
            LEFT JOIN habit_log hl ON hl.habit_id = h.id AND hl.log_date = ?
            WHERE h.is_active = 1 AND h.user_id = ?
            ORDER BY h.created_at
        """, (selected_date, user["id"]))
        habits = cur.fetchall()

        # Learning sessions for this date
        cur.execute("""
            SELECT ls.id, lg.name AS goal_name, lg.id AS goal_id,
                   ls.duration_minutes, ls.topic, ls.notes, ls.session_date
            FROM learning_session ls
            JOIN learning_goal lg ON lg.id = ls.goal_id
            WHERE ls.session_date = ? AND lg.user_id = ?
            ORDER BY ls.created_at
        """, (selected_date, user["id"]))
        learning_sessions = cur.fetchall()

        # Project sessions for this date
        cur.execute("""
            SELECT ps.id, p.name AS project_name, p.id AS project_id,
                   ps.duration_minutes, ps.milestone, ps.notes, ps.session_date
            FROM project_session ps
            JOIN project p ON p.id = ps.project_id
            WHERE ps.session_date = ? AND p.user_id = ?
            ORDER BY ps.created_at
        """, (selected_date, user["id"]))
        project_sessions = cur.fetchall()

        # Active learning goals (for add-session dropdown)
        cur.execute(
            "SELECT id, name FROM learning_goal WHERE is_active = 1 AND user_id = ? ORDER BY name",
            (user["id"],)
        )
        goals = cur.fetchall()

        # Active projects (for add-session dropdown)
        cur.execute(
            "SELECT id, name FROM project WHERE status = 'active' AND user_id = ? ORDER BY name",
            (user["id"],)
        )
        projects = cur.fetchall()

    finally:
        conn.close()

    return templates.TemplateResponse("history.html", {
        "request":           request,
        "user":              user,
        "selected_date":     selected_date,
        "habits":            habits,
        "learning_sessions": learning_sessions,
        "project_sessions":  project_sessions,
        "goals":             goals,
        "projects":          projects,
    })


@router.post("/history/toggle")
def history_toggle_habit(
    habit_id:      int = Form(...),
    log_date:      str = Form(...),
    redirect_date: str = Form(...),
):
    """Toggle a habit's completion for a specific date from the history page."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO habit_log (habit_id, log_date, completed)
            VALUES (?, ?, 1)
            ON CONFLICT (habit_id, log_date)
            DO UPDATE SET completed = NOT habit_log.completed
        """, (habit_id, log_date))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(f"/history?date={redirect_date}", status_code=303)
