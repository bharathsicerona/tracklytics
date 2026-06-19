-- ============================================================
-- Tracklytics – SQLite Schema Reference
-- NOTE: This file is for documentation only.
--       The app initialises the database via: python init_db.py
-- ============================================================

-- ── USERS ───────────────────────────────────────────────────
-- One row per registered user.
-- is_admin = 1 gives access to /admin panel.
-- must_change_password = 1 forces password reset on next login (new accounts).
CREATE TABLE IF NOT EXISTS user (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT    NOT NULL,
    email                TEXT    NOT NULL UNIQUE,
    password_hash        TEXT    NOT NULL,
    is_admin             INTEGER DEFAULT 0,
    must_change_password INTEGER DEFAULT 0,   -- 1 = temp password, must reset
    created_at           TEXT    DEFAULT (datetime('now'))
);

-- ── HABITS ──────────────────────────────────────────────────
-- One row per habit the user creates.
-- Habits are never hard-deleted when paused; is_active = 0 hides them.
CREATE TABLE IF NOT EXISTS habit (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    icon       TEXT    DEFAULT '✅',         -- emoji, auto-assigned from category
    category   TEXT    DEFAULT 'other',      -- fitness | hygiene | nutrition | sleep | mindset | other
    is_active  INTEGER DEFAULT 1,            -- 1 = tracked daily, 0 = paused
    created_at TEXT    DEFAULT (datetime('now'))
);

-- One row per habit per calendar day.
-- completed = 1 means the habit was done that day.
-- UNIQUE constraint prevents duplicate entries for the same habit+date.
CREATE TABLE IF NOT EXISTS habit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id   INTEGER NOT NULL REFERENCES habit(id) ON DELETE CASCADE,
    log_date   TEXT    NOT NULL DEFAULT (date('now')),  -- stored as YYYY-MM-DD
    completed  INTEGER NOT NULL DEFAULT 0,
    notes      TEXT,
    created_at TEXT    DEFAULT (datetime('now')),
    UNIQUE (habit_id, log_date)
);

-- ── LEARNING GOALS ──────────────────────────────────────────
-- One row per learning goal (e.g. Python, AI Tools).
-- is_active = 0 means goal is completed and hidden from tracking.
CREATE TABLE IF NOT EXISTS learning_goal (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                 INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    name                    TEXT    NOT NULL,
    description             TEXT,
    target_minutes_per_week INTEGER DEFAULT 60,
    is_active               INTEGER DEFAULT 1,           -- 0 = completed
    created_at              TEXT    DEFAULT (datetime('now'))
);

-- One row per learning session logged by the user.
CREATE TABLE IF NOT EXISTS learning_session (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id          INTEGER NOT NULL REFERENCES learning_goal(id) ON DELETE CASCADE,
    session_date     TEXT    NOT NULL DEFAULT (date('now')),
    duration_minutes INTEGER NOT NULL,
    topic            TEXT,   -- what was covered in this session
    notes            TEXT,
    created_at       TEXT    DEFAULT (datetime('now'))
);

-- ── PROJECTS ────────────────────────────────────────────────
-- One row per project (e.g. Tracklytics, Gold Trading EA).
-- status: 'active' = in progress, 'completed' = done and archived.
CREATE TABLE IF NOT EXISTS project (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    description TEXT,
    status      TEXT    DEFAULT 'active',   -- active | completed
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- One row per work session logged against a project.
CREATE TABLE IF NOT EXISTS project_session (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    session_date     TEXT    NOT NULL DEFAULT (date('now')),
    duration_minutes INTEGER NOT NULL,
    milestone        TEXT,   -- optional: what was built or completed this session
    notes            TEXT,
    created_at       TEXT    DEFAULT (datetime('now'))
);
