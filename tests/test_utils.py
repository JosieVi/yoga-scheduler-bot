import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from utils import (
    get_user_offset,
    convert_utc_to_local,
    format_time,
    format_time_compact,
    to_seconds,
    escape_markdown,
    validate_user,
)


@pytest.mark.parametrize(
    "offset, expected_hour",
    [
        (3.0, 15),  # UTC+3
        (-5.0, 7),  # UTC-5
        (0.0, 12),  # UTC+0 (No change)
    ],
)
def test_convert_utc_to_local(offset, expected_hour):
    dt_utc = datetime(2025, 10, 15, 12, 0, 0, tzinfo=timezone.utc)

    result = convert_utc_to_local(dt_utc, offset)

    assert result.hour == expected_hour
    assert result.minute == 0

    assert result.day == 15


# --- Formatting Utils ---


@pytest.mark.parametrize(
    "seconds, expected_full, expected_compact",
    [
        (90, "1:30 min", "1:30"),
        (120, "2:00 min", "2:00"),
        (65, "1:05 min", "1:05"),
        (45, "45 sec", "45s"),
        (30, "30 sec", "30s"),
        (0, "0 sec", "0s"),
    ],
)
def test_time_formatting(seconds, expected_full, expected_compact):
    assert format_time(seconds) == expected_full
    assert format_time_compact(seconds) == expected_compact


@pytest.mark.parametrize(
    "input_str, expected_seconds",
    [
        ("1:30", 90),
        ("2:00", 120),
        ("45", 45),
        ("30 sec", 30),
        ("10:15", 615),
        ("0", 0),
    ],
)
def test_to_seconds_parsing(input_str, expected_seconds):
    assert to_seconds(input_str) == expected_seconds


def test_get_user_offset_logic():
    users_db = {"john": 3.5, "alice": -5.0}

    assert get_user_offset("john", users_db) == 3.5
    assert get_user_offset("JOHN", users_db) == 3.5
    assert get_user_offset("unknown", users_db) == 0.0
    assert get_user_offset(None, users_db) == 0.0


@pytest.mark.parametrize(
    "text, expected",
    [
        ("user_name", r"user\_name"),
        ("bold*text", r"bold\*text"),
        ("func(args)", r"func\(args\)"),
        ("normal text", "normal text"),
    ],
)
def test_markdown_escaping(text, expected):
    """Verify strictly required characters are escaped."""
    assert escape_markdown(text) == expected


def test_validate_user_structure():
    """Use Mock objects to simulate Telegram Message structure."""
    msg_valid = Mock()
    msg_valid.from_user.username = "valid_user"
    assert validate_user(msg_valid) is True

    msg_no_username = Mock()
    msg_no_username.from_user.username = None
    assert validate_user(msg_no_username) is False

    msg_channel = Mock()
    msg_channel.from_user = None
