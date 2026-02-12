import logging
import random
from datetime import datetime, timedelta, timezone

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest

from db.database import (
    save_plank_result,
    get_user_stats,
    delete_plank_result,
    get_plank_history,
    get_plank_details,
)
from utils import (
    get_user_offset,
    format_time,
    format_time_compact,
    validate_user,
    convert_utc_to_local,
    to_seconds,
)
from views.plank import (
    get_plank_slider_keyboard,
    get_plank_result_keyboard,
    get_plank_stats_keyboard,
    get_plank_stats_details_keyboard,
    generate_progress_graph,
)
from states import PlankState
from config import (
    PLANK_MIN_SECONDS,
    PLANK_INITIAL_SECONDS,
    PLANK_MOTIVATION,
    PLANK_TEXT_USERNAME_REQUIRED,
    PLANK_TEXT_CHALLENGE_TITLE,
    PLANK_TEXT_DELETE_SUCCESS,
    PLANK_TEXT_DELETE_NONE,
    PLANK_TEXT_DELETE_ERROR,
    PLANK_TEXT_TOO_FAST,
    PLANK_TEXT_PLANK_COMPLETED,
    PLANK_TEXT_STATS_HEADER,
    PLANK_TEXT_STATS_WEEK_TITLE,
    PLANK_TEXT_STATS_MONTH_TITLE,
    PLANK_TEXT_STATS_TAGLINE,
    PLANK_TEXT_NO_DATA,
    PLANK_TEXT_DETAILS_HEADER,
    PLANK_TEXT_GRAPH_NO_DATA,
    PLANK_TEXT_GRAPH_CAPTION,
    PLANK_TEXT_GRAPH_ERROR,
)

logger = logging.getLogger(__name__)

plank_router = Router()


def _build_stats_text(data: dict) -> str:
    """Build full plank statistics text for 7 and 30 days."""
    return (
        PLANK_TEXT_STATS_HEADER
        + PLANK_TEXT_STATS_WEEK_TITLE
        + f" • Total time: <code>{format_time(data[7]['total'])}</code>\n"
        + f" • Attempts: <code>{data[7]['count']}</code>\n"
        + f" • Average: <code>{format_time(data[7]['avg'])}</code>\n"
        + f" • Best: <code>{format_time(data[7]['max'])}</code> 🏆\n\n"
        + PLANK_TEXT_STATS_MONTH_TITLE
        + f" • Total time: <code>{format_time(data[30]['total'])}</code>\n"
        + f" • Attempts: <code>{data[30]['count']}</code>\n"
        + f" • Average: <code>{format_time(data[30]['avg'])}</code>\n"
        + f" • Best: <code>{format_time(data[30]['max'])}</code> 🦁\n\n"
        + PLANK_TEXT_STATS_TAGLINE
    )

@plank_router.message(Command("plank"))
async def cmd_plank(message: Message, state: FSMContext):
    """
    Initiates the plank challenge by prompting the user to adjust their plank time.
    """
    if not validate_user(message):
        await message.answer(PLANK_TEXT_USERNAME_REQUIRED)
        return

    await state.set_state(PlankState.adjusting)
    await state.update_data(current_seconds=PLANK_INITIAL_SECONDS)

    await message.answer(
        PLANK_TEXT_CHALLENGE_TITLE.format(
            user_name=message.from_user.first_name
        ),
        reply_markup=get_plank_slider_keyboard(PLANK_INITIAL_SECONDS),
        parse_mode="Markdown",
    )


@plank_router.callback_query(F.data.startswith("cancel_plank:"))
async def process_cancel_plank(callback: types.CallbackQuery):
    """Deletes the specific record from DB and removes the message."""
    try:
        record_id = int(callback.data.split(":")[1])
        if record_id > 0:  # Only try to delete if it's a valid ID
            await delete_plank_result(record_id)
            await callback.answer(PLANK_TEXT_DELETE_SUCCESS)
        else:
            await callback.answer(PLANK_TEXT_DELETE_NONE, show_alert=True)

        await callback.message.delete()
    except Exception as e:
        logger.debug("Failed to delete plank message or record: %s", e)
        await callback.answer(PLANK_TEXT_DELETE_ERROR)
    # No need for a second callback.answer() if one was already made


