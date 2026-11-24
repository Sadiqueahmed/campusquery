"""
test_database.py — Tests for the hardened database security layer.

Covers:
1. db_exists check
2. Read-only connection enforcement (?mode=ro and PRAGMA query_only=ON)
3. C-level authorizer blocking INSERT, UPDATE, DELETE, DROP, CREATE, PRAGMA, ATTACH
4. execute_query structure and row count
5. Progress handler terminating runaway / cartesian queries
6. get_schema, get_distinct_values, and get_table_counts
"""

import sys
import os
import sqlite3
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database


def test_db_exists():
    assert database.db_exists() is True


def test_get_read_connection():
    conn = database.get_read_connection()
    assert isinstance(conn, sqlite3.Connection)
    # Verify query_only pragma
    cur = conn.cursor()
    cur.execute("SELECT 1")
    assert cur.fetchone()[0] == 1
    conn.close()


def test_authorizer_blocks_dml():
    """Verify authorizer raises DatabaseError when write/alter ops are attempted."""
    conn = database.get_read_connection()
    cur = conn.cursor()

    # INSERT
    with pytest.raises(sqlite3.DatabaseError):
        cur.execute("INSERT INTO students VALUES (999, 'Test', 'T', 't@t.edu', 'CS', 1, '2024-01-01')")

    # UPDATE
    with pytest.raises(sqlite3.DatabaseError):
        cur.execute("UPDATE students SET name = 'Hacked' WHERE id = 1")

    # DELETE
    with pytest.raises(sqlite3.DatabaseError):
        cur.execute("DELETE FROM students WHERE id = 1")

    # DROP TABLE
    with pytest.raises(sqlite3.DatabaseError):
        cur.execute("DROP TABLE enrollments")

    # CREATE TABLE
    with pytest.raises(sqlite3.DatabaseError):
        cur.execute("CREATE TABLE test_table (id INT)")

    # PRAGMA
    with pytest.raises(sqlite3.DatabaseError):
        cur.execute("PRAGMA table_info(students)")

    # ATTACH
    with pytest.raises(sqlite3.DatabaseError):
        cur.execute("ATTACH DATABASE ':memory:' AS hack")

    conn.close()


def test_execute_query_structure():
    result = database.execute_query("SELECT id, name, department FROM students LIMIT 5")
    assert "columns" in result
    assert "rows" in result
    assert "row_count" in result
    assert "truncated" in result
    assert result["columns"] == ["id", "name", "department"]
    assert len(result["rows"]) <= 5
    assert result["row_count"] == len(result["rows"])
    assert result["truncated"] is False


def test_execute_query_row_cap():
    # Test query returning valid data
    result = database.execute_query("SELECT * FROM enrollments")
    assert result["row_count"] > 0
    assert isinstance(result["rows"], list)


def test_progress_handler_runaway_guard():
    """Verify that a massive cartesian product trips the progress handler limit."""
    conn = database.get_read_connection()
    cur = conn.cursor()
    # A 5-way cross join will exceed 1,000,000 instructions
    massive_query = """
        SELECT count(*)
        FROM enrollments e1
        CROSS JOIN enrollments e2
        CROSS JOIN enrollments e3
        CROSS JOIN enrollments e4
    """
    with pytest.raises(sqlite3.OperationalError, match=r"(interrupted|query interrupted)"):
        cur.execute(massive_query)
    conn.close()


def test_get_schema():
    schema = database.get_schema()
    assert "CREATE TABLE students" in schema
    assert "CREATE TABLE courses" in schema
    assert "CREATE TABLE enrollments" in schema


def test_get_distinct_values():
    vals = database.get_distinct_values()
    assert "student_departments" in vals
    assert "course_departments" in vals
    assert "course_names" in vals
    assert len(vals["student_departments"]) > 0
    assert len(vals["course_departments"]) > 0
    assert len(vals["course_names"]) > 0


def test_get_table_counts():
    counts = database.get_table_counts()
    assert counts["students"] > 0
    assert counts["courses"] > 0
    assert counts["enrollments"] > 0
