import logging
import random
from datetime import datetime, timezone

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (
    PLANK_INITIAL_SECONDS,
    PLANK_MIN_SECONDS,
    PLANK_MOTIVATION_OPTIONS,
    PLANK_TEXT_CHALLENGE_TITLE,
    PLANK_TEXT_DELETE_ERROR,
    PLANK_TEXT_DELETE_NONE,
    PLANK_TEXT_DETAILS_HEADER,
    PLANK_TEXT_GRAPH_CAPTION,
    PLANK_TEXT_GRAPH_ERROR,
    PLANK_TEXT_GRAPH_NO_DATA,
    PLANK_TEXT_NO_DATA,
    PLANK_TEXT_PLANK_COMPLETED,
    PLANK_TEXT_TOO_FAST,
    PLANK_TEXT_USERNAME_REQUIRED,
)
from db.database import (
    delete_plank_result,
    get_plank_details,
    get_plank_history,
    get_user_stats,
    save_plank_result,
)
from states import PlankState
from utils import (
    convert_utc_to_local,
    format_time_compact,
    get_user_offset,
    to_seconds,
    validate_user,
)
from views.plank import (
    _build_stats_text,
    generate_progress_graph,
    get_plank_progress_text,
    get_plank_result_keyboard,
    get_plank_slider_keyboard,
    get_plank_stats_details_keyboard,
    get_plank_stats_keyboard,
    get_sets_keyboard,
)

logger = logging.getLogger(__name__)

plank_router = Router()


@plank_router.message(Command("plank"))
async def cmd_plank(message: Message, state: FSMContext):
    """Start plank challenge and ask for number of sets."""
    if not validate_user(message):
        await message.answer(PLANK_TEXT_USERNAME_REQUIRED)
        return

    await state.set_state(PlankState.choosing_sets)

    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=str(i), callback_data=f"sets_{i}")
    builder.adjust(5)

    await message.answer(
        "How many sets did you do? (1-5)",
        parse_mode="Markdown",
        reply_markup=get_sets_keyboard(),
    )


@plank_router.callback_query(PlankState.choosing_sets, F.data.startswith("sets_"))
async def process_sets_selection(callback: types.CallbackQuery, state: FSMContext):
    total_sets = int(callback.data.split("_")[1])
    current_set = 1

    await state.update_data(
        total_sets=total_sets,
        current_set=1,
        current_seconds=PLANK_INITIAL_SECONDS,
        results=[],
    )
    await state.set_state(PlankState.adjusting)

    msg_text = get_plank_progress_text(
        user_name=callback.from_user.first_name,
        current_set=current_set,
        total_sets=total_sets,
    )

    await callback.message.edit_text(
        msg_text,
        reply_markup=get_plank_slider_keyboard(PLANK_INITIAL_SECONDS),
        parse_mode="Markdown",
    )
    await callback.answer()


@plank_router.callback_query(F.data.startswith("cancel_plank:"))
async def process_cancel_plank(callback: types.CallbackQuery):
    try:
        records_str = callback.data.split(":")[1]

        record_ids = [int(r_id) for r_id in records_str.split(",") if r_id]

        if record_ids:
            for rec_id in record_ids:
                await delete_plank_result(rec_id)

            await callback.answer(
                "All results in the series have been successfully deleted!"
            )
        else:
            await callback.answer(PLANK_TEXT_DELETE_NONE, show_alert=True)

        await callback.message.delete()
    except (TelegramBadRequest, TelegramRetryAfter, ValueError, IndexError) as exc:
        logger.debug(
            "Failed to cancel plank entry for payloasd %s: %s", callback.data, exc
        )
        await callback.answer(PLANK_TEXT_DELETE_ERROR)


@plank_router.callback_query(F.data.startswith("plank_adj_"))
async def process_plank_adjustment(callback: types.CallbackQuery, state: FSMContext):
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


