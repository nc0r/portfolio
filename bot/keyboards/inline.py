from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import PORTFOLIO_URL


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Book appointment", callback_data="book")],
            [InlineKeyboardButton(text="Services & prices", callback_data="prices")],
            [InlineKeyboardButton(text="View portfolio", callback_data="portfolio")],
            [InlineKeyboardButton(text="Cancel booking", callback_data="cancel_booking")],
        ]
    )


def service_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Classic Haircut", callback_data="service_Classic Haircut")],
            [InlineKeyboardButton(text="Beard Trim", callback_data="service_Beard Trim")],
            [InlineKeyboardButton(text="Haircut + Beard", callback_data="service_Haircut + Beard")],
        ]
    )


def portfolio_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Open gallery", url=PORTFOLIO_URL)]])


def subscribe_kb(link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Join channel", url=link)],
            [InlineKeyboardButton(text="Check access", callback_data="check_sub")],
        ]
    )
