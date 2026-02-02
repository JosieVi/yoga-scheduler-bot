import asyncio
import logging
import os
import json
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest

# --- CONFIGURATION ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN not found!")

from config import (
    MIN_PARTICIPANTS,
    DEFAULT_SLOTS_UTC,
    PLANK_MIN_SECONDS,
    PLANK_INITIAL_SECONDS,
    YOGA_JOKES,
    PLANK_MOTIVATION,
)


def load_users(filename: str) -> dict:
    """Load user timezone offsets from JSON file. Returns empty dict on error."""
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Failed to load {filename}: {e}")
    return {}


YOGA_USERS = load_users("users_yoga.json")
PLANK_USERS = load_users("users_plank.json")

yoga_sessions = {}

# --- LOGGER & BOT SETUP ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class YogaState(StatesGroup):
    waiting_for_time = State()


class PlankState(StatesGroup):
    adjusting = State()


# --- Helper Functions ---


def get_week_keyboard():
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


def get_user_offset(username: str, user_dict: dict) -> float:
    """Get timezone offset (hours) for a username from provided dict."""
    if not username:
        return 0.0
    try:
        return float(user_dict.get(username.lower(), 0.0))
    except (TypeError, ValueError):
        return 0.0


def convert_utc_to_local(dt_utc: datetime, user_offset: float) -> datetime:
    return dt_utc + timedelta(hours=user_offset)


def format_time(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}" if m > 0 else f"{s} sec"


def validate_user(message: Message) -> bool:
    return bool(message.from_user and message.from_user.username)


# --- HANDLERS ---


@dp.message(Command("yoga"))
async def cmd_yoga(message: Message, state: FSMContext):
    """
    Initiates the yoga session planning process. Clears current state and prompts user to select a day.

    Args:
        message (Message): The incoming message object.
        state (FSMContext): The state context for the current user.
    """
    await state.clear()
    if not validate_user(message):
        await message.answer("❌ Set a Username in Telegram!")
        return

    await message.answer(
        "📅 **Planning a session**\nChoose a day:",
        reply_markup=get_week_keyboard(),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data == "cancel_calendar")
async def process_cancel_calendar(callback: types.CallbackQuery, state: FSMContext):
    """
    Cancels the calendar interaction, clears the state, and deletes the message.

    Args:
        callback (types.CallbackQuery): The callback query object.
        state (FSMContext): The state context for the current user.
    """
    await state.clear()
    try:
        await callback.message.delete()
    except Exception as e:
        logger.debug("Failed to delete calendar message: %s", e)
        await callback.answer("Window closed")
    await callback.answer()


@dp.callback_query(F.data.startswith("day_"))
async def process_day_selection(callback: types.CallbackQuery, state: FSMContext):
    """
    Shows available time slots for booking on the selected day based on the user's timezone.

    Args:
        callback (types.CallbackQuery): The callback query containing the selected date.
        state (FSMContext): The state context to store the chosen date.
    """
    date_str = callback.data.split("_")[1]
    selected_date = datetime.strptime(date_str, "%Y-%m-%d")

    await state.update_data(chosen_date=selected_date)
    username = (
        callback.from_user.username.lower() if callback.from_user.username else ""
    )
    user_offset = get_user_offset(username, YOGA_USERS)

    builder = InlineKeyboardBuilder()
    for utc_time in DEFAULT_SLOTS_UTC:
        h, m = map(int, utc_time.split(":"))
        local_hour = int((h + user_offset) % 24)
        local_time_label = f"{local_hour:02d}:{m:02d}"
        builder.button(text=local_time_label, callback_data=f"time_{utc_time}")

    builder.adjust(2)
    builder.row(
        types.InlineKeyboardButton(
            text="⬅️ Back to dates", callback_data="back_to_weeks"
        )
    )

    await callback.message.edit_text(
        f"📅 **{selected_date.strftime('%d.%m')}**\nChoose time:",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "back_to_weeks")
async def process_back_to_weeks(callback: types.CallbackQuery, state: FSMContext):
    """
    Returns the user to the day of the week selection menu.

    Args:
        callback (types.CallbackQuery): The callback query object.
        state (FSMContext): The state context (unused here but required by signature).
    """
    await callback.message.edit_text(
        "📅 **Planning a session**\nChoose a day:",
        reply_markup=get_week_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("time_"))
