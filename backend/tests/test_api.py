"""
test_api.py — Integration tests for FastAPI endpoints (/api/health, /api/chat, /api/export-csv).

Covers:
1. GET /api/health returns 200 and schema counts
2. POST /api/chat success with mocked query engine
3. POST /api/chat validation errors (empty question, >500 chars)
4. POST /api/export-csv valid SQL streaming with UTF-8 BOM
5. POST /api/export-csv formula injection neutralization
6. POST /api/export-csv unsafe SQL rejection (400)
7. Global exception handling (500)
"""

import sys
import os
from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db_connected"] is True
    assert "students" in data["counts"]
    assert "courses" in data["counts"]
    assert "enrollments" in data["counts"]
    assert "llm_provider" in data
    assert isinstance(data["llm_configured"], bool)


def test_chat_endpoint_success():
    mock_result = {
        "answer": "Rahul is enrolled in 3 courses.",
        "sql": "SELECT * FROM enrollments WHERE student_id = 1",
        "columns": ["id", "student_id", "course_id", "grade", "marks"],
        "rows": [[1, 1, 101, "A", 92]],
        "row_count": 1,
        "csv_available": True,
        "error": None,
    }
    with patch("main.process_question", new_callable=AsyncMock) as mock_process:
        mock_process.return_value = mock_result
        response = client.post("/api/chat", json={"question": "What courses is Rahul taking?"})
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == mock_result["answer"]
        assert data["sql"] == mock_result["sql"]
        assert data["row_count"] == 1
        assert data["csv_available"] is True
        assert data["error"] is None


def test_chat_endpoint_validation_empty():
    response = client.post("/api/chat", json={"question": ""})
    assert response.status_code == 422


def test_chat_endpoint_validation_too_long():
    long_q = "A" * 501
    response = client.post("/api/chat", json={"question": long_q})
    assert response.status_code == 422


def test_export_csv_success():
    sql = "SELECT name, department FROM students LIMIT 3"
    response = client.post("/api/export-csv", json={"sql": sql})
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment; filename=\"query_results.csv\"" in response.headers["content-disposition"]
    content = response.content.decode("utf-8-sig")
    lines = content.strip().splitlines()
    assert len(lines) >= 2  # header + at least 1 row
    assert lines[0] == "name,department"


def test_export_csv_formula_injection_defense():
    """Verify cells starting with =, +, -, @ are escaped with leading single quote."""
    sql = "SELECT '=HYPERLINK(\"http://evil.com\")' AS calc, '+cmd' AS plus, '@sum' AS at"
    response = client.post("/api/export-csv", json={"sql": sql})
    assert response.status_code == 200
    content = response.content.decode("utf-8-sig")
    lines = content.strip().splitlines()
    assert len(lines) == 2
    row = lines[1]
    # Cells with leading =, +, @ should be escaped with '
    assert "'=" in row
    assert "'+cmd" in row
    assert "'@sum" in row


def test_export_csv_blocked_unsafe_sql():
    sql = "DROP TABLE students"
    response = client.post("/api/export-csv", json={"sql": sql})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "blocked_unsafe_sql"


def test_export_csv_empty_sql():
    response = client.post("/api/export-csv", json={"sql": ""})
    assert response.status_code == 422


def test_history_endpoints():
    # Clear history first
    del_res = client.delete("/api/history")
    assert del_res.status_code == 200
    assert del_res.json() == {"cleared": True}

    # Verify history is empty
    get_res = client.get("/api/history")
    assert get_res.status_code == 200
    assert get_res.json() == []

    # Send a chat message to record history
    mock_result = {
        "answer": "Test answer",
        "sql": "SELECT 1",
        "columns": ["1"],
        "rows": [[1]],
        "row_count": 1,
        "csv_available": False,
        "error": None,
    }
    with patch("main.process_question", new_callable=AsyncMock) as mock_process:
        mock_process.return_value = mock_result
        client.post("/api/chat", json={"question": "History test query"})

    # Verify history now has 1 entry
    get_res = client.get("/api/history")
    assert get_res.status_code == 200
    entries = get_res.json()
    assert len(entries) == 1
    assert entries[0]["question"] == "History test query"
    assert entries[0]["status"] == "success"

    # Clear history again
    del_res = client.delete("/api/history")
    assert del_res.status_code == 200
    assert client.get("/api/history").json() == []


def test_frontend_static_serving():
    """Verify that root / serves index.html when frontend dist exists."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "CampusQuery" in response.text


def test_global_exception_handler():
    with patch("main.process_question", new_callable=AsyncMock) as mock_process:
        mock_process.side_effect = RuntimeError("Simulated internal crash")
        response = client.post("/api/chat", json={"question": "Trigger error"})
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "server_error"
        assert "unexpected error" in data["answer"].lower()
    with patch("main.process_question", new_callable=AsyncMock) as mock_process:
        mock_process.side_effect = RuntimeError("Simulated internal crash")
        response = client.post("/api/chat", json={"question": "Trigger error"})
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "server_error"
        assert "unexpected error" in data["answer"].lower()
