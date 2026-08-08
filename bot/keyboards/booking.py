from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


DAY_LABELS = {
    "Monday": "Mon",
    "Tuesday": "Tue",
    "Wednesday": "Wed",
    "Thursday": "Thu",
    "Friday": "Fri",
    "Saturday": "Sat",
    "Sunday": "Sun",
}


def date_selection_keyboard(dates: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for value in dates:
        parsed = datetime.strptime(value, "%Y-%m-%d")
        day = DAY_LABELS.get(parsed.strftime("%A"), parsed.strftime("%A"))
        rows.append([InlineKeyboardButton(text=f"{parsed:%d.%m.%Y} ({day})", callback_data=f"date_{value}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def time_selection_keyboard(date: str, times: list[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for index in range(0, len(times), 3):
        rows.append([
            InlineKeyboardButton(text=value, callback_data=f"time_{date}_{value}")
            for value in times[index : index + 3]
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
