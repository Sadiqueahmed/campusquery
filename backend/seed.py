"""
seed.py — Creates and populates the student_data.db SQLite database.
Idempotent: drops and recreates all tables on every run.
"""

import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "student_data.db")


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ── Drop existing tables (reverse dependency order) ──
    cur.execute("DROP TABLE IF EXISTS enrollments")
    cur.execute("DROP TABLE IF EXISTS courses")
    cur.execute("DROP TABLE IF EXISTS students")

    # ── Create tables ──
    cur.execute("""
        CREATE TABLE students (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number     TEXT    UNIQUE NOT NULL,
            name            TEXT    NOT NULL,
            email           TEXT    UNIQUE NOT NULL,
            department      TEXT    NOT NULL,
            year            INTEGER NOT NULL,
            enrollment_date TEXT    NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE courses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            department  TEXT NOT NULL,
            credits     INTEGER NOT NULL,
            instructor  TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE enrollments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL REFERENCES students(id),
            course_id   INTEGER NOT NULL REFERENCES courses(id),
            semester    TEXT    NOT NULL,
            marks       INTEGER NOT NULL CHECK (marks >= 0 AND marks <= 100),
            grade       TEXT    NOT NULL CHECK (grade IN ('A+','A','B+','B','C','D','F')),
            UNIQUE(student_id, course_id, semester)
        )
    """)

    # ── Indexes on FK columns for query performance ──
    cur.execute("CREATE INDEX idx_enrollments_student_id ON enrollments(student_id)")
    cur.execute("CREATE INDEX idx_enrollments_course_id  ON enrollments(course_id)")

    # ── Seed students (15 students, realistic Indian names) ──
    students = [
        ("CS001", "Rahul Sharma",     "rahul.sharma@university.edu",     "Computer Science", 3, "2024-08-01"),
        ("CS002", "Priya Patel",      "priya.patel@university.edu",      "Computer Science", 2, "2025-08-01"),
        ("CS003", "Amit Kumar",       "amit.kumar@university.edu",       "Computer Science", 4, "2023-08-01"),
        ("MT001", "Sneha Gupta",      "sneha.gupta@university.edu",      "Mathematics",      2, "2025-08-01"),
        ("MT002", "Rahul Verma",      "rahul.verma@university.edu",      "Mathematics",      3, "2024-08-01"),
        ("MT003", "Ananya Singh",     "ananya.singh@university.edu",     "Mathematics",      1, "2026-08-01"),
        ("EC001", "Vikram Reddy",     "vikram.reddy@university.edu",     "Electronics",      3, "2024-08-01"),
        ("EC002", "Deepika Nair",     "deepika.nair@university.edu",     "Electronics",      2, "2025-08-01"),
        ("EC003", "Arjun Mehta",      "arjun.mehta@university.edu",      "Electronics",      4, "2023-08-01"),
        ("ME001", "Kavita Joshi",     "kavita.joshi@university.edu",     "Mechanical",       1, "2026-08-01"),
        ("ME002", "Rohan Das",        "rohan.das@university.edu",        "Mechanical",       2, "2025-08-01"),
        ("ME003", "Neha Agarwal",     "neha.agarwal@university.edu",     "Mechanical",       3, "2024-08-01"),
        ("CS004", "Suresh Iyer",      "suresh.iyer@university.edu",      "Computer Science", 1, "2026-08-01"),
        ("MT004", "Pooja Deshmukh",   "pooja.deshmukh@university.edu",   "Mathematics",      4, "2023-08-01"),
        ("EC004", "Manish Tiwari",    "manish.tiwari@university.edu",    "Electronics",      1, "2026-08-01"),
    ]
    cur.executemany(
        "INSERT INTO students (roll_number, name, email, department, year, enrollment_date) VALUES (?,?,?,?,?,?)",
        students,
    )

    # ── Seed courses (8 courses) ──
    courses = [
        ("MATH101", "Mathematics",              "Mathematics",      4, "Dr. R. Krishnamurthy"),
        ("CS101",   "Computer Science",          "Computer Science", 4, "Dr. S. Venkatesh"),
        ("PHY101",  "Physics",                   "Electronics",      3, "Dr. A. Banerjee"),
        ("CS201",   "Data Structures",           "Computer Science", 4, "Dr. P. Ramesh"),
        ("CS301",   "Database Systems",          "Computer Science", 3, "Dr. M. Sundaram"),
        ("STAT201", "Statistics",                "Mathematics",      3, "Dr. L. Narayan"),
        ("EC101",   "Electronics Fundamentals",  "Electronics",      4, "Dr. K. Bhat"),
        ("ENG101",  "English Communication",     "General",          2, "Prof. D. Chatterjee"),
    ]
    cur.executemany(
        "INSERT INTO courses (course_code, course_name, department, credits, instructor) VALUES (?,?,?,?,?)",
        courses,
    )

    # ── Helper: compute grade from marks ──
    def grade_from_marks(m: int) -> str:
        if m >= 90: return "A+"
        if m >= 80: return "A"
        if m >= 70: return "B+"
        if m >= 60: return "B"
        if m >= 50: return "C"
        if m >= 40: return "D"
        return "F"

    # ── Seed enrollments (45-50 rows, 3-4 per student) ──
    # Format: (student_id, course_id, semester, marks)
    enrollment_data = [
        # Rahul Sharma (id=1) — CS dept, 4 courses, scores 85 in Math (above 80)
        (1, 1, "Fall 2024", 85),
        (1, 2, "Fall 2024", 78),
        (1, 4, "Fall 2024", 72),
        (1, 8, "Spring 2025", 65),

        # Priya Patel (id=2) — CS dept, 3 courses, scores 92 in Math (above 80)
        (2, 1, "Fall 2025", 92),
        (2, 2, "Fall 2025", 88),
        (2, 4, "Spring 2026", 76),

        # Amit Kumar (id=3) — CS dept, 4 courses
        (3, 2, "Fall 2023", 91),
        (3, 4, "Fall 2023", 85),
        (3, 5, "Spring 2024", 79),
        (3, 8, "Spring 2024", 55),

        # Sneha Gupta (id=4) — Math dept, 3 courses, scores 88 in Math (above 80)
        (4, 1, "Fall 2025", 88),
        (4, 6, "Fall 2025", 82),
        (4, 8, "Spring 2026", 70),

        # Rahul Verma (id=5) — Math dept, 4 courses, scores 81 in Math (above 80)
        (5, 1, "Fall 2024", 81),
        (5, 6, "Fall 2024", 74),
        (5, 2, "Spring 2025", 69),
        (5, 8, "Spring 2025", 58),

        # Ananya Singh (id=6) — Math dept, 3 courses
        (6, 1, "Fall 2026", 76),
        (6, 6, "Fall 2026", 68),
        (6, 8, "Fall 2026", 90),

        # Vikram Reddy (id=7) — Electronics dept, 4 courses, scores 83 in Math (above 80)
        (7, 1, "Fall 2024", 83),
        (7, 7, "Fall 2024", 87),
        (7, 3, "Spring 2025", 71),
        (7, 8, "Spring 2025", 62),

        # Deepika Nair (id=8) — Electronics dept, 3 courses
        (8, 7, "Fall 2025", 94),
        (8, 3, "Fall 2025", 66),
        (8, 1, "Spring 2026", 73),

        # Arjun Mehta (id=9) — Electronics dept, 4 courses
        (9, 7, "Fall 2023", 77),
        (9, 3, "Fall 2023", 82),
        (9, 5, "Spring 2024", 61),
        (9, 1, "Spring 2024", 45),

        # Kavita Joshi (id=10) — Mechanical dept, 3 courses
        (10, 1, "Fall 2026", 55),
        (10, 3, "Fall 2026", 48),
        (10, 8, "Fall 2026", 86),

        # Rohan Das (id=11) — Mechanical dept, 3 courses, scores 84 in Math (above 80)
        (11, 1, "Fall 2025", 84),
        (11, 3, "Fall 2025", 59),
        (11, 8, "Spring 2026", 72),

        # Neha Agarwal (id=12) — Mechanical dept, 4 courses
        (12, 1, "Fall 2024", 67),
        (12, 2, "Spring 2025", 53),
        (12, 7, "Spring 2025", 71),
        (12, 8, "Fall 2024", 88),

        # Suresh Iyer (id=13) — CS dept, 3 courses
        (13, 2, "Fall 2026", 75),
        (13, 4, "Fall 2026", 68),
        (13, 8, "Fall 2026", 82),

        # Pooja Deshmukh (id=14) — Math dept, 3 courses, scores 91 in Math (above 80)
        (14, 1, "Fall 2023", 91),
        (14, 6, "Fall 2023", 86),
        (14, 5, "Spring 2024", 73),

        # Manish Tiwari (id=15) — Electronics dept, 3 courses
        (15, 7, "Fall 2026", 64),
        (15, 3, "Fall 2026", 57),
        (15, 1, "Fall 2026", 42),
    ]

    enrollments = [(sid, cid, sem, marks, grade_from_marks(marks)) for sid, cid, sem, marks in enrollment_data]
    cur.executemany(
        "INSERT INTO enrollments (student_id, course_id, semester, marks, grade) VALUES (?,?,?,?,?)",
        enrollments,
    )

    conn.commit()

    # ── Print summary ──
    s_count = cur.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    c_count = cur.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    e_count = cur.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]
    print(f"Database seeded successfully: {DB_PATH}")
    print(f"  students:    {s_count}")
    print(f"  courses:     {c_count}")
    print(f"  enrollments: {e_count}")
    print(f"  total rows:  {s_count + c_count + e_count}")

    conn.close()


if __name__ == "__main__":
    seed()