@plank_router.callback_query(F.data.startswith("plank_adj_"))
async def process_plank_adjustment(callback: types.CallbackQuery, state: FSMContext):
    """
    Adjusts the plank time based on user input and updates the inline keyboard.
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
        await callback.answer(
            PLANK_TEXT_TOO_FAST.format(seconds=e.retry_after),
            show_alert=True,
        )
    except TelegramBadRequest:
        await callback.answer()


@plank_router.callback_query(F.data.startswith("plank_final_"))
async def process_plank_final(callback: types.CallbackQuery, state: FSMContext, plank_users_map: dict):
    """
    Finalizes the plank challenge, calculates the user's local date, and displays the result.
    """
    result = callback.data.split("_")[2]
    duration_sec = to_seconds(result)
    username = (
        callback.from_user.username.lower() if callback.from_user.username else ""
    )
    user_name = callback.from_user.first_name
    user_id = callback.from_user.id

    user_offset = get_user_offset(username, plank_users_map)  # Use the passed map
    now_utc = datetime.now(timezone.utc)
    user_time = convert_utc_to_local(now_utc, user_offset)
    date_today = user_time.strftime("%d.%m.%Y")

    # Записываем в базу и получаем ID
    last_id = await save_plank_result(user_id, username, duration_sec)

    note = random.choice(PLANK_MOTIVATION)
    final_text = PLANK_TEXT_PLANK_COMPLETED.format(
        user_name=user_name,
        result=result,
        date=date_today,
        note=note,
    )

    await state.clear()
    await callback.message.edit_text(
        final_text,
        reply_markup=get_plank_result_keyboard(last_id),
        parse_mode="Markdown",
    )
    await callback.answer("Result saved!")


@plank_router.callback_query(F.data == "ignore")
async def process_ignore(callback: types.CallbackQuery):
    """Empty handler for the central time button to prevent errors."""
    await callback.answer()


@plank_router.callback_query(F.data.startswith("back_to_plank:"))
async def process_back_to_plank(callback: types.CallbackQuery, state: FSMContext):
    """
    Deletes the saved record (if ID is present) and returns to the slider.
    """
    try:
        record_id = int(callback.data.split(":")[1])
        if record_id > 0:  # Only try to delete if it's a valid ID
            await delete_plank_result(record_id)
    except (IndexError, ValueError):
        logger.warning(
            "Could not parse record_id for back_to_plank: %s", callback.data
        )
        # Ignore deletion if ID is missing or invalid

    await state.set_state(PlankState.adjusting)
    await state.update_data(current_seconds=PLANK_INITIAL_SECONDS)

    await callback.message.edit_text(
        PLANK_TEXT_CHALLENGE_TITLE.format(
            user_name=callback.from_user.first_name
        ),
        reply_markup=get_plank_slider_keyboard(PLANK_INITIAL_SECONDS),
        parse_mode="Markdown",
    )
    await callback.answer()


@plank_router.message(Command("progress"))
async def show_summary(message: types.Message):
    user_id = message.from_user.id
    
    data = await get_user_stats(user_id)

    text = _build_stats_text(data)

    await message.answer(
        text, parse_mode="HTML", reply_markup=get_plank_stats_keyboard()
    )


@plank_router.callback_query(F.data == "show_stats_details")
async def process_stats_details(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    raw_data = await get_plank_details(user_id)
    
    if not raw_data:
        await callback.answer(PLANK_TEXT_NO_DATA, show_alert=True)
        return

    # 2. Group data by dates
    history_map = {}
    for date_str, duration in raw_data:
        # Convert '2023-10-08' to '08.10' (DD.MM format)
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        short_date = date_obj.strftime("%d.%m") 
        
        if short_date not in history_map:
            history_map[short_date] = []
        history_map[short_date].append(duration)

    # 3. Assemble details text
    details_text = PLANK_TEXT_DETAILS_HEADER

    for date, durations in history_map.items():
        # Convert [60, 45] to "1:00, 45s"
        times_str = ", ".join([format_time_compact(d) for d in durations])
        details_text += f"🔹 <b>{date}:</b> {times_str}\n"

    # 4. Add "Hide" button and edit old message
    await callback.message.edit_text(
        details_text,
        parse_mode="HTML",
        reply_markup=get_plank_stats_details_keyboard(),
    )


@plank_router.callback_query(F.data == "hide_stats_details")
async def process_hide_details(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = await get_user_stats(user_id)

    text = _build_stats_text(data)

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=get_plank_stats_keyboard()
    )


@plank_router.message(Command("graph"))
async def send_graph(message: types.Message):
    user_id = message.from_user.id
    
    raw_data = await get_plank_history(user_id)
    
    if not raw_data:
        await message.answer(PLANK_TEXT_GRAPH_NO_DATA)
        return

    # Prepare (datetime, seconds) points for the graph
    points = [
        (datetime.strptime(date_str, "%Y-%m-%d"), duration)
        for date_str, duration in raw_data
    ]

    photo_file = generate_progress_graph(points)
    
    if photo_file:
        # BufferedInputFile is needed to send bytes as a file
        photo = BufferedInputFile(photo_file.read(), filename="progress.png")
        await message.answer_photo(photo, caption=PLANK_TEXT_GRAPH_CAPTION)
    else:
        await message.answer(PLANK_TEXT_GRAPH_ERROR)
