"""
routers/projects.py
-------------------
Project routes scoped to the logged-in user.

Endpoints:
  GET  /projects/                    – projects page
  POST /projects/add                 – create project
  POST /projects/log                 – log work session
  POST /projects/complete/{id}       – mark project completed
  POST /projects/reactivate/{id}     – reactivate completed project
  POST /projects/delete/{id}         – delete project + sessions
  POST /projects/session/edit/{id}   – edit a logged session
  POST /projects/session/delete/{id} – delete a logged session
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
def projects_page(request: Request):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user

    today      = date.today()
    week_start = str(today - timedelta(days=today.weekday()))

    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT p.id, p.name, p.description, p.status,
                   COALESCE(SUM(CASE WHEN ps.session_date >= ? THEN ps.duration_minutes ELSE 0 END), 0) AS minutes_this_week,
                   COALESCE(SUM(ps.duration_minutes), 0) AS minutes_total,
                   COUNT(ps.id) AS session_count
            FROM project p
            LEFT JOIN project_session ps ON ps.project_id = p.id
            WHERE p.status = 'active' AND p.user_id = ?
            GROUP BY p.id, p.name, p.description, p.status
            ORDER BY p.name
        """, (week_start, user["id"]))
        projects = cur.fetchall()

        cur.execute("""
            SELECT ps.id, p.name AS project_name, ps.session_date,
                   ps.duration_minutes, ps.milestone, ps.notes
            FROM project_session ps
            JOIN project p ON p.id = ps.project_id
            WHERE p.status = 'active' AND p.user_id = ?
            ORDER BY ps.session_date DESC, ps.created_at DESC
            LIMIT 10
        """, (user["id"],))
        recent_sessions = cur.fetchall()

        cur.execute("""
            SELECT p.id, p.name, p.description,
                   COALESCE(SUM(ps.duration_minutes), 0) AS minutes_total,
                   COUNT(ps.id) AS session_count
            FROM project p
            LEFT JOIN project_session ps ON ps.project_id = p.id
            WHERE p.status = 'completed' AND p.user_id = ?
            GROUP BY p.id, p.name, p.description
            ORDER BY p.name
        """, (user["id"],))
        completed_projects = cur.fetchall()
    finally:
        conn.close()

    return templates.TemplateResponse("projects.html", {
        "request":            request,
        "user":               user,
        "projects":           projects,
        "recent_sessions":    recent_sessions,
        "completed_projects": completed_projects,
        "today":              str(today),
    })


@router.post("/add")
def add_project(request: Request, name: str = Form(...), description: str = Form("")):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO project (user_id, name, description) VALUES (?, ?, ?)",
            (user["id"], name.strip(), description or None)
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/projects", status_code=303)


@router.post("/log")
def log_session(
    request:          Request,
    project_id:       int = Form(...),
    session_date:     str = Form(...),
    duration_minutes: int = Form(...),
    milestone:        str = Form(""),
    notes:            str = Form(""),
):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO project_session (project_id, session_date, duration_minutes, milestone, notes) VALUES (?, ?, ?, ?, ?)",
            (project_id, session_date, duration_minutes, milestone or None, notes or None)
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/projects", status_code=303)


@router.post("/complete/{project_id}")
def complete_project(request: Request, project_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE project SET status = 'completed' WHERE id = ? AND user_id = ?",
            (project_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/projects", status_code=303)


@router.post("/reactivate/{project_id}")
def reactivate_project(request: Request, project_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE project SET status = 'active' WHERE id = ? AND user_id = ?",
            (project_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/projects", status_code=303)


@router.post("/delete/{project_id}")
def delete_project(request: Request, project_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM project WHERE id = ? AND user_id = ?",
            (project_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/projects", status_code=303)


@router.post("/session/edit/{session_id}")
def edit_session(
    request:          Request,
    session_id:       int,
    session_date:     str = Form(...),
    duration_minutes: int = Form(...),
    milestone:        str = Form(""),
    notes:            str = Form(""),
):
    """Update an existing project session."""
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE project_session SET
                session_date = ?, duration_minutes = ?, milestone = ?, notes = ?
            WHERE id = ?
              AND project_id IN (SELECT id FROM project WHERE user_id = ?)
        """, (session_date, duration_minutes, milestone or None, notes or None, session_id, user["id"]))
        conn.commit()
    finally:
        conn.close()
    referer = request.headers.get("referer", "/projects")
    return RedirectResponse(referer, status_code=303)


@router.post("/session/delete/{session_id}")
def delete_session(request: Request, session_id: int):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM project_session WHERE id = ? AND project_id IN (SELECT id FROM project WHERE user_id = ?)",
            (session_id, user["id"])
        )
        conn.commit()
    finally:
        conn.close()
    referer = request.headers.get("referer", "/projects")
    return RedirectResponse(referer, status_code=303)
