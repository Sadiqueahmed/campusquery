# CampusQuery 🎓
### Natural Language to SQL Assistant for University Student & Academic Records

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.0+-646CFF.svg?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Tests](https://img.shields.io/badge/Tests-25%2F25%20Passing-brightgreen.svg?style=flat&logo=pytest&logoColor=white)](backend/tests/)
[![CI](https://github.com/Sadiqueahmed/campusquery/actions/workflows/ci.yml/badge.svg)](https://github.com/Sadiqueahmed/campusquery/actions)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)](LICENSE)

CampusQuery is a full-stack, enterprise-grade AI system that enables university staff, advisors, and students to query student records, academic performance, and course enrollments using plain English. 

It translates natural language questions into optimized, dialect-specific SQL queries, runs them against a hardened read-only SQLite database, and returns both an executive summary and an interactive tabular data inspector with instant CSV export.

---

## 📸 Interface Showcase

| State | Preview |
|---|---|
| **01. Welcome Screen & Sample Queries**<br>Interactive question pills with clean onboarding. | ![Empty State](docs/screenshots/01-empty-state.png) |
| **02. Query Answer Bubble**<br>Natural-language synthesis with exact entity recognition. | ![Query Answer](docs/screenshots/02-query-answer.png) |
| **03. Syntax-Highlighted SQL & Data Panel**<br>Collapsible drawer displaying formatted SQL and real-time records. | ![SQL Drawer](docs/screenshots/03-sql-panel.png) |
| **04. CSV Export Action**<br>Formula-sanitized, Excel-compatible UTF-8 BOM CSV streaming. | ![CSV Download](docs/screenshots/04-csv-download.png) |
| **05. Multi-Layer Security Refusal**<br>Shields against destructive injection, system overrides, and off-topic questions. | ![Refusal](docs/screenshots/05-refusal.png) |

---

## 🏛️ System Architecture

CampusQuery implements a robust three-stage pipeline (**Text → SQL → Validation & Read-Only Execution → Answer Synthesis**) decoupled across specialized layers:

```mermaid
flowchart TD
    User([User in Browser]) <-->|React 18 + Tailwind| UI[Vite Frontend Client]
    UI <-->|REST API / JSON| API[FastAPI Application]
    
    subgraph "Query Engine Pipeline"
        API -->|Step A: Question + Schema| LLM[LLM Client\nGemini / Groq / Ollama]
        LLM -->|Generated SQL JSON| Val{Multi-Layer\nSQL Validator}
        
        Val -- Blocked / Unsafe --> Refusal[Safe Refusal Response]
        Refusal --> API
        
        Val -- Validated SQL --> Exec[Hardened SQLite Connection]
        
        subgraph "Defense-in-Depth Database Sandbox"
            Exec --> RO_URI[1. URI mode=ro]
            RO_URI --> PRAGMA[2. PRAGMA query_only = ON]
            PRAGMA --> AUTH[3. sqlite3 Authorizer Callback]
            AUTH --> PROG[4. Progress Handler 1M Steps Timeout]
            PROG --> DB[(student_data.db\n15 Students | 8 Courses | 51 Enrollments)]
        end
        
        DB -->|Raw Records| Synth[Step C: LLM Answer Synthesis]
        Synth -->|Natural Language Summary| RespPkg[Response Packager]
    end
    
    RespPkg -->|Answer + SQL + Rows + CSV Flag| API
```

---

## 🗄️ Relational Database Schema & ERD

The underlying database models university student academics with normalized relational integrity, foreign key cascades, and unique constraints:

```mermaid
erDiagram
    STUDENTS ||--o{ ENROLLMENTS : "has"
    COURSES ||--o{ ENROLLMENTS : "records"

    STUDENTS {
        INTEGER id PK "Auto Increment"
        TEXT roll_number UK "Unique (e.g., CS001)"
        TEXT name "Student Full Name"
        TEXT email UK "University Email"
        TEXT department "e.g., Computer Science, Mathematics"
        INTEGER year "Academic Year (1-4)"
    }

    COURSES {
        INTEGER id PK "Auto Increment"
        TEXT course_code UK "Unique (e.g., CS101)"
        TEXT course_name "Course Title"
        TEXT department "Offering Department"
        INTEGER credits "Credit Hours (1-4)"
    }

    ENROLLMENTS {
        INTEGER id PK "Auto Increment"
        INTEGER student_id FK "References students(id)"
        INTEGER course_id FK "References courses(id)"
        TEXT semester "e.g., Fall 2024, Spring 2025"
        INTEGER marks "Score (0 - 100)"
        TEXT grade "Computed Grade (A+, A, B+, B, C, F)"
    }
```

### Database Composition:
* **Students**: 15 students across Computer Science, Electrical Engineering, Mechanical Engineering, and Mathematics.
* **Courses**: 8 undergraduate courses across CS, Math, Physics, Electrical, and Humanities.
* **Enrollments**: 51 student-course enrollment records with marks (0-100) and standard letter grades (`A+` to `F`).

---

## 🛡️ 5-Point Defense-in-Depth Security Model

CampusQuery does **not** rely on LLM alignment alone for database safety. It enforces 5 distinct layers of defense:

1. **OS-Level Read-Only URI (`file:...db?mode=ro`)**:
   Connections are opened in immutable read-only mode at the SQLite virtual file system (VFS) layer. The OS kernel refuses write calls.
2. **SQLite Query-Only Enforcement (`PRAGMA query_only = ON`)**:
   Locks the database connection so any query that attempts to create, alter, insert, or delete data fails immediately inside SQLite.
3. **C-Level SQLite Authorizer Callback (`set_authorizer`)**:
   Intercepts every internal SQLite virtual machine opcode. Only `SQLITE_SELECT`, `SQLITE_READ`, and `SQLITE_FUNCTION` actions are approved. `ATTACH`, `DETACH`, `PRAGMA`, and all DDL/DML statements are denied before execution begins.
4. **Runaway Query Guard (`set_progress_handler`)**:
   Terminates runaway, Cartesian-product, or denial-of-service queries exceeding 1,000,000 SQLite VM instructions.
5. **Pre-Execution Abstract Syntax & Regex Validator (`sql_validator.py`)**:
   * Strips markdown fences, single-line (`--`), and block (`/* ... */`) comments.
   * Enforces single-statement execution (blocks stacked semicolons `;`).
   * Validates statement prefix (`SELECT` or `WITH` CTEs only).
   * Scans word-boundary tokens for blocked keywords (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`, `INSERT`, `PRAGMA`, `EXEC`, `LOAD_EXTENSION`).
   * Blocks access to SQLite metadata tables (`sqlite_master`, `sqlite_schema`).
6. **Spreadsheet Formula Injection Neutralization**:
   CSV streaming sanitizes cells starting with dangerous formula triggers (`=`, `+`, `-`, `@`) by prepending a single quote (`'`), preventing remote code execution when opened in Microsoft Excel or Google Sheets.

---

## 🚀 3-Minute Quickstart Guide

### Prerequisites
* **Python**: 3.10 or higher
* **Node.js**: 18.0 or higher
* **API Key**: Gemini API key (or Groq / local Ollama)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/Sadiqueahmed/campusquery.git
cd campusquery
```

---

### Step 2: Backend Setup
```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed the database
python seed.py

# Configure environment variables
cp .env.example .env
```

Edit `backend/.env` with your API credentials:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
```
*(Or set `LLM_PROVIDER=groq` with `GROQ_API_KEY`, or `LLM_PROVIDER=ollama` for 100% offline local inference).*

**Run the backend server:**
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Backend will be live at `http://127.0.0.1:8000`. Test via `curl http://127.0.0.1:8000/api/health`.

---

### Step 3: Frontend Setup
In a new terminal window:
```bash
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```
Frontend will be live at `http://localhost:5173`. Open in your browser to start querying!

---

### Alternative: Run with Docker Compose (Single Command) 🐳

You can launch both the full-stack backend and built frontend in a single containerized environment:

```bash
# 1. Configure your API key
cp backend/.env.example backend/.env
# Edit backend/.env with your GEMINI_API_KEY or GROQ_API_KEY

# 2. Build and launch
docker compose up --build
```
The entire application will be live at `http://localhost:8000` with automated health checks, SQLite initialization, and static file delivery.

---

## 📡 API Reference

### 1. Health Check
* **Endpoint**: `GET /api/health`
* **Response**:
```json
{
  "status": "ok",
  "db_connected": true,
  "counts": {
    "students": 15,
    "courses": 8,
    "enrollments": 51
  },
  "llm_provider": "gemini",
  "llm_configured": true
}
```

### 2. Chat & Query Processing
* **Endpoint**: `POST /api/chat`
* **Request**:
```json
{
  "question": "Which students scored above 80% in Mathematics?"
}
```
* **Success Response (200 OK)**:
```json
{
  "answer": "Seven students scored above 80% in Mathematics: Priya Patel led with 92% (Grade A+), followed by Pooja Deshmukh with 91% (Grade A+)...",
  "sql": "SELECT s.name AS student_name, s.roll_number, c.course_name, e.marks, e.grade FROM students s JOIN enrollments e ON s.id = e.student_id JOIN courses c ON e.course_id = c.id WHERE c.course_name = 'Mathematics' AND e.marks > 80 ORDER BY e.marks DESC LIMIT 500",
  "columns": ["student_name", "roll_number", "course_name", "marks", "grade"],
  "rows": [
    ["Priya Patel", "CS002", "Mathematics", 92, "A+"],
    ["Pooja Deshmukh", "MT004", "Mathematics", 91, "A+"]
  ],
  "row_count": 7,
  "csv_available": true,
  "error": null
}
```
* **Refusal / Blocked Response**:
```json
{
  "answer": "I can only answer questions about student data in this database.",
  "sql": null,
  "columns": [],
  "rows": [],
  "row_count": 0,
  "csv_available": false,
  "error": {
    "code": "cannot_answer",
    "message": "I can only answer questions about student data in this database."
  }
}
```

### 3. CSV Export
* **Endpoint**: `POST /api/export-csv`
* **Request**:
```json
{
  "sql": "SELECT DISTINCT s.roll_number, s.name AS student_name, s.email, s.department, s.year FROM students s JOIN enrollments e ON s.id = e.student_id JOIN courses c ON e.course_id = c.id WHERE c.course_name = 'Computer Science' ORDER BY s.name ASC LIMIT 500"
}
```
* **Response**: Binary streaming `text/csv; charset=utf-8` with UTF-8 BOM (`\ufeff`) for direct Excel rendering and `Content-Disposition: attachment; filename="query_results.csv"`.

### 4. Query History Management
* **List History**: `GET /api/history`
  * Returns recent queries (up to 50), timestamps, statuses (`success`, `refused`, `error`), and row counts.
* **Clear History**: `DELETE /api/history`
  * Clears the in-memory query history ring buffer: `{"cleared": true}`.

---

## 🧪 Testing & Verification Suite

The repository includes comprehensive unit and integration tests covering SQL validation, injection defense, and SQLite sandboxing:

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Test Coverage Highlights (22 Assertions):
* ✅ Standard SELECT and WITH/CTE queries accepted.
* ✅ Comment-stripping (`--` and `/* ... */`) with stacked query detection.
* ✅ Semicolon injection blocking outside string literals.
* ✅ Rejection of non-SELECT statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `PRAGMA`).
* ✅ Blocking of internal SQLite tables (`sqlite_master`, `sqlite_schema`).
* ✅ Prevention of statement-level `REPLACE` (while allowing `REPLACE()` string function).
* ✅ SQLite low-level authorizer write rejection verification.

---

## 📂 Project Directory Structure

```
campusquery/
├── .github/
│   └── workflows/
│       └── ci.yml                # Automated GitHub Actions test & build workflow
├── Dockerfile                    # Multi-stage production container build
├── docker-compose.yml            # Container orchestration with healthchecks
├── docker-entrypoint.sh          # Container runtime seed & startup
├── LICENSE                       # MIT License
├── backend/
│   ├── .env.example              # Template for API credentials
│   ├── database.py               # Read-only SQLite connection, authorizer & helpers
│   ├── history.py                # In-memory query history store
│   ├── llm_client.py             # Agnostic LLM driver (Gemini, Groq, Ollama)
│   ├── main.py                   # FastAPI app with health, chat, export, history endpoints
│   ├── query_engine.py           # 3-step Text-to-SQL & answer synthesis pipeline
│   ├── requirements.txt          # Production dependencies (FastAPI, SlowAPI, Pytest)
│   ├── seed.py                   # Deterministic database population script
│   ├── sql_validator.py          # Security scanner & AST sanitization
│   └── tests/
│       ├── test_api.py           # FastAPI endpoint & CSV export integration tests
│       ├── test_database.py      # Hardened database sandbox security tests
│       └── test_sql_validator.py # 22-point validator security test suite
├── docs/
│   └── screenshots/              # High-resolution application screenshots
├── frontend/
│   ├── index.html                # Entry point with anti-FOUC theme detector
│   ├── package.json              # React 18, Tailwind, Lucide dependencies
│   ├── tailwind.config.js        # UI utility styling with class-based dark mode
│   ├── vite.config.js            # Development bundler configuration
│   └── src/
│       ├── App.jsx               # Main chat container & state orchestrator
│       ├── api.js                # Frontend HTTP client (chat, CSV, history, health)
│       ├── index.css             # Tailwind directives & animations
│       ├── main.jsx              # DOM root mount
│       ├── hooks/
│       │   └── useTheme.js       # Light/Dark mode state with localStorage sync
│       └── components/
│           ├── ChatMessage.jsx   # Assistant/user bubbles, badges & CSV triggers
│           ├── DataVisualization.jsx # Interactive metric & distribution charts
│           ├── HistoryDrawer.jsx # Slide-out query history drawer & re-run action
│           ├── SampleQuestions.jsx # Quickstart prompt pills
│           ├── SqlResultPanel.jsx  # Multi-tab panel: Table, Chart, and SQL
│           └── ThemeToggle.jsx   # Animated Sun/Moon theme switcher
├── .gitignore                    # Strictly ignores .env, *.db, venv, node_modules
└── README.md                     # Production documentation
```

---

## 💡 Key Design Decisions & Trade-offs

1. **Why Defense-in-Depth vs Relying on LLM Prompting?**
   Prompt engineering alone cannot guarantee SQL safety. Adversarial jailbreaks ("*ignore previous rules and drop tables*") can deceive language models. By enforcing validation in Python code and locking down the SQLite C-authorizer, writes are physically impossible regardless of LLM output.
2. **Dynamic Live Schema & Known Value Injection:**
   The prompt generator queries distinct departments and course names dynamically on startup. This prevents the LLM from hallucinating non-existent department names or misinterpreting fuzzy strings.
3. **Automated Query Repair Loop:**
   If a generated SQL statement fails execution (e.g., SQLite syntax nuance), `query_engine.py` catches the database error and feeds it back to the LLM for a zero-shot automated self-correction before returning a failure to the user.
4. **Client Re-Validation on CSV Export:**
   The `/api/export-csv` endpoint never trusts SQL passed from the client; it re-validates the string through `sql_validator.py` and re-runs through the read-only authorizer.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
