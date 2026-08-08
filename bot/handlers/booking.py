import html
import logging
import re
from datetime import date, timedelta

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, BOOKING_DAYS_AHEAD
from database.models import (
    BookingConflictError,
    SlotUnavailableError,
    create_booking,
    get_available_dates,
    get_available_slots,
    get_user_booking,
)
from keyboards.booking import date_selection_keyboard, time_selection_keyboard
from keyboards.inline import main_menu, service_keyboard
from scheduler.scheduler import schedule_reminder
from states.booking_states import BookingState


router = Router()
logger = logging.getLogger(__name__)
PHONE_PATTERN = re.compile(r"^\+?[0-9]{10,15}$")


@router.callback_query(F.data == "book")
async def start_booking(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    existing = get_user_booking(callback.from_user.id)
    if existing:
        await callback.message.answer(
            "<b>You already have an active appointment:</b>\n\n"
            f"Service: {existing.get('service', 'Barber appointment')}\n"
            f"Date: {existing['date']}\nTime: {existing['time']}\n\n"
            "Cancel the current booking before choosing a new slot.",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )
        return
    await state.clear()
    await state.set_state(BookingState.choosing_service)
    await callback.message.answer("Choose a service:", reply_markup=service_keyboard())


@router.callback_query(BookingState.choosing_service, F.data.startswith("service_"))
async def process_service_selection(callback: types.CallbackQuery, state: FSMContext) -> None:
    service = callback.data.removeprefix("service_")
    today = date.today()
    end = today + timedelta(days=max(BOOKING_DAYS_AHEAD, 1))
    dates = get_available_dates(today.isoformat(), end.isoformat())
    if not dates:
        await callback.message.answer(
            "There are no available appointment slots right now. Please try again later.",
            reply_markup=main_menu(),
        )
        await state.clear()
        return
    await state.update_data(service=service)
    await state.set_state(BookingState.choosing_date)
    await callback.answer()
    await callback.message.answer(
        f"{service} selected. Choose an appointment date:",
        reply_markup=date_selection_keyboard(dates),
    )


@router.callback_query(BookingState.choosing_date, F.data.startswith("date_"))
async def process_date_selection(callback: types.CallbackQuery, state: FSMContext) -> None:
    selected_date = callback.data.removeprefix("date_")
    times = get_available_slots(selected_date)
    if not times:
        await callback.answer("No appointment slots remain for this date", show_alert=True)
        return
    await state.update_data(date=selected_date)
    await state.set_state(BookingState.choosing_time)
    await callback.answer()
    await callback.message.answer(
        f"Date {selected_date} selected. Choose a time:",
        reply_markup=time_selection_keyboard(selected_date, times),
    )


@router.callback_query(BookingState.choosing_time, F.data.startswith("time_"))
async def process_time_selection(callback: types.CallbackQuery, state: FSMContext) -> None:
    try:
        _, selected_date, selected_time = callback.data.split("_", 2)
    except ValueError:
        await callback.answer("Invalid slot format", show_alert=True)
        return
    data = await state.get_data()
    if data.get("date") != selected_date or selected_time not in get_available_slots(selected_date):
        await callback.answer("This time is no longer available", show_alert=True)
        return
    await state.update_data(time=selected_time)
    await state.set_state(BookingState.entering_name)
    await callback.answer()
    await callback.message.answer(f"Time {selected_time} selected. Enter your name for the booking:")


@router.message(BookingState.entering_name)
async def get_name(message: types.Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not 2 <= len(name) <= 50:
        await message.answer("Name must contain 2 to 50 characters.")
        return
    await state.update_data(name=name)
    await state.set_state(BookingState.entering_phone)
    await message.answer("Name saved. Enter a contact phone number, for example +12025550123.")


@router.message(BookingState.entering_phone)
async def finish_booking(message: types.Message, state: FSMContext, bot: Bot) -> None:
    phone = re.sub(r"[\s()-]", "", message.text or "")
    if not PHONE_PATTERN.fullmatch(phone):
        await message.answer("Invalid phone number format.")
        return
    data = await state.get_data()
    try:
        booking_id = create_booking(
            user_id=message.from_user.id,
            name=data["name"],
            phone=phone,
            service=data["service"],
            date=data["date"],
            time=data["time"],
            username=message.from_user.username,
        )
    except (BookingConflictError, SlotUnavailableError) as exc:
        await state.clear()
        await message.answer(f"{exc}", reply_markup=main_menu())
        return
    except Exception:
        logger.exception("Failed to create booking")
        await message.answer("Could not create the appointment. Please try again.")
        return

    schedule_reminder(bot, booking_id, data["date"], data["time"])
    safe_name = html.escape(data["name"])
    safe_service = html.escape(data["service"])
    try:
        await bot.send_message(
            ADMIN_ID,
            "<b>New barber shop appointment:</b>\n"
            f"Service: {safe_service}\nName: {safe_name}\nPhone: {phone}\n"
            f"Date: {data['date']}\nTime: {data['time']}\n"
            f"Telegram user ID: {message.from_user.id}",
            parse_mode="HTML",
        )
    except Exception:
        logger.exception("Booking %s created, but admin notification failed", booking_id)

    await state.clear()
    await message.answer(
        "<b>Your appointment is booked.</b>\n\n"
        f"Service: {safe_service}\nName: {safe_name}\n"
        f"Date: {data['date']}\nTime: {data['time']}",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )
