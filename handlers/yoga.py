import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (
    MIN_PARTICIPANTS,
    YOGA_JOKES,
    YOGA_TEXT_USERNAME_REQUIRED,
    YOGA_TEXT_PLANNING_TITLE,
    YOGA_TEXT_TIME_TITLE,
    YOGA_TEXT_SESSION_SUMMARY,
    YOGA_TEXT_WINDOW_CLOSED,
    YOGA_TEXT_MESSAGE_DELETED,
    YOGA_TEXT_PLANNING_CANCELLED,
    YOGA_TEXT_ALREADY_GOING,
    YOGA_TEXT_ALREADY_NOT_GOING,
    YOGA_TEXT_STATUS_SECTION,
    YOGA_TEXT_SESSION_CONFIRMED,
    YOGA_TEXT_SESSION_NEED_MORE,
)
from states import YogaState
from views.yoga import (
    get_week_keyboard,
    get_yoga_time_keyboard,
    get_yoga_attendance_keyboard,
)
from utils import get_user_offset, convert_utc_to_local, validate_user, escape_markdown

logger = logging.getLogger(__name__)

yoga_router = Router()

# Global dictionary to store ongoing yoga sessions' attendance
yoga_sessions = {}

@yoga_router.message(Command("yoga"))
async def cmd_yoga(message: Message, state: FSMContext, yoga_users_map: dict):
    """
    Initiates the yoga session planning process. Clears current state and prompts user to select a day.
    """
    await state.clear()
    if not validate_user(message):
        await message.answer(YOGA_TEXT_USERNAME_REQUIRED)
        return

    await message.answer(
        YOGA_TEXT_PLANNING_TITLE,
        reply_markup=get_week_keyboard(),
        parse_mode="Markdown",
    )


@yoga_router.callback_query(F.data == "cancel_calendar")
async def process_cancel_calendar(callback: types.CallbackQuery, state: FSMContext):
    """
    Cancels the calendar interaction, clears the state, and deletes the message.
    """
    await state.clear()
    try:
        await callback.message.delete()
    except Exception as e:
        logger.debug("Failed to delete calendar message: %s", e)
        await callback.answer(YOGA_TEXT_WINDOW_CLOSED)
    await callback.answer()


@yoga_router.callback_query(F.data.startswith("day_"))
async def process_day_selection(callback: types.CallbackQuery, state: FSMContext, yoga_users_map: dict):
    """
    Shows available time slots for booking on the selected day based on the user's timezone.
    """
    date_str = callback.data.split("_")[1]
    selected_date = datetime.strptime(date_str, "%Y-%m-%d")

    await state.update_data(chosen_date=selected_date)
    username = (
        callback.from_user.username.lower() if callback.from_user.username else ""
    )
    user_offset = get_user_offset(username, yoga_users_map)  # Use the passed map

    await callback.message.edit_text(
        YOGA_TEXT_TIME_TITLE.format(date=selected_date.strftime("%d.%m")),
        reply_markup=get_yoga_time_keyboard(user_offset, selected_date),
    )


