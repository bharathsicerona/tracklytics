"""
database.py
-----------
Provides a single get_connection() helper used by all routers.

The database is a local SQLite file (tracklytics.db) stored at the project root.
SQLite requires no server — the file is created automatically on first connection.

Run `python init_db.py` once to create the tables before starting the app.
"""

import sqlite3
import os

# Absolute path to the database file, resolved relative to this file's location.
# This keeps the DB at the project root regardless of where uvicorn is launched from.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tracklytics.db')


def get_connection() -> sqlite3.Connection:
    """
    Open and return a new SQLite connection.

    Row factory is set to sqlite3.Row so columns can be accessed by name
    (e.g. row['name']) instead of by index — Jinja2 templates use dot notation
    (row.name) which sqlite3.Row also supports.

    Foreign key enforcement is enabled per connection via PRAGMA because
    SQLite disables it by default.

    Always close the connection in a try/finally block in the caller.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # dict-like column access
    conn.execute("PRAGMA foreign_keys = ON")  # enforce ON DELETE CASCADE
    return conn
