"""
sql_validator.py — Multi-layer SQL validation to ensure only safe read queries execute.

Validation pipeline:
 1. Strip markdown fences, SQL comments, and extraneous whitespace.
 2. Reject multiple statements (semicolon outside string literals).
 3. Must begin with SELECT or WITH.
 4. Remove string literals, then scan for dangerous keywords as whole words.
 5. Block references to sqlite_ internal tables.
"""

import re
from typing import Optional


class ValidationError(Exception):
    """Raised when SQL fails a safety check."""
    def __init__(self, message: str, code: str = "blocked_unsafe_sql"):
        self.message = message
        self.code = code
        super().__init__(message)


# Keywords that are never allowed as SQL statements/commands
_BLOCKED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "PRAGMA", "ATTACH", "DETACH", "VACUUM",
    "EXEC", "EXECUTE", "LOAD_EXTENSION",
}

# REPLACE is blocked as a statement but allowed as a function (followed by "(")
_REPLACE_STMT_RE = re.compile(r'\bREPLACE\b(?!\s*\()', re.IGNORECASE)

# Match markdown code fences
_FENCE_RE = re.compile(r'^```(?:sql)?\s*\n?|```\s*$', re.MULTILINE | re.IGNORECASE)

# Match SQL single-line and block comments
_LINE_COMMENT_RE = re.compile(r'--[^\n]*')
_BLOCK_COMMENT_RE = re.compile(r'/\*.*?\*/', re.DOTALL)

# Match string literals (single-quoted in SQLite) — handles escaped quotes ('')
_STRING_LITERAL_RE = re.compile(r"'(?:[^']|'')*'")

# Match references to sqlite_ internal tables
_SQLITE_INTERNAL_RE = re.compile(r'\bsqlite_\w+', re.IGNORECASE)


def _strip_fences(sql: str) -> str:
    return _FENCE_RE.sub('', sql)


def _strip_comments(sql: str) -> str:
    sql = _BLOCK_COMMENT_RE.sub(' ', sql)
    sql = _LINE_COMMENT_RE.sub(' ', sql)
    return sql


def _remove_string_literals(sql: str) -> str:
    """Replace all string literals with a placeholder so keyword scanning ignores them."""
    return _STRING_LITERAL_RE.sub("''", sql)


def _count_real_semicolons(sql: str) -> int:
    """Count semicolons that are outside string literals."""
    cleaned = _remove_string_literals(sql)
    return cleaned.count(';')


def validate(sql: Optional[str]) -> str:
    """
    Validate and sanitize a SQL string. Returns the cleaned SQL.
    Raises ValidationError if the SQL is unsafe.
    """
    if not sql or not sql.strip():
        raise ValidationError("Empty SQL query.", code="empty_sql")

    # Step 1: Strip markdown fences and whitespace
    sql = _strip_fences(sql)

    # Step 2: Pre-check — reject multiple semicolons before comment stripping
    # (prevents hiding injection after a semicolon inside a comment)
    pre_check = _remove_string_literals(sql)
    pre_check = _BLOCK_COMMENT_RE.sub(' ', pre_check)  # Remove block comments for counting
    # Count semicolons in the pre-check text (excluding one trailing)
    pre_stripped = pre_check.strip()
    if pre_stripped.endswith(';'):
        pre_stripped = pre_stripped[:-1]
    if pre_stripped.count(';') > 0:
        raise ValidationError(
            "Multiple SQL statements are not allowed.",
            code="blocked_unsafe_sql",
        )

    # Step 3: Now strip comments and whitespace for further analysis
    sql = _strip_comments(sql)
    sql = sql.strip()

    # Remove one trailing semicolon
    if sql.endswith(';'):
        sql = sql[:-1].strip()

    if not sql:
        raise ValidationError("Empty SQL query after cleaning.", code="empty_sql")

    # Reject multiple statements (any remaining semicolons outside strings)
    if _count_real_semicolons(sql) > 0:
        raise ValidationError(
            "Multiple SQL statements are not allowed.",
            code="blocked_unsafe_sql",
        )

    # Step 4: Must start with SELECT or WITH
    first_word = sql.split()[0].upper()
    if first_word not in ("SELECT", "WITH"):
        raise ValidationError(
            f"Only SELECT queries are allowed. Got: {first_word}",
            code="blocked_unsafe_sql",
        )

    # Step 5: Remove string literals, then scan for blocked keywords
    sql_no_strings = _remove_string_literals(sql).upper()

    for keyword in _BLOCKED_KEYWORDS:
        # Match as whole word to avoid false positives (e.g., "CREATED" matching "CREATE")
        if re.search(rf'\b{keyword}\b', sql_no_strings):
            raise ValidationError(
                f"Forbidden keyword detected: {keyword}",
                code="blocked_unsafe_sql",
            )

    # Check REPLACE as statement (not as a function)
    if _REPLACE_STMT_RE.search(sql):
        raise ValidationError(
            "REPLACE statements are not allowed.",
            code="blocked_unsafe_sql",
        )

    # Step 6: Block references to sqlite_ internal tables
    sql_no_strings_original = _STRING_LITERAL_RE.sub("''", sql)
    if _SQLITE_INTERNAL_RE.search(sql_no_strings_original):
        raise ValidationError(
            "Access to SQLite internal tables is not allowed.",
            code="blocked_unsafe_sql",
        )

    return sql
