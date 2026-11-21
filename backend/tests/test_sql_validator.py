"""
test_sql_validator.py — Tests for the SQL validation layer.

Covers: valid queries, dangerous statements, injection attacks,
comment hiding, string literals containing keywords, and read-only enforcement.
"""

import sys
import os
import sqlite3

# Allow importing from parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sql_validator import validate, ValidationError

passed = 0
failed = 0


def assert_valid(sql: str, label: str):
    """Expect validate() to succeed."""
    global passed, failed
    try:
        result = validate(sql)
        assert result, f"validate returned empty for: {label}"
        passed += 1
        print(f"  ✓ {label}")
    except Exception as e:
        failed += 1
        print(f"  ✗ {label} — unexpected error: {e}")


def assert_blocked(sql: str, label: str):
    """Expect validate() to raise ValidationError."""
    global passed, failed
    try:
        validate(sql)
        failed += 1
        print(f"  ✗ {label} — should have been blocked but was allowed")
    except ValidationError:
        passed += 1
        print(f"  ✓ {label}")
    except Exception as e:
        failed += 1
        print(f"  ✗ {label} — wrong exception type: {type(e).__name__}: {e}")


def test_valid_queries():
    print("\n── Valid Queries ──")
    assert_valid("SELECT * FROM students", "basic SELECT")
    assert_valid(
        "WITH cte AS (SELECT id FROM students) SELECT * FROM cte",
        "WITH CTE",
    )
    assert_valid(
        "```sql\nSELECT * FROM students\n```",
        "markdown-fenced SQL",
    )
    assert_valid(
        "SELECT * FROM students ORDER BY name;",
        "trailing semicolon stripped",
    )
    assert_valid(
        "SELECT name FROM students WHERE name LIKE '%delete%'",
        "string literal containing 'delete' is allowed",
    )
    assert_valid(
        "SELECT REPLACE(name, 'a', 'b') FROM students",
        "REPLACE() function is allowed",
    )


def test_blocked_queries():
    print("\n── Blocked Queries ──")
    assert_blocked("DROP TABLE enrollments", "DROP TABLE")
    assert_blocked("DELETE FROM students", "DELETE FROM")
    assert_blocked("SELECT 1; DROP TABLE students", "semicolon injection")
    assert_blocked(
        "UPDATE students SET name='hacked' WHERE id=1",
        "UPDATE",
    )
    assert_blocked("INSERT INTO students VALUES (99, 'x', 'x', 'x', 'x', 1, '2024-01-01')", "INSERT")
    assert_blocked("TRUNCATE TABLE students", "TRUNCATE")
    assert_blocked("CREATE TABLE hack (id INTEGER)", "CREATE")
    assert_blocked("PRAGMA table_info(students)", "PRAGMA")
    assert_blocked("ATTACH DATABASE ':memory:' AS hack", "ATTACH")
    assert_blocked("", "empty input")
    assert_blocked("   ", "whitespace-only input")


def test_comment_attacks():
    print("\n── Comment-Hidden Attacks ──")
    assert_blocked(
        "SELECT * FROM students; -- DROP TABLE students",
        "comment-hidden DROP after semicolon",
    )
    assert_blocked(
        "SELECT * FROM students /* ; DELETE FROM students */; DROP TABLE enrollments",
        "block-comment hidden attack",
    )


def test_sqlite_internal():
    print("\n── SQLite Internal Tables ──")
    assert_blocked(
        "SELECT * FROM sqlite_master",
        "sqlite_master access",
    )
    assert_blocked(
        "SELECT sql FROM sqlite_schema",
        "sqlite_schema access",
    )


def test_read_only_connection():
    """Verify the read-only connection actually refuses writes at the DB level."""
    print("\n── Read-Only Connection ──")
    global passed, failed

    # Create a temp DB for this test
    from database import get_read_connection, DB_PATH
    if not os.path.isfile(DB_PATH):
        print("  ⚠ Skipping read-only test (no database file). Run seed.py first.")
        return

    conn = get_read_connection()
    try:
        conn.execute("INSERT INTO students (roll_number, name, email, department, year, enrollment_date) VALUES ('XX', 'XX', 'xx@x.com', 'XX', 1, '2024-01-01')")
        failed += 1
        print("  ✗ Read-only connection allowed INSERT")
    except Exception:
        passed += 1
        print("  ✓ Read-only connection blocked INSERT")
    finally:
        conn.close()


if __name__ == "__main__":
    test_valid_queries()
    test_blocked_queries()
    test_comment_attacks()
    test_sqlite_internal()
    test_read_only_connection()

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
    print("All tests passed! ✓")
