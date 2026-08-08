"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*args, **kwargs):
        return False


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _int_env(name: str, default: int = 0) -> int:
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip().strip('"')
ADMIN_ID = _int_env("ADMIN_ID")
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "database.db"))).expanduser()

BUSINESS_NAME = os.getenv("BUSINESS_NAME", "BarberFlow Studio")
PORTFOLIO_URL = os.getenv("PORTFOLIO_URL", "https://example.com/barber-portfolio")
PRICE_LIST = os.getenv(
    "PRICE_LIST",
    "Classic Haircut - <b>$25</b>\n"
    "Beard Trim - <b>$15</b>\n"
    "Haircut + Beard - <b>$35</b>",
)

APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Europe/Kyiv")
BOOKING_DAYS_AHEAD = _int_env("BOOKING_DAYS_AHEAD", 60)
REMINDER_HOURS = _int_env("REMINDER_HOURS", 24)

CHANNEL_ID = _int_env("CHANNEL_ID")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "").strip()

WEB_ADMIN_PASSWORD = os.getenv("WEB_ADMIN_PASSWORD", "").strip()
WEB_SECRET_KEY = os.getenv("WEB_SECRET_KEY", "change-me-before-production").strip()
WEB_COOKIE_SECURE = os.getenv("WEB_COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}


def validate_bot_config() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured. Add it to .env")
    if not ADMIN_ID:
        raise RuntimeError("ADMIN_ID is not configured. Add it to .env")
