"""SQLite connection management and forward-only schema migrations."""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from config import DATABASE_PATH


logger = logging.getLogger(__name__)


def _connect(path: Path | str | None = None) -> sqlite3.Connection:
    database_path = Path(path or DATABASE_PATH)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


@contextmanager
def get_db_connection(path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    connection = _connect(path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}


def init_db(path: Path | str | None = None) -> None:
    with get_db_connection(path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                service TEXT NOT NULL DEFAULT 'Barber appointment',
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                reminder_id TEXT,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                is_booked INTEGER NOT NULL DEFAULT 0 CHECK (is_booked IN (0, 1)),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        booking_columns = _column_names(connection, "bookings")
        if "username" not in booking_columns:
            connection.execute("ALTER TABLE bookings ADD COLUMN username TEXT")
        if "reminder_id" not in booking_columns:
            connection.execute("ALTER TABLE bookings ADD COLUMN reminder_id TEXT")
        if "service" not in booking_columns:
            connection.execute("ALTER TABLE bookings ADD COLUMN service TEXT NOT NULL DEFAULT 'Barber appointment'")

        connection.execute(
            """
            INSERT INTO slots (date, time, is_booked)
            SELECT DISTINCT b.date, b.time, 1
            FROM bookings b
            WHERE NOT EXISTS (
                SELECT 1 FROM slots s WHERE s.date = b.date AND s.time = b.time
            )
            """
        )
        connection.execute(
            """
            UPDATE slots
            SET is_booked = 1
            WHERE (date, time) IN (
                SELECT date, time FROM bookings
            )
            """
        )
        connection.execute(
            """
            DELETE FROM slots
            WHERE id NOT IN (
                SELECT MIN(id) FROM slots GROUP BY date, time
            )
            """
        )
        connection.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
            CREATE INDEX IF NOT EXISTS idx_bookings_date_time ON bookings(date, time);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_slots_unique_date_time ON slots(date, time);
            CREATE INDEX IF NOT EXISTS idx_slots_booked ON slots(is_booked);
            """
        )
    logger.info("Database initialized at %s", path or DATABASE_PATH)