async def process_time_button(callback: types.CallbackQuery, state: FSMContext):
    """
    Processes time selection, calculates local times for all users, and shows the confirmation summary.

    Args:
        callback (types.CallbackQuery): The callback query containing the selected UTC time.
        state (FSMContext): The state context to retrieve the chosen date.
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
    for user_login, user_offset in YOGA_USERS.items():
        user_dt = convert_utc_to_local(dt_utc, float(user_offset))
        # Escape markdown special characters (underscore, asterisk, etc.)
        escaped_login = user_login.replace("_", "\\_").replace("*", "\\*")
        results.append(f"📍 {escaped_login}: {user_dt.strftime('%H:%M')}")

    times_list = "\n".join(results)

    builder = InlineKeyboardBuilder()
    builder.button(text="🙋‍♂️ I'm in", callback_data="approve")
    builder.button(text="🏃‍♂️ Not going", callback_data="reject")
    builder.adjust(2)
    builder.row(
        types.InlineKeyboardButton(text="❌ Delete", callback_data="cancel_session")
    )

    await callback.message.edit_text(
        f"🧘 **Yoga {dt_utc.strftime('%d.%m')}** (base UTC {utc_time_str})\n\n{times_list}\n\nShall we confirm?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data == "cancel_session")
async def process_cancel_session(callback: types.CallbackQuery, state: FSMContext):
    """
    Processes the 'Delete' button click, resets the FSM state, and deletes the session message.

    Args:
        callback (types.CallbackQuery): The callback query object.
        state (FSMContext): The state context to be cleared.
    """
    await state.clear()
    try:
        await callback.message.delete()
    except Exception as e:
        logger.debug("Failed to delete session message: %s", e)
        await callback.answer("Message deleted or hidden")

    await callback.answer("Planning cancelled")


@dp.callback_query(F.data.in_(["approve", "reject"]))
async def handle_attendance(callback: types.CallbackQuery):
    """
    Processes 'Going' or 'Cannot go' button clicks and updates the participant lists for the session.

    Args:
        callback (types.CallbackQuery): The callback query containing the action ('approve' or 'reject').
    """
    msg_id = callback.message.message_id
    user_name = callback.from_user.first_name
    action = callback.data

    if msg_id not in yoga_sessions:
        yoga_sessions[msg_id] = {"going": set(), "not_going": set()}

    session = yoga_sessions[msg_id]
    if action == "approve":
        if user_name in session["going"]:
            await callback.answer("You are already on the list! 😉")
            return
        session["going"].add(user_name)
        session["not_going"].discard(user_name)
    else:
        if user_name in session["not_going"]:
            await callback.answer("You have already marked that you won't come.")
            return
        session["not_going"].add(user_name)
        session["going"].discard(user_name)

    await update_session_message(callback)
    await callback.answer()


async def update_session_message(callback: types.CallbackQuery):
    """
    Updates the session message text with the current list of participants and status.

    Args:
        callback (types.CallbackQuery): The callback query associated with the message to update.
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

    status_section = f"✅ Who is going: {going_str}\n❌ Can't make it: {not_going_str}"

    if count_going >= MIN_PARTICIPANTS:
        joke = random.choice(YOGA_JOKES)
        confirmation_text = (
            f"\n\n🎉 **Session confirmed!** (gathered {count_going}/{MIN_PARTICIPANTS})\n"
            f"---\n\n✨ _{joke}_"
        )
    else:
        needed = MIN_PARTICIPANTS - count_going
        confirmation_text = f"\n\n⏳ Need at least {needed} more people to confirm."

    final_text = f"{base_text}\n\n{status_section}{confirmation_text}"

    await callback.message.edit_text(
        text=final_text,
        reply_markup=callback.message.reply_markup,
        parse_mode="Markdown",
    )


@dp.message(Command("plank"))
async def cmd_plank(message: Message, state: FSMContext):
    """
    Initiates the plank challenge by prompting the user to adjust their plank time.

    Args:
        message (Message): The message containing the command.
        state (FSMContext): The state context for the FSM.
    """
    if not validate_user(message):
        await message.answer("❌ Set a Username in Telegram!")
        return

    await state.set_state(PlankState.adjusting)
    await state.update_data(current_seconds=PLANK_INITIAL_SECONDS)

    await message.answer(
        f"💪 **Plank Challenge**\n{message.from_user.first_name}, adjust your result:",
        reply_markup=get_plank_slider_keyboard(PLANK_INITIAL_SECONDS),
        parse_mode="Markdown",
    )


def get_plank_slider_keyboard(seconds: int) -> types.InlineKeyboardMarkup:
    """
    Generates an inline keyboard for adjusting plank time.

    Args:
        seconds (int): The current number of seconds for the plank.

    Returns:
        InlineKeyboardMarkup: The generated keyboard markup.
    """
    builder = InlineKeyboardBuilder()

    time_str = format_time(seconds)

    # Row 1: Fine-tuning (5 sec)
    builder.row(
        types.InlineKeyboardButton(text="➖ 5s", callback_data="plank_adj_-5"),
        types.InlineKeyboardButton(text=f"⏱ {time_str}", callback_data="ignore"),
        types.InlineKeyboardButton(text="➕ 5s", callback_data="plank_adj_5"),
    )

    # Row 2: Quick adjustment (10 sec)
    builder.row(
        types.InlineKeyboardButton(text="➖ 10s", callback_data="plank_adj_-10"),
        types.InlineKeyboardButton(text="➕ 10s", callback_data="plank_adj_10"),
    )

    # Row 3: Controls
    builder.row(
        types.InlineKeyboardButton(
            text="✅ Confirm", callback_data=f"plank_final_{time_str}"
        ),
        types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_plank"),
    )
    return builder.as_markup()


