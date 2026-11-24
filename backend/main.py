"""
main.py — FastAPI application with health, chat, export-csv, and query history endpoints.
"""

import csv
import io
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    _HAS_SLOWAPI = True
except ImportError:
    _HAS_SLOWAPI = False

import database
import llm_client
import history
from query_engine import process_question
from sql_validator import validate, ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Lifespan: check DB exists on startup ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not database.db_exists():
        logger.warning("Database not found. Run 'python seed.py' first.")
    yield


app = FastAPI(title="CampusQuery API", version="1.0.0", lifespan=lifespan)

# Rate limiter (graceful fallback when slowapi is not installed)
if _HAS_SLOWAPI:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
else:
    limiter = None
    logger.warning(
        "slowapi not installed — rate limiting disabled. "
        "Run 'pip install slowapi' to enable it."
    )


def _noop_limit(*_args, **_kwargs):
    """Passthrough decorator used when slowapi is not installed."""
    def _wrap(fn):
        return fn
    return _wrap


_rate_limit = limiter.limit if limiter else _noop_limit

# CORS for the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ──
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class ErrorDetail(BaseModel):
    code: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    sql: str | None = None
    columns: list = []
    rows: list = []
    row_count: int = 0
    csv_available: bool = False
    error: ErrorDetail | None = None


class ExportRequest(BaseModel):
    sql: str = Field(..., min_length=1)


class HealthResponse(BaseModel):
    status: str
    db_connected: bool
    counts: dict = {}
    llm_provider: str
    llm_configured: bool


# ── Global exception handler ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "answer": "An unexpected error occurred. Please try again.",
            "sql": None,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "csv_available": False,
            "error": {"code": "server_error", "message": "Internal server error."},
        },
    )


# ── Endpoints ──
@app.get("/api/health", response_model=HealthResponse)
async def health():
    db_ok = database.db_exists()
    counts = database.get_table_counts() if db_ok else {}
    return HealthResponse(
        status="ok" if db_ok else "db_missing",
        db_connected=db_ok,
        counts=counts,
        llm_provider=llm_client.get_provider_name(),
        llm_configured=llm_client.is_configured(),
    )


@app.post("/api/chat", response_model=ChatResponse)
@_rate_limit("30/minute")
async def chat_endpoint(request: Request, req: ChatRequest):
    if not database.db_exists():
        return ChatResponse(
            answer="Database not found. Please run 'python seed.py' to set up the database.",
            error=ErrorDetail(code="db_missing", message="student_data.db not found."),
        )

    result = await process_question(req.question)

    # Wrap error dict into ErrorDetail if present
    error = None
    if result.get("error"):
        error = ErrorDetail(**result["error"])

    # Determine status for history tracking
    if error:
        status = "refused" if error.code in ("cannot_answer", "blocked_unsafe_sql") else "error"
    else:
        status = "success"

    # Log in history
    history.add_entry(
        question=req.question,
        sql=result.get("sql"),
        answer=result["answer"],
        row_count=result.get("row_count", 0),
        status=status,
    )

    return ChatResponse(
        answer=result["answer"],
        sql=result.get("sql"),
        columns=result.get("columns", []),
        rows=result.get("rows", []),
        row_count=result.get("row_count", 0),
        csv_available=result.get("csv_available", False),
        error=error,
    )


@app.get("/api/history")
async def get_history_endpoint():
    """Return the recent query history."""
    return history.get_history()


@app.delete("/api/history")
async def clear_history_endpoint():
    """Clear query history."""
    history.clear_history()
    return {"cleared": True}


@app.post("/api/export-csv")
@_rate_limit("20/minute")
async def export_csv(request: Request, req: ExportRequest):
    """Re-validate and re-execute the SQL, then stream as CSV."""
    # Validate again — never trust client-sent SQL
    try:
        clean_sql = validate(req.sql)
    except ValidationError as ve:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": ve.code, "message": ve.message}},
        )

    try:
        result = database.execute_query(clean_sql)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "query_failed", "message": str(e)}},
        )

    # Build CSV in memory with UTF-8 BOM for Excel compatibility
    output = io.StringIO()
    output.write('\ufeff')  # UTF-8 BOM
    writer = csv.writer(output)

    # Write header
    writer.writerow(result["columns"])

    # Write rows with formula injection protection
    for row in result["rows"]:
        safe_row = []
        for cell in row:
            if isinstance(cell, str) and cell and cell[0] in ('=', '+', '-', '@'):
                cell = "'" + cell  # Neutralize formula injection
            safe_row.append(cell)
        writer.writerow(safe_row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="query_results.csv"'},
    )


# ── Production static frontend serving (Docker or single-port) ──
_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't catch /api
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        target = _DIST_DIR / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(_DIST_DIR / "index.html")
