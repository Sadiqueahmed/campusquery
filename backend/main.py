"""
main.py — FastAPI application with 3 endpoints: health, chat, export-csv.
"""

import csv
import io
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

import database
import llm_client
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

# CORS for the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
async def chat_endpoint(req: ChatRequest):
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

    return ChatResponse(
        answer=result["answer"],
        sql=result.get("sql"),
        columns=result.get("columns", []),
        rows=result.get("rows", []),
        row_count=result.get("row_count", 0),
        csv_available=result.get("csv_available", False),
        error=error,
    )


@app.post("/api/export-csv")
async def export_csv(req: ExportRequest):
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
