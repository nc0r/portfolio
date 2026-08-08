import logging

from aiogram import F, Router, types

from config import PRICE_LIST
from database.models import cancel_user_booking
from keyboards.inline import main_menu, portfolio_kb
from scheduler.scheduler import cancel_reminder


router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "prices")
async def prices(callback: types.CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        f"<b>Services & prices:</b>\n\n{PRICE_LIST}\n\n"
        "Tap \"Book appointment\" to choose a service and available time.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "portfolio")
async def portfolio(callback: types.CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "<b>Shop portfolio:</b>\n\nOpen the gallery to show recent haircuts and beard work.",
        parse_mode="HTML",
        reply_markup=portfolio_kb(),
    )


@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: types.CallbackQuery) -> None:
    await callback.answer()
    booking = cancel_user_booking(callback.from_user.id)
    if not booking:
        await callback.message.answer("You do not have an active appointment.", reply_markup=main_menu())
        return
    cancel_reminder(booking["id"])
    await callback.message.answer(
        "Appointment cancelled.\n\n"
        f"Service: {booking.get('service', 'Barber appointment')}\n"
        f"Date: {booking['date']}\nTime: {booking['time']}",
        reply_markup=main_menu(),
    )
