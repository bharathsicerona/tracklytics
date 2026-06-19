"""
routers/learning.py
-------------------
Learning goal routes scoped to the logged-in user.

Endpoints:
  GET  /learning/                    – learning page
  POST /learning/add                 – create goal
  POST /learning/log                 – log session
  POST /learning/complete/{id}       – mark goal completed
  POST /learning/reactivate/{id}     – reactivate completed goal
  POST /learning/delete/{id}         – delete goal + sessions
  POST /learning/session/edit/{id}   – edit a logged session
  POST /learning/session/delete/{id} – delete a logged session
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date, timedelta

from app.database import get_connection
from app.auth import require_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def learning_page(request: Request):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user

    today      = date.today()
    week_start = str(today - timedelta(days=today.weekday()))

    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT lg.id, lg.name, lg.description, lg.target_minutes_per_week,
                   COALESCE(SUM(CASE WHEN ls.session_date >= ? THEN ls.duration_minutes ELSE 0 END), 0) AS minutes_this_week,
                   COALESCE(SUM(ls.duration_minutes), 0) AS minutes_total,
                   COUNT(ls.id) AS session_count
            FROM learning_goal lg
            LEFT JOIN learning_session ls ON ls.goal_id = lg.id
            WHERE lg.is_active = 1 AND lg.user_id = ?
            GROUP BY lg.id, lg.name, lg.description, lg.target_minutes_per_week
            ORDER BY lg.name
        """, (week_start, user["id"]))
        goals = cur.fetchall()

        cur.execute("""
            SELECT ls.id, lg.name AS goal_name, ls.session_date,
                   ls.duration_minutes, ls.topic, ls.notes
            FROM learning_session ls
            JOIN learning_goal lg ON lg.id = ls.goal_id
            WHERE lg.is_active = 1 AND lg.user_id = ?
            ORDER BY ls.session_date DESC, ls.created_at DESC
            LIMIT 10
        """, (user["id"],))
        recent_sessions = cur.fetchall()

        cur.execute("""
            SELECT lg.id, lg.name, lg.description,
                   COALESCE(SUM(ls.duration_minutes), 0) AS minutes_total,
                   COUNT(ls.id) AS session_count
            FROM learning_goal lg
            LEFT JOIN learning_session ls ON ls.goal_id = lg.id
            WHERE lg.is_active = 0 AND lg.user_id = ?
            GROUP BY lg.id, lg.name, lg.description
            ORDER BY lg.name
        """, (user["id"],))
        completed_goals = cur.fetchall()
    finally:
        conn.close()

    return templates.TemplateResponse("learning.html", {
        "request":         request,
        "user":            user,
        "goals":           goals,
        "recent_sessions": recent_sessions,
        "completed_goals": completed_goals,
        "today":           str(today),
    })


@router.post("/add")
def add_goal(
    request:                 Request,
    name:                    str = Form(...),
    description:             str = Form(""),
    target_minutes_per_week: int = Form(60),
):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO learning_goal (user_id, name, description, target_minutes_per_week) VALUES (?, ?, ?, ?)",
            (user["id"], name.strip(), description or None, target_minutes_per_week)
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/learning", status_code=303)


@router.post("/log")
def log_session(
    request:          Request,
    goal_id:          int = Form(...),
    session_date:     str = Form(...),
    duration_minutes: int = Form(...),
    topic:            str = Form(""),
    notes:            str = Form(""),
):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO learning_session (goal_id, session_date, duration_minutes, topic, notes) VALUES (?, ?, ?, ?, ?)",
            (goal_id, session_date, duration_minutes, topic or None, notes or None)
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/learning", status_code=303)


@router.post("/complete/{goal_id}")
def complete_goal(request: Request, goal_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE learning_goal SET is_active = 0 WHERE id = ? AND user_id = ?",
            (goal_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/learning", status_code=303)


@router.post("/reactivate/{goal_id}")
def reactivate_goal(request: Request, goal_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE learning_goal SET is_active = 1 WHERE id = ? AND user_id = ?",
            (goal_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/learning", status_code=303)


@router.post("/delete/{goal_id}")
def delete_goal(request: Request, goal_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM learning_goal WHERE id = ? AND user_id = ?",
            (goal_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/learning", status_code=303)


@router.post("/session/edit/{session_id}")
def edit_session(
    request:          Request,
    session_id:       int,
    session_date:     str = Form(...),
    duration_minutes: int = Form(...),
    topic:            str = Form(""),
    notes:            str = Form(""),
):
    """Update an existing learning session. Redirects back to the referring page."""
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        # Verify session belongs to this user via goal ownership
        conn.execute("""
            UPDATE learning_session SET
                session_date = ?, duration_minutes = ?, topic = ?, notes = ?
            WHERE id = ?
              AND goal_id IN (SELECT id FROM learning_goal WHERE user_id = ?)
        """, (session_date, duration_minutes, topic or None, notes or None, session_id, user["id"]))
        conn.commit()
    finally:
        conn.close()
    # Redirect back to wherever the edit was triggered from
    referer = request.headers.get("referer", "/learning")
    return RedirectResponse(referer, status_code=303)


@router.post("/session/delete/{session_id}")
def delete_session(request: Request, session_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM learning_session WHERE id = ? AND goal_id IN (SELECT id FROM learning_goal WHERE user_id = ?)",
            (session_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    referer = request.headers.get("referer", "/learning")
    return RedirectResponse(referer, status_code=303)
