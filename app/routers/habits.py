"""
routers/habits.py
-----------------
Habit routes scoped to the logged-in user.
Every query filters by user_id so users only see their own data.

Endpoints:
  GET  /habits/                – habits page
  POST /habits/toggle          – mark done/undone for a date
  POST /habits/add             – create new habit
  POST /habits/deactivate/{id} – pause habit
  POST /habits/reactivate/{id} – resume habit
  POST /habits/delete/{id}     – permanently delete habit + history
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date, timedelta

from app.database import get_connection
from app.auth import require_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ICONS = {
    "fitness":   "🏋️",
    "hygiene":   "🚿",
    "nutrition": "🍳",
    "sleep":     "😴",
    "mindset":   "🧘",
    "other":     "✅",
}


@router.get("/", response_class=HTMLResponse)
def habits_page(request: Request):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user

    today     = date.today()
    today_str = str(today)
    seven_ago = str(today - timedelta(days=6))

    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT h.id, h.name, h.icon, h.category,
                   date(h.created_at) AS start_date,
                   COALESCE(hl.completed, 0) AS completed
            FROM habit h
            LEFT JOIN habit_log hl ON hl.habit_id = h.id AND hl.log_date = ?
            WHERE h.is_active = 1 AND h.user_id = ?
            ORDER BY h.created_at
        """, (today_str, user["id"]))
        habits = cur.fetchall()

        cur.execute("""
            SELECT h.id AS habit_id, hl.log_date, hl.completed
            FROM habit h
            JOIN habit_log hl ON hl.habit_id = h.id
            WHERE h.is_active = 1 AND h.user_id = ?
              AND hl.log_date >= ?
              AND hl.log_date >= date(h.created_at)
            ORDER BY h.id, hl.log_date
        """, (user["id"], seven_ago))
        history_rows = cur.fetchall()

        cur.execute("""
            SELECT id, name, icon, category FROM habit
            WHERE is_active = 0 AND user_id = ?
            ORDER BY name
        """, (user["id"],))
        inactive = cur.fetchall()
    finally:
        conn.close()

    history = {}
    for row in history_rows:
        hid = row["habit_id"]
        if hid not in history:
            history[hid] = {}
        history[hid][str(row["log_date"])] = bool(row["completed"])

    last_7 = [str(today - timedelta(days=i)) for i in range(6, -1, -1)]

    return templates.TemplateResponse("habits.html", {
        "request":  request,
        "user":     user,
        "habits":   habits,
        "inactive": inactive,
        "today":    today_str,
        "history":  history,
        "last_7":   last_7,
    })


@router.post("/toggle")
def toggle_habit(habit_id: int = Form(...), log_date: str = Form(...)):
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
    return RedirectResponse("/", status_code=303)


@router.post("/add")
def add_habit(request: Request, name: str = Form(...), category: str = Form("other")):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    icon = ICONS.get(category, "✅")
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO habit (user_id, name, icon, category) VALUES (?, ?, ?, ?)",
            (user["id"], name.strip(), icon, category)
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/habits", status_code=303)


@router.post("/deactivate/{habit_id}")
def deactivate_habit(request: Request, habit_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE habit SET is_active = 0 WHERE id = ? AND user_id = ?",
            (habit_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/habits", status_code=303)


@router.post("/reactivate/{habit_id}")
def reactivate_habit(request: Request, habit_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE habit SET is_active = 1 WHERE id = ? AND user_id = ?",
            (habit_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/habits", status_code=303)


@router.post("/delete/{habit_id}")
def delete_habit(request: Request, habit_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM habit WHERE id = ? AND user_id = ?",
            (habit_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/habits", status_code=303)
