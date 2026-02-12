from datetime import datetime, timedelta
import io
import math

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from utils import format_time
from config import (
    PLANK_INITIAL_SECONDS,
    PLANK_BTN_CONFIRM,
    PLANK_BTN_DELETE,
    PLANK_BTN_BACK,
    PLANK_BTN_DETAILS,
    PLANK_BTN_HIDE,
)


def get_plank_slider_keyboard(
    seconds: int, record_id: int | None = None
) -> types.InlineKeyboardMarkup:
    """
    Inline keyboard for adjusting plank time.

    Args:
        seconds: current plank duration in seconds.
        record_id: optional record id for delete callback.
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
    delete_callback_data = (
        f"cancel_plank:{record_id}" if record_id else "cancel_plank:0"
    )

    builder.row(
        types.InlineKeyboardButton(
            text=PLANK_BTN_CONFIRM, callback_data=f"plank_final_{time_str}"
        ),
        types.InlineKeyboardButton(
            text=PLANK_BTN_DELETE, callback_data=delete_callback_data
        ),
    )
    return builder.as_markup()


def get_plank_result_keyboard(record_id: int) -> types.InlineKeyboardMarkup:
    """Keyboard shown after saving plank result."""
    builder = InlineKeyboardBuilder()
    builder.button(text=PLANK_BTN_DELETE, callback_data=f"cancel_plank:{record_id}")
    builder.button(text=PLANK_BTN_BACK, callback_data=f"back_to_plank:{record_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_plank_stats_keyboard() -> types.InlineKeyboardMarkup:
    """Keyboard for main statistics message."""
    builder = InlineKeyboardBuilder()
    builder.button(text=PLANK_BTN_DETAILS, callback_data="show_stats_details")
    return builder.as_markup()


def get_plank_stats_details_keyboard() -> types.InlineKeyboardMarkup:
    """Keyboard for detailed statistics view."""
    builder = InlineKeyboardBuilder()
    builder.button(text=PLANK_BTN_HIDE, callback_data="hide_stats_details")
    return builder.as_markup()


def generate_plank_graph(seconds: int, days: int = 7) -> io.BytesIO:
    """
    Generates a plank graph with constant value `seconds` across `days`.

    Returns:
        BytesIO buffer with PNG image.
    """
    dates = [datetime.now() + timedelta(days=i) for i in range(days)]
    plank_times = [seconds] * days

    plt.figure(figsize=(10, 5))
    plt.plot(dates, plank_times, marker="o")

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.tight_layout()

    output = io.BytesIO()
    plt.savefig(output, format="png")
    output.seek(0)
    return output


def generate_progress_graph(points: list[tuple[datetime, int]]) -> io.BytesIO | None:
    """
    Generates a progress graph from prepared (datetime, seconds) points.
    Y-axis: fixed intervals every 10 seconds, from (min - 10) to (max + 10).
    """
    if not points:
        return None

    # Enable headless backend for server usage
    plt.switch_backend("Agg")

    timestamps, durations = zip(*points)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        timestamps,
        durations,
        marker="o",
        linestyle="-",
        color="#1f77b4",
        linewidth=2,
        markersize=6,
    )

    ax.set_title("Plank Progress", fontsize=16, fontweight="bold", pad=20)
    ax.set_ylabel("Time (seconds)", fontsize=12)

    ax.grid(True, which="major", axis="both", linestyle="--", alpha=0.6)

    if len(points) <= 14:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    else:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))

    fig.autofmt_xdate(rotation=45, ha="right")

    if durations:
        min_val = min(durations)
        max_val = max(durations)
        lower_bound = max(0, math.floor((min_val - 10) / 10) * 10)
        upper_bound = math.ceil((max_val + 10) / 10) * 10

        ax.set_ylim(bottom=lower_bound, top=upper_bound)
        ticks = range(int(lower_bound), int(upper_bound) + 1, 10)
        ax.set_yticks(ticks)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)

    return buf

