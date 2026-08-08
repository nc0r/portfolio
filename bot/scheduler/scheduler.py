"""Reminder scheduling with database-backed recovery after restarts."""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import APP_TIMEZONE, REMINDER_HOURS
from database.models import get_all_bookings, get_booking


logger = logging.getLogger(__name__)
timezone = ZoneInfo(APP_TIMEZONE)
scheduler = AsyncIOScheduler(timezone=timezone)


async def send_reminder(bot: Bot, booking_id: int) -> None:
    booking = get_booking(booking_id)
    if not booking:
        logger.info("Skipping reminder for deleted booking %s", booking_id)
        return
    await bot.send_message(
        booking["user_id"],
        "<b>Appointment reminder</b>\n\n"
        f"Service: {booking.get('service', 'Barber appointment')}\n"
        f"Date: {booking['date']}\nTime: {booking['time']}\n\n"
        "We look forward to seeing you at the shop.",
        parse_mode="HTML",
    )


def schedule_reminder(bot: Bot, booking_id: int, date: str, time: str) -> bool:
    visit_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone)
    reminder_time = visit_time - timedelta(hours=REMINDER_HOURS)
    if reminder_time <= datetime.now(timezone):
        logger.info("Booking %s is too close for an advance reminder", booking_id)
        return False
    scheduler.add_job(
        send_reminder,
        "date",
        run_date=reminder_time,
        args=[bot, booking_id],
        id=str(booking_id),
        name=f"reminder_booking_{booking_id}",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    return True


def restore_reminders(bot: Bot) -> int:
    restored = 0
    for booking in get_all_bookings():
        try:
            restored += int(schedule_reminder(bot, booking["id"], booking["date"], booking["time"]))
        except (ValueError, OSError):
            logger.exception("Invalid reminder data for booking %s", booking["id"])
    logger.info("Restored %s reminder(s)", restored)
    return restored


def cancel_reminder(booking_id: int) -> None:
    try:
        scheduler.remove_job(str(booking_id))
    except JobLookupError:
        pass


def get_scheduled_reminders() -> list[tuple]:
    return [(job.id, job.name, job.next_run_time) for job in scheduler.get_jobs()]
