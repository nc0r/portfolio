"""Database queries shared by the Telegram bot, web panel, and scheduler."""

from datetime import date as date_type, datetime
from typing import Any

from database.db import get_db_connection


class BookingConflictError(ValueError):
    """The user already has an active booking."""


class SlotUnavailableError(ValueError):
    """The requested slot does not exist or is already booked."""


def _row_dict(row: Any) -> dict | None:
    return dict(row) if row is not None else None


def get_user_booking(user_id: int) -> dict | None:
    today = date_type.today().isoformat()
    now_time = datetime.now().strftime("%H:%M")
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM bookings
            WHERE user_id = ? AND (date > ? OR (date = ? AND time >= ?))
            ORDER BY date, time LIMIT 1
            """,
            (user_id, today, today, now_time),
        ).fetchone()
    return _row_dict(row)


def get_booking(booking_id: int) -> dict | None:
    with get_db_connection() as connection:
        row = connection.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    return _row_dict(row)


def create_booking(*, user_id: int, name: str, phone: str, service: str, date: str, time: str, username: str | None) -> int:
    try:
        requested_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise SlotUnavailableError("Invalid date or time") from exc
    if requested_time <= datetime.now():
        raise SlotUnavailableError("Cannot book an appointment in the past")

    with get_db_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        today = date_type.today().isoformat()
        now_time = datetime.now().strftime("%H:%M")
        existing_user = connection.execute(
            """
            SELECT id FROM bookings
            WHERE user_id = ? AND (date > ? OR (date = ? AND time >= ?))
            LIMIT 1
            """,
            (user_id, today, today, now_time),
        ).fetchone()
        if existing_user:
            raise BookingConflictError("You already have an active appointment")

        existing_slot_booking = connection.execute(
            "SELECT id FROM bookings WHERE date = ? AND time = ? LIMIT 1", (date, time)
        ).fetchone()
        if existing_slot_booking:
            raise SlotUnavailableError("This time is already booked")

        updated = connection.execute(
            "UPDATE slots SET is_booked = 1 WHERE date = ? AND time = ? AND is_booked = 0",
            (date, time),
        )
        if updated.rowcount != 1:
            raise SlotUnavailableError("This slot is no longer available")

        cursor = connection.execute(
            """
            INSERT INTO bookings (user_id, name, phone, service, date, time, username)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, phone, service, date, time, username),
        )
        return int(cursor.lastrowid)


def cancel_user_booking(user_id: int) -> dict | None:
    today = date_type.today().isoformat()
    now_time = datetime.now().strftime("%H:%M")
    with get_db_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        booking = connection.execute(
            """
            SELECT * FROM bookings
            WHERE user_id = ? AND (date > ? OR (date = ? AND time >= ?))
            ORDER BY date, time LIMIT 1
            """,
            (user_id, today, today, now_time),
        ).fetchone()
        if booking is None:
            return None
        connection.execute("UPDATE slots SET is_booked = 0 WHERE date = ? AND time = ?", (booking["date"], booking["time"]))
        connection.execute("DELETE FROM bookings WHERE id = ?", (booking["id"],))
        return dict(booking)


def delete_booking(user_id: int) -> bool:
    return cancel_user_booking(user_id) is not None


def get_all_bookings(date: str | None = None) -> list[dict]:
    query = "SELECT * FROM bookings"
    parameters: tuple = ()
    if date:
        query += " WHERE date = ?"
        parameters = (date,)
    else:
        query += " WHERE date >= ?"
        parameters = (date_type.today().isoformat(),)
    query += " ORDER BY date, time"
    with get_db_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [dict(row) for row in rows]


def get_available_slots(date: str) -> list[str]:
    today = date_type.today().isoformat()
    now_time = datetime.now().strftime("%H:%M")
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT time FROM slots
            WHERE date = ? AND is_booked = 0
              AND (date > ? OR (date = ? AND time > ?))
            ORDER BY time
            """,
            (date, today, today, now_time),
        ).fetchall()
    return [row["time"] for row in rows]


def get_available_dates(start: str, end: str) -> list[str]:
    now_time = datetime.now().strftime("%H:%M")
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT date FROM slots
            WHERE is_booked = 0 AND date BETWEEN ? AND ?
              AND (date > ? OR (date = ? AND time > ?))
            ORDER BY date
            """,
            (start, end, date_type.today().isoformat(), date_type.today().isoformat(), now_time),
        ).fetchall()
    return [row["date"] for row in rows]
