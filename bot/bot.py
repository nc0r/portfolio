import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError

from config import BOT_TOKEN, validate_bot_config
from database.db import init_db
from handlers import admin, booking, subscription, user
from scheduler.scheduler import restore_reminders, scheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    validate_bot_config()
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(subscription.router)
    dispatcher.include_router(user.router)
    dispatcher.include_router(booking.router)
    dispatcher.include_router(admin.router)

    scheduler.start()
    restore_reminders(bot)
    logger.info("Bot is starting long polling")
    try:
        await dispatcher.start_polling(bot)
    except TelegramAPIError:
        logger.exception("Telegram API error")
        raise
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
