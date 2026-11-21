"""
database.py — Read-only SQLite access with defense-in-depth security.

Security layers:
 1. URI mode with ?mode=ro (OS-level read-only)
 2. PRAGMA query_only = ON (SQLite-level write block)
 3. set_authorizer callback (denies everything except SELECT/READ/FUNCTION)
 4. Progress handler timeout (kills runaway queries)
 5. Row cap via fetchmany(500)
"""

import sqlite3
import os
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "student_data.db")

# Maximum rows returned per query
MAX_ROWS = 500

# Authorizer action codes — only these are allowed
_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,     # Allow SELECT statements
    sqlite3.SQLITE_READ,       # Allow reading column values
    sqlite3.SQLITE_FUNCTION,   # Allow calling functions (COUNT, AVG, etc.)
}


def _authorizer(action, arg1, arg2, db_name, trigger_name):
    """Deny everything except SELECT, READ, and FUNCTION calls."""
    if action in _ALLOWED_ACTIONS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def get_read_connection() -> sqlite3.Connection:
    """Open a hardened read-only connection."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only = ON")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.set_authorizer(_authorizer)
    # Kill queries that run more than 1 million SQLite VM steps (~few seconds)
    conn.set_progress_handler(lambda: 1, 1_000_000)
    return conn


def execute_query(sql: str) -> dict:
    """
    Execute a validated read-only SQL query and return results.
    Returns: {columns: [...], rows: [[...], ...], row_count: int, truncated: bool}
    """
    conn = get_read_connection()
    try:
        cur = conn.execute(sql)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchmany(MAX_ROWS)
        # Check if there are more rows beyond the cap
        extra = cur.fetchone()
        truncated = extra is not None
        return {
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
            "truncated": truncated,
        }
    finally:
        conn.close()


def get_schema() -> str:
    """Read the CREATE TABLE statements from the database for the LLM prompt."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    schemas = [row[0] for row in cur.fetchall() if row[0]]
    conn.close()
    return "\n\n".join(schemas)


def get_distinct_values() -> dict:
    """Fetch distinct values the LLM needs for exact name matching."""
    conn = sqlite3.connect(DB_PATH)
    result = {}
    for col_label, query in [
        ("student_departments",  "SELECT DISTINCT department FROM students ORDER BY department"),
        ("course_departments",   "SELECT DISTINCT department FROM courses ORDER BY department"),
        ("course_names",         "SELECT DISTINCT course_name FROM courses ORDER BY course_name"),
    ]:
        result[col_label] = [r[0] for r in conn.execute(query).fetchall()]
    conn.close()
    return result


def get_table_counts() -> dict:
    """Return row counts for health check."""
    conn = sqlite3.connect(DB_PATH)
    counts = {}
    for table in ("students", "courses", "enrollments"):
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return counts


def db_exists() -> bool:
    return os.path.isfile(DB_PATH)
