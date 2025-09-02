"""SQLite helpers for Falowen.

The database location can be configured either by passing a path to
``get_connection`` (and helpers that call it) or by setting the
``FALOWEN_DB_PATH`` environment variable.  By default a file named
``vocab_progress.db`` in the current working directory is used.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date
from typing import Optional


FALOWEN_DAILY_LIMIT = 20
VOCAB_DAILY_LIMIT = 20
SCHREIBEN_DAILY_LIMIT = 5

DEFAULT_DB_PATH = "vocab_progress.db"


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Return a SQLite connection using the configured database path.

    If ``db_path`` is not provided it falls back to the ``FALOWEN_DB_PATH``
    environment variable and finally to ``DEFAULT_DB_PATH``.
    """

    path = db_path or os.getenv("FALOWEN_DB_PATH", DEFAULT_DB_PATH)
    return sqlite3.connect(path, check_same_thread=False)


def init_db(db_path: Optional[str] = None) -> None:
    """Initialise all required tables in the configured database."""

    with get_connection(db_path) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS vocab_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT,
                name TEXT,
                level TEXT,
                word TEXT,
                student_answer TEXT,
                is_correct INTEGER,
                date TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS schreiben_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT,
                name TEXT,
                level TEXT,
                essay TEXT,
                score INTEGER,
                feedback TEXT,
                date TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS sprechen_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT,
                name TEXT,
                level TEXT,
                teil TEXT,
                message TEXT,
                score INTEGER,
                feedback TEXT,
                date TEXT
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS exam_progress (
                student_code TEXT,
                level TEXT,
                teil TEXT,
                remaining TEXT,
                used TEXT,
                PRIMARY KEY (student_code, level, teil)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS my_vocab (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT,
                level TEXT,
                word TEXT,
                translation TEXT,
                date_added TEXT
            )
            """
        )
        for tbl in ["sprechen_usage", "letter_coach_usage", "schreiben_usage"]:
            c.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {tbl} (
                    student_code TEXT,
                    date TEXT,
                    count INTEGER,
                    PRIMARY KEY (student_code, date)
                )
                """
            )


def get_sprechen_usage(student_code: str, db_path: Optional[str] = None) -> int:
    """Return today's sprechen usage for ``student_code``."""

    today = str(date.today())
    with get_connection(db_path) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT count FROM sprechen_usage WHERE student_code=? AND date=?",
            (student_code, today),
        )
        row = c.fetchone()
    return row[0] if row else 0


def inc_sprechen_usage(student_code: str, db_path: Optional[str] = None) -> None:
    """Increment today's sprechen usage for ``student_code``."""

    today = str(date.today())
    with get_connection(db_path) as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO sprechen_usage (student_code, date, count)
            VALUES (?, ?, 1)
            ON CONFLICT(student_code, date)
            DO UPDATE SET count = count + 1
            """,
            (student_code, today),
        )
        conn.commit()


def has_sprechen_quota(
    student_code: str,
    limit: int = FALOWEN_DAILY_LIMIT,
    db_path: Optional[str] = None,
) -> bool:
    """Return ``True`` if ``student_code`` has remaining sprechen quota."""

    return get_sprechen_usage(student_code, db_path=db_path) < limit