@plank_router.callback_query(PlankState.adjusting, F.data.startswith("plank_final_"))
async def process_plank_final(
    callback: types.CallbackQuery, state: FSMContext, plank_users_map: dict
):
    """Finalize current set and check if more sets are needed."""
    result = callback.data.split("_")[2]
    duration_sec = to_seconds(result)

    data = await state.get_data()
    total_sets = data.get("total_sets", 1)
    current_set = data.get("current_set", 1)
    results = data.get("results", [])

    results.append(duration_sec)

    if current_set < total_sets:
        current_set += 1
        await state.update_data(
            current_set=current_set,
            current_seconds=PLANK_INITIAL_SECONDS,
            results=results,
        )

        msg_text = get_plank_progress_text(
            user_name=callback.from_user.first_name,
            current_set=current_set,
            total_sets=total_sets,
        )

        await callback.message.edit_text(
            msg_text,
            reply_markup=get_plank_slider_keyboard(PLANK_INITIAL_SECONDS),
            parse_mode="Markdown",
        )
        await callback.answer(f"Set {current_set - 1} saved in memory!")
        return

    username = (
        callback.from_user.username.lower() if callback.from_user.username else ""
    )
    user_name = callback.from_user.first_name
    user_id = callback.from_user.id

    user_offset = get_user_offset(username, plank_users_map)
    now_utc = datetime.now(timezone.utc)
    user_time = convert_utc_to_local(now_utc, user_offset)
    date_today = user_time.strftime("%d.%m.%Y")

    saved_ids = []
    total_duration = 0
    for res_sec in results:
        record_id = await save_plank_result(user_id, username, res_sec)
        saved_ids.append(str(record_id))
        total_duration += res_sec

    joined_ids = ",".join(saved_ids)
    total_mins = total_duration // 60
    total_secs = total_duration % 60
    formatted_total = f"{total_mins:02d}:{total_secs:02d}"

    motivation_dict = random.choice(PLANK_MOTIVATION_OPTIONS)
    final_text = PLANK_TEXT_PLANK_COMPLETED.format(
        user_name=user_name,
        result=formatted_total,
        date=date_today,
        note=motivation_dict["caption"],
    )

    if total_sets > 1:
        sets_details = ", ".join([f"{r//60:02d}:{r%60:02d}" for r in results])
        final_text += f"\n\n📊 Details per set: {sets_details}"

    await state.clear()
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=motivation_dict["image"],
        caption=final_text,
        reply_markup=get_plank_result_keyboard(joined_ids),  # Передаем строку с ID
        parse_mode="Markdown",
    )
    await callback.answer("All sets saved! Great job!")


@plank_router.callback_query(F.data == "ignore")
async def process_ignore(callback: types.CallbackQuery):
    await callback.answer()


@plank_router.callback_query(F.data.startswith("back_to_plank:"))
async def process_back_to_plank(callback: types.CallbackQuery, state: FSMContext):
    """Return user to plank slider and optionally delete saved record."""
    try:
        record_id = int(callback.data.split(":")[1])
        if record_id > 0:
            await delete_plank_result(record_id)
    except (IndexError, ValueError):
        logger.warning("Could not parse record_id for back_to_plank: %s", callback.data)

    await state.set_state(PlankState.adjusting)
    await state.update_data(current_seconds=PLANK_INITIAL_SECONDS)

    await callback.message.edit_text(
        PLANK_TEXT_CHALLENGE_TITLE.format(user_name=callback.from_user.first_name),
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
    history_map: dict[str, list[int]] = {}
    for date_str, duration in raw_data:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        short_date = date_obj.strftime("%d.%m")
        history_map.setdefault(short_date, []).append(duration)

    details_lines = [
        f"🔹 <b>{date}:</b> {', '.join(format_time_compact(d) for d in durations)}"
        for date, durations in history_map.items()
    ]
    details_text = PLANK_TEXT_DETAILS_HEADER + "\n".join(details_lines) + "\n"

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

    points = [
        (datetime.strptime(date_str, "%Y-%m-%d"), duration)
        for date_str, duration in raw_data
    ]

    photo_file = generate_progress_graph(points)

    if photo_file:
        photo = BufferedInputFile(photo_file.read(), filename="progress.png")
        await message.answer_photo(photo, caption=PLANK_TEXT_GRAPH_CAPTION)
    else:
        await message.answer(PLANK_TEXT_GRAPH_ERROR)
