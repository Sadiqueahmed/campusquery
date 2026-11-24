"""
history.py — In-memory query history store (capped at 50 recent queries).
"""

from datetime import datetime, timezone
import uuid
from typing import Optional, List, Dict, Any

MAX_HISTORY_ENTRIES = 50

_history: List[Dict[str, Any]] = []


def add_entry(
    question: str,
    sql: Optional[str],
    answer: str,
    row_count: int,
    status: str = "success",
) -> Dict[str, Any]:
    """Record a query execution in the history log."""
    entry = {
        "id": str(uuid.uuid4()),
        "question": question,
        "sql": sql,
        "answer": answer[:200] if answer else "",
        "row_count": row_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
    }
    _history.insert(0, entry)  # Prepend latest first
    if len(_history) > MAX_HISTORY_ENTRIES:
        _history.pop()
    return entry


def get_history() -> List[Dict[str, Any]]:
    """Return the list of recorded history items (most recent first)."""
    return list(_history)


def clear_history() -> None:
    """Clear all recorded history."""
    _history.clear()