@dp.callback_query(F.data == "cancel_plank")
async def process_cancel_plank(callback: types.CallbackQuery):
    """Delete the plank selection message."""
    try:
        await callback.message.delete()
    except Exception as e:
        logger.debug("Failed to delete plank message: %s", e)
        await callback.answer("Window closed")
    await callback.answer()


@dp.callback_query(F.data.startswith("plank_adj_"))
async def process_plank_adjustment(callback: types.CallbackQuery, state: FSMContext):
    """
    Adjusts the plank time based on user input and updates the inline keyboard.

    Args:
        callback (types.CallbackQuery): The callback query containing the adjustment data.
        state (FSMContext): The state context for the FSM.
    """
    adjustment = int(callback.data.split("_")[2])

    data = await state.get_data()
    current_seconds = data.get("current_seconds", PLANK_INITIAL_SECONDS)
    new_seconds = max(PLANK_MIN_SECONDS, current_seconds + adjustment)

    if new_seconds == current_seconds:
        await callback.answer()
        return

    await state.update_data(current_seconds=new_seconds)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_plank_slider_keyboard(new_seconds)
        )
        await callback.answer()
    except TelegramRetryAfter as e:
        await callback.answer(f"Too fast! Wait {e.retry_after}s", show_alert=True)
    except TelegramBadRequest:
        await callback.answer()


@dp.callback_query(F.data.startswith("plank_final_"))
async def process_plank_final(callback: types.CallbackQuery, state: FSMContext):
    """
    Finalizes the plank challenge, calculates the user's local date, and displays the result.

    Args:
        callback (types.CallbackQuery): The callback query containing the final result.
        state (FSMContext): The state context for the FSM.
    """
    result = callback.data.split("_")[2]
    username = (
        callback.from_user.username.lower() if callback.from_user.username else ""
    )
    user_name = callback.from_user.first_name

    user_offset = get_user_offset(username, PLANK_USERS)
    now_utc = datetime.now(timezone.utc)
    user_time = convert_utc_to_local(now_utc, user_offset)
    date_today = user_time.strftime("%d.%m.%Y")

    note = random.choice(PLANK_MOTIVATION)
    final_text = (
        f"🏆 **Plank Completed!**\n\n"
        f"👤 **User:** {user_name}\n"
        f"⏱ **Result:** {result}\n"
        f"📅 **Date:** {date_today}\n\n"
        f"_{note}_"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back", callback_data="back_to_plank")
    builder.button(text="❌ Delete", callback_data="cancel_plank")
    builder.adjust(2)

    await state.clear()
    await callback.message.edit_text(
        final_text, reply_markup=builder.as_markup(), parse_mode="Markdown"
    )
    await callback.answer("Result saved!")


@dp.callback_query(F.data == "ignore")
async def process_ignore(callback: types.CallbackQuery):
    """Empty handler for the central time button to prevent errors."""
    await callback.answer()


@dp.callback_query(F.data == "back_to_plank")
async def process_back_to_plank(callback: types.CallbackQuery, state: FSMContext):
    """
    Returns the user to the interactive slider.
    Resets the state to 'adjusting' with default 60 seconds.
    """
    await state.set_state(PlankState.adjusting)
    await state.update_data(current_seconds=PLANK_INITIAL_SECONDS)

    await callback.message.edit_text(
        f"💪 **Plank Challenge**\n{callback.from_user.first_name}, adjust your result:",
        reply_markup=get_plank_slider_keyboard(PLANK_INITIAL_SECONDS),
        parse_mode="Markdown",
    )
    await callback.answer()


@dp.message(Command("shutdown"))
async def cmd_shutdown(message: Message):
    """
    Processes the /shutdown command to turn off the bot. Only the first user in config can execute this.

    Args:
        message (Message): The command message.
    """
    if not validate_user(message):
        return

    user_keys = list(YOGA_USERS.keys())
    admin_username = user_keys[0] if user_keys else ""

    if message.from_user.username.lower() == admin_username:
        await message.answer("🛑 Bot shut down.")
        logger.info("Bot shutdown initiated by admin: %s", message.from_user.username)
        await bot.session.close()
        await dp.stop_polling()
        os._exit(0)


# --- STARTUP ---
async def main():
    """
    Entry point for the bot. Starts the polling loop.
    """
    print("🚀 Bot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
