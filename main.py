import asyncio
import logging
import os
import json
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message
from aiogram import BaseMiddleware

# --- CONFIGURATION ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN not found!")

def load_users_config():
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

USERS_CONFIG = load_users_config()
MIN_PARTICIPANTS = 2
DEFAULT_SLOTS_UTC = ["16:00", "16:30", "17:00", "17:30"]
YOGA_JOKES = [
    "Get your mats ready! Savasana won't do itself 🧘‍♀️",
    "The hardest part of yoga is unrolling the mat 😉",
    "Your back will say thank you! 🙏",
    "Don't be like a log, be like bamboo! 🌱",
    "Inhale - exhale. The main thing is not to fall asleep! 😴",
    "Yesterday I tried a new yoga pose. It's called 'Sleeping dog face down in the sofa'. Turned out perfectly!"
]
yoga_sessions = {}

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user and user.username and user.username.lower() in USERS_CONFIG:
            return await handler(event, data)
        return

dp.update.outer_middleware(AccessMiddleware())

class YogaState(StatesGroup):
    waiting_for_time = State()

# --- Helper Functions ---

def get_week_keyboard():
    builder = InlineKeyboardBuilder()
    now = datetime.now()
    
    # Days of the week abbreviations
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Generate exactly 7 days starting from today
    for i in range(7):
        day = now + timedelta(days=i)
        date_val = day.strftime('%Y-%m-%d')
        
        # Format label: "Mon 24.01"
        label = f"{weekdays[day.weekday()]} {day.strftime('%d.%m')}"
        
        builder.button(text=label, callback_data=f"day_{date_val}")
    
    # Arrange buttons in rows of 4
    builder.adjust(4)
    
    # Add a cancel button at the bottom row
    builder.row(types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_calendar"))
    
    return builder.as_markup()

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
    
    if not message.from_user or not message.from_user.username:
        await message.answer("❌ Set a Username in Telegram!")
        return

    msg = await message.answer(
        "📅 **Planning a session**\nChoose a day:",
        reply_markup=get_week_keyboard(),
        parse_mode="Markdown"
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
        # Simply delete the message with buttons
        await callback.message.delete()
    except Exception:
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
    selected_date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # IMPORTANT: save the date so process_time_button can see it
    await state.update_data(chosen_date=selected_date)
    username = callback.from_user.username.lower() if callback.from_user.username else ""
    user_offset = float(USERS_CONFIG.get(username, 0.0))
    
    builder = InlineKeyboardBuilder()
    for utc_time in DEFAULT_SLOTS_UTC:
        h, m = map(int, utc_time.split(':'))
        # Conversion UTC -> User's local time
        local_hour = int((h + user_offset) % 24)
        local_time_label = f"{local_hour:02d}:{m:02d}"
        builder.button(text=local_time_label, callback_data=f"time_{utc_time}")
    
    builder.adjust(2)

    builder.row(types.InlineKeyboardButton(
        text="⬅️ Back to dates", 
        callback_data="back_to_weeks")
    )

    await callback.message.edit_text(
        f"📅 **{selected_date.strftime('%d.%m')}**\nChoose time:",
        reply_markup=builder.as_markup()
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
        parse_mode="Markdown"
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
    if not isinstance(callback.message, Message) or not callback.from_user: return
    
    # Extract UTC time from the button
    utc_time_str = callback.data.split("_")[1]
    utc_h, utc_m = map(int, utc_time_str.split(':'))
    
    data = await state.get_data()
    chosen_date = data.get('chosen_date')
    if not chosen_date: return

    # Create time object in UTC
    dt_utc = chosen_date.replace(hour=utc_h, minute=utc_m)
    
    # Generate list of times for ALL based on saved UTC
    results = []
    for user_login, user_offset in USERS_CONFIG.items():
        # Calculate time for each: UTC + offset
        user_dt = dt_utc + timedelta(hours=float(user_offset))
        results.append(f"📍 **{user_login}**: `{user_dt.strftime('%H:%M (%d.%m)')}`")
    
    times_list = "\n".join(results)

    builder = InlineKeyboardBuilder()
    builder.button(text="🙋‍♂️ I'm in", callback_data="approve")
    builder.button(text="🏃‍♂️ Can't make it", callback_data="reject")
    builder.adjust(2)

    builder.row(types.InlineKeyboardButton(
        text="❌ Delete", 
        callback_data="cancel_session")
    )

    await callback.message.edit_text(
        f"🧘 **Yoga {dt_utc.strftime('%d.%m')}** (base UTC {utc_time_str})\n\n{times_list}\n\nShall we confirm?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
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
        # Delete the message so it doesn't hang in the chat
        await callback.message.delete()
    except Exception:
        # If deletion failed (e.g., too much time passed), just notify
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

    # Block repeated selection of the same option
    if action == "approve" and user_name in session["going"]:
        await callback.answer("You are already on the list! 😉")
        return
    if action == "reject" and user_name in session["not_going"]:
        await callback.answer("You have already marked that you won't come.")
        return

    # Update lists
    if action == "approve":
        session["going"].add(user_name)
        session["not_going"].discard(user_name)
    else:
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
    
    # Clear the main text from old statuses
    raw_text = callback.message.text
    # Find the start of the participants block to keep only the session time
    if "✅ Who is going:" in raw_text:
        base_text = raw_text.split("✅ Who is going:")[0].strip()
    else:
        base_text = raw_text.strip()

    # Form the bottom part of the message
    status_section = f"✅ Who is going: {going_str}\n❌ Can't make it: {not_going_str}"
    
    # Check minimum
    if count_going >= MIN_PARTICIPANTS:
        joke = random.choice(YOGA_JOKES)
        confirmation_text = (
            f"\n\n🎉 **Session confirmed!** (gathered {count_going}/{MIN_PARTICIPANTS})\n"
            f"---\n"
            f"\n✨ _{joke}_"
        )
    else:
        # If there are few people, write how many more are needed
        needed = MIN_PARTICIPANTS - count_going
        confirmation_text = f"\n\n⏳ Need at least {needed} more people to confirm."

    final_text = f"{base_text}\n\n{status_section}{confirmation_text}"

    await callback.message.edit_text(
        text=final_text,
        reply_markup=callback.message.reply_markup,
        parse_mode="Markdown"
    )
        
@dp.message(Command("shutdown"))
async def cmd_shutdown(message: Message):
    """
    Processes the /shutdown command to turn off the bot. Only the first user in config can execute this.

    Args:
        message (Message): The command message.
    """
    if not message.from_user or not message.from_user.username: return
    
    user_keys = list(USERS_CONFIG.keys())
    admin_username = user_keys[0] if user_keys else ""

    if message.from_user.username.lower() == admin_username:
        await message.answer("🛑 Bot shut down.")        
        await bot.session.close()
        await dp.stop_polling()
        
        print("Bot successfully finished work.")
        os._exit(0)

# --- STARTUP ---
async def main():
    """
    Entry point for the bot. Starts the polling loop.
    """
    print("🚀 Bot started!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())