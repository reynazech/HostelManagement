"""SQLite storage for students, attendance and admin settings."""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_DB_PATH = Path("messtime.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id  TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    phone       TEXT,
    room        TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  TEXT NOT NULL REFERENCES students(student_id),
    meal        TEXT NOT NULL,
    meal_date   DATE NOT NULL,
    marked_at   TIMESTAMP NOT NULL,
    UNIQUE (student_id, meal, meal_date)
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# Meal windows as (name, start hour, end hour). Scans outside these are rejected.
MEALS = [
    ("breakfast", 6, 11),
    ("lunch", 11, 16),
    ("dinner", 18, 23),
]


@dataclass
class Student:
    student_id: str
    name: str
    phone: str = ""
    room: str = ""


class AttendanceError(Exception):
    """Raised when attendance can't be marked (unknown student, duplicate, wrong time)."""


def meal_for(moment: datetime) -> str | None:
    for name, start, end in MEALS:
        if start <= moment.hour < end:
            return name
    return None


@contextmanager
def connect(path: Path = DEFAULT_DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def add_student(conn: sqlite3.Connection, student: Student) -> None:
    try:
        conn.execute(
            "INSERT INTO students (student_id, name, phone, room) VALUES (?, ?, ?, ?)",
            (student.student_id, student.name, student.phone, student.room),
        )
    except sqlite3.IntegrityError:
        raise ValueError(f"A student with ID {student.student_id!r} already exists") from None


def get_student(conn: sqlite3.Connection, student_id: str) -> Student | None:
    row = conn.execute(
        "SELECT student_id, name, phone, room FROM students WHERE student_id = ?",
        (student_id,),
    ).fetchone()
    return Student(**row) if row else None


def list_students(conn: sqlite3.Connection) -> list[Student]:
    rows = conn.execute("SELECT student_id, name, phone, room FROM students ORDER BY name")
    return [Student(**row) for row in rows]


def mark_attendance(
    conn: sqlite3.Connection, student_id: str, moment: datetime | None = None
) -> tuple[Student, str]:
    """Record that a student ate the current meal. Returns the student and meal name."""
    moment = moment or datetime.now()
    student = get_student(conn, student_id)
    if student is None:
        raise AttendanceError(f"Unknown student ID {student_id!r}")

    meal = meal_for(moment)
    if meal is None:
        raise AttendanceError(f"No meal is being served at {moment:%H:%M}")

    try:
        conn.execute(
            "INSERT INTO attendance (student_id, meal, meal_date, marked_at) VALUES (?, ?, ?, ?)",
            (student_id, meal, moment.date().isoformat(), moment.isoformat(timespec="seconds")),
        )
    except sqlite3.IntegrityError:
        raise AttendanceError(f"{student.name} has already been marked for {meal} today") from None
    return student, meal


def attendance_records(conn: sqlite3.Connection, on: str | None = None) -> list[sqlite3.Row]:
    query = """
        SELECT a.meal_date, a.meal, a.marked_at, s.student_id, s.name, s.room
        FROM attendance a JOIN students s USING (student_id)
    """
    params: tuple = ()
    if on:
        query += " WHERE a.meal_date = ?"
        params = (on,)
    query += " ORDER BY a.marked_at"
    return conn.execute(query, params).fetchall()


def get_setting(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
