import os
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(os.getenv("DB_PATH", "langassist.db"))


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_utc():
    return datetime.now(timezone.utc)


def now_iso():
    return now_utc().isoformat()


def add_column_if_missing(conn, table_name, column_name, column_sql):
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    column_names = [column["name"] for column in columns]

    if column_name not in column_names:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


def init_db():
    with connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            native_lang TEXT,
            target_lang TEXT,
            state TEXT NOT NULL DEFAULT 'await_native',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            phrase TEXT NOT NULL,
            translation TEXT NOT NULL,
            definition TEXT,
            pronunciation TEXT,
            part_of_speech TEXT,
            difficulty TEXT,
            example_target TEXT,
            example_native TEXT,
            times_reviewed INTEGER NOT NULL DEFAULT 0,
            correct_count INTEGER NOT NULL DEFAULT 0,
            wrong_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_reviewed_at TEXT,
            next_due_at TEXT,
            UNIQUE(telegram_id, phrase)
        )
        """)

        add_column_if_missing(conn, "users", "updated_at", "updated_at TEXT")
        add_column_if_missing(conn, "cards", "part_of_speech", "part_of_speech TEXT")
        add_column_if_missing(conn, "cards", "difficulty", "difficulty TEXT")
        add_column_if_missing(conn, "cards", "wrong_count", "wrong_count INTEGER NOT NULL DEFAULT 0")
        add_column_if_missing(conn, "cards", "updated_at", "updated_at TEXT")
        add_column_if_missing(conn, "cards", "last_reviewed_at", "last_reviewed_at TEXT")
        add_column_if_missing(conn, "cards", "next_due_at", "next_due_at TEXT")


def row_to_user(row):
    if not row:
        return None

    return {
        "telegram_id": row["telegram_id"],
        "native_lang": row["native_lang"],
        "target_lang": row["target_lang"],
        "state": row["state"],
    }


def get_or_create_user(telegram_id: int):
    with connect() as conn:
        row = conn.execute(
            """
            SELECT telegram_id, native_lang, target_lang, state
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()

        if row:
            return row_to_user(row)

        timestamp = now_iso()

        conn.execute(
            """
            INSERT INTO users (
                telegram_id, state, created_at, updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (telegram_id, "await_native", timestamp, timestamp),
        )

        return {
            "telegram_id": telegram_id,
            "native_lang": None,
            "target_lang": None,
            "state": "await_native",
        }


def get_user(telegram_id: int):
    with connect() as conn:
        row = conn.execute(
            """
            SELECT telegram_id, native_lang, target_lang, state
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()

        return row_to_user(row)


def set_native_language(telegram_id: int, native_lang: str):
    with connect() as conn:
        conn.execute(
            """
            UPDATE users
            SET native_lang = ?, state = ?, updated_at = ?
            WHERE telegram_id = ?
            """,
            (native_lang, "await_target", now_iso(), telegram_id),
        )


def set_target_language(telegram_id: int, target_lang: str):
    with connect() as conn:
        conn.execute(
            """
            UPDATE users
            SET target_lang = ?, state = ?, updated_at = ?
            WHERE telegram_id = ?
            """,
            (target_lang, "ready", now_iso(), telegram_id),
        )


def reset_languages(telegram_id: int):
    with connect() as conn:
        conn.execute(
            """
            UPDATE users
            SET native_lang = NULL,
                target_lang = NULL,
                state = ?,
                updated_at = ?
            WHERE telegram_id = ?
            """,
            ("await_native", now_iso(), telegram_id),
        )


def save_card(telegram_id: int, card: dict):
    timestamp = now_iso()

    with connect() as conn:
        existing = conn.execute(
            """
            SELECT id
            FROM cards
            WHERE telegram_id = ? AND lower(phrase) = lower(?)
            """,
            (telegram_id, card["phrase"]),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE cards
                SET translation = ?,
                    definition = ?,
                    pronunciation = ?,
                    part_of_speech = ?,
                    difficulty = ?,
                    example_target = ?,
                    example_native = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    card.get("translation", ""),
                    card.get("definition", ""),
                    card.get("pronunciation", ""),
                    card.get("part_of_speech", ""),
                    card.get("difficulty", "beginner"),
                    card.get("example_target", ""),
                    card.get("example_native", ""),
                    timestamp,
                    existing["id"],
                ),
            )
            return existing["id"]

        cursor = conn.execute(
            """
            INSERT INTO cards (
                telegram_id,
                phrase,
                translation,
                definition,
                pronunciation,
                part_of_speech,
                difficulty,
                example_target,
                example_native,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                card.get("phrase", ""),
                card.get("translation", ""),
                card.get("definition", ""),
                card.get("pronunciation", ""),
                card.get("part_of_speech", ""),
                card.get("difficulty", "beginner"),
                card.get("example_target", ""),
                card.get("example_native", ""),
                timestamp,
                timestamp,
            ),
        )

        return cursor.lastrowid


def list_cards(telegram_id: int, limit: int = 30):
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                phrase,
                translation,
                difficulty,
                times_reviewed,
                correct_count,
                wrong_count
            FROM cards
            WHERE telegram_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (telegram_id, limit),
        ).fetchall()

        return [dict(row) for row in rows]


def count_cards(telegram_id: int):
    with connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM cards
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()

        return row["total"]


def get_progress_stats(telegram_id: int):
    with connect() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN times_reviewed > 0 THEN 1 ELSE 0 END) AS reviewed,
                SUM(CASE WHEN times_reviewed >= 3 AND correct_count >= 3 THEN 1 ELSE 0 END) AS mastered,
                SUM(times_reviewed) AS total_reviews,
                SUM(correct_count) AS total_correct,
                SUM(wrong_count) AS total_wrong
            FROM cards
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()

        return {
            "total": row["total"] or 0,
            "reviewed": row["reviewed"] or 0,
            "mastered": row["mastered"] or 0,
            "total_reviews": row["total_reviews"] or 0,
            "total_correct": row["total_correct"] or 0,
            "total_wrong": row["total_wrong"] or 0,
        }


def get_review_cards(telegram_id: int, limit: int = 5):
    timestamp = now_iso()

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                phrase,
                translation,
                example_target,
                example_native,
                times_reviewed,
                correct_count,
                wrong_count
            FROM cards
            WHERE telegram_id = ?
            ORDER BY
                CASE
                    WHEN next_due_at IS NULL THEN 0
                    WHEN next_due_at <= ? THEN 0
                    ELSE 1
                END ASC,
                times_reviewed ASC,
                wrong_count DESC,
                RANDOM()
            LIMIT ?
            """,
            (telegram_id, timestamp, limit),
        ).fetchall()

        return [dict(row) for row in rows]