@yoga_router.callback_query(F.data == "back_to_weeks")
async def process_back_to_weeks(callback: types.CallbackQuery, state: FSMContext):
    """
    Returns the user to the day of the week selection menu.
    """
    await callback.message.edit_text(
        YOGA_TEXT_PLANNING_TITLE,
        reply_markup=get_week_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@yoga_router.callback_query(F.data.startswith("time_"))
async def process_time_button(callback: types.CallbackQuery, state: FSMContext, yoga_users_map: dict):
    """
    Processes time selection, calculates local times for all users, and shows the confirmation summary.
    """
    if not isinstance(callback.message, Message) or not callback.from_user:
        return

    utc_time_str = callback.data.split("_")[1]
    utc_h, utc_m = map(int, utc_time_str.split(":"))

    data = await state.get_data()
    chosen_date = data.get("chosen_date")
    if not chosen_date:
        return

    dt_utc = chosen_date.replace(hour=utc_h, minute=utc_m)

    results = []
    for user_login, user_offset in yoga_users_map.items():  # Use the passed map
        user_dt = convert_utc_to_local(dt_utc, float(user_offset))
        escaped_login = escape_markdown(user_login)
        results.append(f"📍 {escaped_login}: {user_dt.strftime('%H:%M')}")

    times_list = "\n".join(results)

    await callback.message.edit_text(
        YOGA_TEXT_SESSION_SUMMARY.format(
            date=dt_utc.strftime("%d.%m"),
            utc_time=utc_time_str,
            times=times_list,
        ),
        reply_markup=get_yoga_attendance_keyboard(),
        parse_mode="Markdown",
    )


@yoga_router.callback_query(F.data == "cancel_session")
async def process_cancel_session(callback: types.CallbackQuery, state: FSMContext):
    """
    Processes the 'Delete' button click, resets the FSM state, and deletes the session message.
    """
    await state.clear()
    try:
        await callback.message.delete()
        # Clean up session data if message is deleted
        if callback.message.message_id in yoga_sessions:
            del yoga_sessions[callback.message.message_id]
    except Exception as e:
        logger.debug("Failed to delete session message: %s", e)
        await callback.answer(YOGA_TEXT_MESSAGE_DELETED)

    await callback.answer(YOGA_TEXT_PLANNING_CANCELLED)


@yoga_router.callback_query(F.data.in_(["approve", "reject"]))
async def handle_attendance(callback: types.CallbackQuery):
    """
    Processes 'Going' or 'Cannot go' button clicks and updates the participant lists for the session.
    """
    msg_id = callback.message.message_id
    user_name = callback.from_user.first_name
    action = callback.data

    if msg_id not in yoga_sessions:
        yoga_sessions[msg_id] = {"going": set(), "not_going": set()}

    session = yoga_sessions[msg_id]
    if action == "approve":
        if user_name in session["going"]:
            await callback.answer(YOGA_TEXT_ALREADY_GOING)
            return
        session["going"].add(user_name)
        session["not_going"].discard(user_name)
    else:
        if user_name in session["not_going"]:
            await callback.answer(YOGA_TEXT_ALREADY_NOT_GOING)
            return
        session["not_going"].add(user_name)
        session["going"].discard(user_name)

    await update_session_message(callback)
    await callback.answer()


async def update_session_message(callback: types.CallbackQuery):
    """
    Updates the session message text with the current list of participants and status.
    """
    msg_id = callback.message.message_id
    session = yoga_sessions.get(msg_id, {"going": set(), "not_going": set()})

    count_going = len(session["going"])
    going_str = ", ".join(session["going"]) if session["going"] else "..."
    not_going_str = ", ".join(session["not_going"]) if session["not_going"] else "..."

    raw_text = callback.message.text or ""
    if "Shall we confirm?" in raw_text:
        base_text = raw_text.split("Shall we confirm?")[0].strip()
    elif "✅ Who is going:" in raw_text:
        base_text = raw_text.split("✅ Who is going:")[0].strip()
    else:
        base_text = raw_text.strip()

    status_section = YOGA_TEXT_STATUS_SECTION.format(
        going=going_str,
        not_going=not_going_str,
    )

    if count_going >= MIN_PARTICIPANTS:
        joke = random.choice(YOGA_JOKES)
        confirmation_text = "\n\n" + YOGA_TEXT_SESSION_CONFIRMED.format(
            count=count_going,
            min_participants=MIN_PARTICIPANTS,
            joke=joke,
        )
    else:
        needed = MIN_PARTICIPANTS - count_going
        confirmation_text = "\n\n" + YOGA_TEXT_SESSION_NEED_MORE.format(
            needed=needed
        )

    final_text = f"{base_text}\n\n{status_section}{confirmation_text}"

    await callback.message.edit_text(
        text=final_text,
        reply_markup=callback.message.reply_markup,
        parse_mode="Markdown",
    )
