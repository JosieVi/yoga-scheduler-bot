from datetime import datetime, timedelta

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (
    DEFAULT_SLOTS_UTC,
    YOGA_BTN_BACK_TO_DATES,
    YOGA_BTN_IM_IN,
    YOGA_BTN_NOT_GOING,
    YOGA_BTN_DELETE,
)


def get_week_keyboard() -> types.InlineKeyboardMarkup:
    """Keyboard for selecting one of the next 7 days."""
    builder = InlineKeyboardBuilder()
    now = datetime.now()

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i in range(7):
        day = now + timedelta(days=i)
        date_val = day.strftime("%Y-%m-%d")
        label = f"{weekdays[day.weekday()]} {day.strftime('%d.%m')}"
        builder.button(text=label, callback_data=f"day_{date_val}")

    builder.adjust(3)
    builder.row(
        types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_calendar")
    )
    return builder.as_markup()


def get_yoga_time_keyboard(
    user_offset: float, chosen_date: datetime
) -> types.InlineKeyboardMarkup:
    """Keyboard for yoga time slots converted from UTC to user's local time."""
    builder = InlineKeyboardBuilder()

    for utc_time in DEFAULT_SLOTS_UTC:
        h, m = map(int, utc_time.split(":"))
        local_hour = int((h + user_offset) % 24)
        local_time_label = f"{local_hour:02d}:{m:02d}"
        builder.button(text=local_time_label, callback_data=f"time_{utc_time}")

    builder.adjust(2)
    builder.row(
        types.InlineKeyboardButton(
            text=YOGA_BTN_BACK_TO_DATES, callback_data="back_to_weeks"
        )
    )

    return builder.as_markup()


def get_yoga_attendance_keyboard() -> types.InlineKeyboardMarkup:
    """Keyboard for confirming / rejecting yoga attendance."""
    builder = InlineKeyboardBuilder()
    builder.button(text=YOGA_BTN_IM_IN, callback_data="approve")
    builder.button(text=YOGA_BTN_NOT_GOING, callback_data="reject")
    builder.adjust(2)
    builder.row(
        types.InlineKeyboardButton(
            text=YOGA_BTN_DELETE, callback_data="cancel_session"
        )
    )
    return builder.as_markup()

