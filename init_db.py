"""
init_db.py
----------
One-time database initialisation script. Run this before starting the app:

    python init_db.py

Creates all tables if they don't already exist and sets up Bharath's
admin account (prompted on first run). Safe to re-run — existing data
is untouched. The database file (tracklytics.db) is created at the
project root if absent.
"""

import random
import string
from app.database import get_connection
from app.auth import hash_password

SCHEMA = """
-- Users (one row per person using the app)
CREATE TABLE IF NOT EXISTS user (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT    NOT NULL,
    email                TEXT    NOT NULL UNIQUE,
    hashed_password      TEXT    NOT NULL,
    must_change_password INTEGER DEFAULT 1,  -- 1 = force change on first login
    is_admin             INTEGER DEFAULT 0,  -- 1 = can access /admin panel
    created_at           TEXT    DEFAULT (datetime('now'))
);

-- Habits (one per user per habit they create)
CREATE TABLE IF NOT EXISTS habit (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    icon       TEXT    DEFAULT '✅',
    category   TEXT    DEFAULT 'other',
    is_active  INTEGER DEFAULT 1,
    created_at TEXT    DEFAULT (datetime('now'))
);

-- Daily habit completion logs
CREATE TABLE IF NOT EXISTS habit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id   INTEGER NOT NULL REFERENCES habit(id) ON DELETE CASCADE,
    log_date   TEXT    NOT NULL DEFAULT (date('now')),
    completed  INTEGER NOT NULL DEFAULT 0,
    notes      TEXT,
    created_at TEXT    DEFAULT (datetime('now')),
    UNIQUE (habit_id, log_date)
);

-- Learning goals (one per user per goal)
CREATE TABLE IF NOT EXISTS learning_goal (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                 INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    name                    TEXT    NOT NULL,
    description             TEXT,
    target_minutes_per_week INTEGER DEFAULT 60,
    is_active               INTEGER DEFAULT 1,
    created_at              TEXT    DEFAULT (datetime('now'))
);

-- Learning sessions logged against a goal
CREATE TABLE IF NOT EXISTS learning_session (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id          INTEGER NOT NULL REFERENCES learning_goal(id) ON DELETE CASCADE,
    session_date     TEXT    NOT NULL DEFAULT (date('now')),
    duration_minutes INTEGER NOT NULL,
    topic            TEXT,
    notes            TEXT,
    created_at       TEXT    DEFAULT (datetime('now'))
);

-- Projects (one per user per project)
CREATE TABLE IF NOT EXISTS project (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    description TEXT,
    status      TEXT    DEFAULT 'active',
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- Work sessions logged against a project
CREATE TABLE IF NOT EXISTS project_session (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    session_date     TEXT    NOT NULL DEFAULT (date('now')),
    duration_minutes INTEGER NOT NULL,
    milestone        TEXT,
    notes            TEXT,
    created_at       TEXT    DEFAULT (datetime('now'))
);
"""


def _generate_temp_password(length: int = 10) -> str:
    """Generate a readable random temporary password."""
    chars = string.ascii_letters + string.digits
    chars = chars.translate(str.maketrans("", "", "0OIl1"))
    return "".join(random.choices(chars, k=length))


def create_admin(conn):
    """Create Bharath's admin account if no admin exists yet."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM user WHERE is_admin = 1")
    if cur.fetchone()[0] > 0:
        return  # Admin already exists

    print("\n── First-time setup: create your admin account ──")
    name  = input("Your name: ").strip() or "Bharath"
    email = input("Your email: ").strip().lower()
    temp  = _generate_temp_password()

    conn.execute(
        "INSERT INTO user (name, email, hashed_password, must_change_password, is_admin) VALUES (?, ?, ?, 1, 1)",
        (name, email, hash_password(temp))
    )
    conn.commit()
    print(f"\n✅ Admin account created!")
    print(f"   Email:             {email}")
    print(f"   Temporary password: {temp}")
    print(f"   You'll be asked to set a new password on first login.\n")


if __name__ == '__main__':
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    create_admin(conn)
    conn.close()
    print("✅ Database ready! Add your habits, goals, and projects from the app.")