def get_next_due_at(correct: bool, new_correct_count: int):
    if not correct:
        return now_utc() + timedelta(hours=4)

    if new_correct_count <= 1:
        return now_utc() + timedelta(days=1)

    if new_correct_count == 2:
        return now_utc() + timedelta(days=3)

    if new_correct_count == 3:
        return now_utc() + timedelta(days=7)

    if new_correct_count == 4:
        return now_utc() + timedelta(days=14)

    return now_utc() + timedelta(days=30)


def mark_review(card_id: int, correct: bool):
    with connect() as conn:
        row = conn.execute(
            """
            SELECT correct_count
            FROM cards
            WHERE id = ?
            """,
            (card_id,),
        ).fetchone()

        if not row:
            return

        new_correct_count = row["correct_count"] + 1 if correct else row["correct_count"]
        next_due_at = get_next_due_at(correct, new_correct_count).isoformat()

        conn.execute(
            """
            UPDATE cards
            SET times_reviewed = times_reviewed + 1,
                correct_count = correct_count + ?,
                wrong_count = wrong_count + ?,
                last_reviewed_at = ?,
                next_due_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                1 if correct else 0,
                0 if correct else 1,
                now_iso(),
                next_due_at,
                now_iso(),
                card_id,
            ),
        )


def clear_cards(telegram_id: int):
    with connect() as conn:
        conn.execute(
            """
            DELETE FROM cards
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        )