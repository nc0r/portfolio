import html
import logging
import sqlite3
from datetime import date, datetime

from aiogram import F, Router, types

from config import ADMIN_ID
from database.db import get_db_connection
from database.models import get_all_bookings


router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def parse_slot(value_date: str, value_time: str) -> tuple[str, str]:
    parsed = datetime.strptime(f"{value_date} {value_time}", "%Y-%m-%d %H:%M")
    if parsed <= datetime.now():
        raise ValueError("Cannot add a slot in the past")
    return parsed.strftime("%Y-%m-%d"), parsed.strftime("%H:%M")


async def reject_unless_admin(message: types.Message) -> bool:
    if is_admin(message.from_user.id):
        return False
    await message.answer("You do not have admin access.")
    return True


@router.message(F.text == "/admin")
async def admin_panel(message: types.Message) -> None:
    if await reject_unless_admin(message):
        return
    await message.answer(
        "<b>BarberFlow Admin Panel:</b>\n\n"
        "<code>/add_slot YYYY-MM-DD HH:MM</code> - add an appointment slot\n"
        "<code>/delete_slot YYYY-MM-DD HH:MM</code> - delete a free slot\n"
        "<code>/view YYYY-MM-DD</code> - view the schedule\n"
        "<code>/stats</code> - booking statistics",
        parse_mode="HTML",
    )


@router.message(F.text.startswith("/add_slot"))
async def add_slot(message: types.Message) -> None:
    if await reject_unless_admin(message):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Format: <code>/add_slot YYYY-MM-DD HH:MM</code>", parse_mode="HTML")
        return
    try:
        value_date, value_time = parse_slot(parts[1], parts[2])
        with get_db_connection() as connection:
            connection.execute("INSERT INTO slots (date, time, is_booked) VALUES (?, ?, 0)", (value_date, value_time))
    except ValueError as exc:
        await message.answer(f"{exc}")
        return
    except sqlite3.IntegrityError:
        await message.answer("This slot already exists.")
        return
    except Exception:
        logger.exception("Failed to add slot")
        await message.answer("Could not add the slot.")
        return
    await message.answer(f"Slot added: {value_date} {value_time}")


@router.message(F.text.startswith("/delete_slot"))
async def delete_slot(message: types.Message) -> None:
    if await reject_unless_admin(message):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Format: <code>/delete_slot YYYY-MM-DD HH:MM</code>", parse_mode="HTML")
        return
    try:
        value_date, value_time = parse_slot(parts[1], parts[2])
    except ValueError as exc:
        await message.answer(f"{exc}")
        return
    with get_db_connection() as connection:
        cursor = connection.execute("DELETE FROM slots WHERE date = ? AND time = ? AND is_booked = 0", (value_date, value_time))
    if cursor.rowcount:
        await message.answer(f"Slot deleted: {value_date} {value_time}")
    else:
        await message.answer("Free slot was not found.")


@router.message(F.text.startswith("/view"))
async def view(message: types.Message) -> None:
    if await reject_unless_admin(message):
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Format: <code>/view YYYY-MM-DD</code>", parse_mode="HTML")
        return
    try:
        value_date = datetime.strptime(parts[1], "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        await message.answer("Invalid date.")
        return
    with get_db_connection() as connection:
        slots = connection.execute("SELECT time, is_booked FROM slots WHERE date = ? ORDER BY time", (value_date,)).fetchall()
    if not slots:
        await message.answer(f"No slots found for {value_date}.")
        return
    lines = [f"<b>Schedule for {value_date}:</b>", ""]
    lines.extend(f"{slot['time']} - {'booked' if slot['is_booked'] else 'free'}" for slot in slots)
    bookings = get_all_bookings(value_date)
    if bookings:
        lines.extend(["", "<b>Clients:</b>"])
        lines.extend(f"{html.escape(item['name'])} - {html.escape(item.get('service', 'Appointment'))} - {item['time']} - {item['phone']}" for item in bookings)
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "/stats")
async def stats(message: types.Message) -> None:
    if await reject_unless_admin(message):
        return
    today = date.today().isoformat()
    with get_db_connection() as connection:
        total = connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        active = connection.execute("SELECT COUNT(*) FROM bookings WHERE date >= ?", (today,)).fetchone()[0]
        occupied = connection.execute("SELECT COUNT(*) FROM slots WHERE is_booked = 1").fetchone()[0]
        free = connection.execute("SELECT COUNT(*) FROM slots WHERE is_booked = 0").fetchone()[0]
    await message.answer(
        f"<b>BarberFlow stats:</b>\n\nTotal bookings: {total}\n"
        f"Active bookings: {active}\nBooked slots: {occupied}\nFree slots: {free}",
        parse_mode="HTML",
    )
