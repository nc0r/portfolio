import logging

from aiogram import Bot, F, Router, types
from aiogram.filters import CommandStart

from config import BUSINESS_NAME, CHANNEL_ID, CHANNEL_LINK
from keyboards.inline import main_menu, subscribe_kb


router = Router()
logger = logging.getLogger(__name__)


async def check_subscription(bot: Bot, user_id: int) -> bool:
    if not CHANNEL_ID or not CHANNEL_LINK:
        return True
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in {"member", "administrator", "creator"}
    except Exception:
        logger.exception("Could not check channel membership for user %s", user_id)
        return False


async def show_menu(message: types.Message) -> None:
    await message.answer(
        f"<b>Welcome to {BUSINESS_NAME}!</b>\n\n"
        "Use this bot to book a haircut, check service prices, open the shop gallery, "
        "or cancel an existing appointment.",
        reply_markup=main_menu(),
        parse_mode="HTML",
    )


@router.message(CommandStart())
async def start(message: types.Message, bot: Bot) -> None:
    if not await check_subscription(bot, message.from_user.id):
        await message.answer(
            "Please join the shop channel before booking an appointment.",
            reply_markup=subscribe_kb(CHANNEL_LINK),
        )
        return
    await show_menu(message)


@router.callback_query(F.data == "check_sub")
async def check_sub(callback: types.CallbackQuery, bot: Bot) -> None:
    if await check_subscription(bot, callback.from_user.id):
        await callback.answer("Access confirmed")
        await show_menu(callback.message)
    else:
        await callback.answer("Access was not found", show_alert=True)
