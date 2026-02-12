import pytest
from datetime import datetime
from utils import (
    get_user_offset,
    convert_utc_to_local,
    format_time,
    format_time_compact,
    to_seconds,
    escape_markdown,
    validate_user,
)


class TestGetUserOffset:
    """Tests for get_user_offset function."""
    
    def test_get_user_offset_with_valid_username(self):
        """Test getting offset for existing username."""
        user_dict = {"john": 3.5, "alice": -5.0}
        assert get_user_offset("john", user_dict) == 3.5
        assert get_user_offset("JOHN", user_dict) == 3.5  # Case insensitive
    
    def test_get_user_offset_with_nonexistent_username(self):
        """Test getting offset for non-existent username returns 0."""
        user_dict = {"john": 3.5}
        assert get_user_offset("bob", user_dict) == 0.0
    
    def test_get_user_offset_with_empty_username(self):
        """Test with None or empty username returns 0."""
        user_dict = {"john": 3.5}
        assert get_user_offset(None, user_dict) == 0.0
        assert get_user_offset("", user_dict) == 0.0
    
    def test_get_user_offset_with_invalid_offset_value(self):
        """Test with invalid offset value returns 0."""
        user_dict = {"john": "invalid"}
        assert get_user_offset("john", user_dict) == 0.0


class TestConvertUtcToLocal:
    """Tests for convert_utc_to_local function."""
    
    def test_convert_positive_offset(self):
        """Test converting UTC to local time with positive offset."""
        dt_utc = datetime(2023, 10, 15, 12, 0, 0)
        result = convert_utc_to_local(dt_utc, 3.0)
        assert result.hour == 15
        assert result.minute == 0
    
    def test_convert_negative_offset(self):
        """Test converting UTC to local time with negative offset."""
        dt_utc = datetime(2023, 10, 15, 12, 0, 0)
        result = convert_utc_to_local(dt_utc, -5.0)
        assert result.hour == 7
    
    def test_convert_zero_offset(self):
        """Test converting with zero offset returns same time."""
        dt_utc = datetime(2023, 10, 15, 12, 0, 0)
        result = convert_utc_to_local(dt_utc, 0.0)
        assert result == dt_utc


class TestFormatTime:
    """Tests for format_time function."""
    
    def test_format_time_minutes_and_seconds(self):
        """Test formatting time with minutes and seconds."""
        assert format_time(90) == "1:30 min"
        assert format_time(120) == "2:00 min"
        assert format_time(65) == "1:05 min"
    
    def test_format_time_only_seconds(self):
        """Test formatting time with only seconds."""
        assert format_time(45) == "45 sec"
        assert format_time(30) == "30 sec"
        assert format_time(59) == "59 sec"
    
    def test_format_time_zero(self):
        """Test formatting zero seconds."""
        assert format_time(0) == "0 sec"


class TestFormatTimeCompact:
    """Tests for format_time_compact function."""

    def test_format_time_compact_minutes_and_seconds(self):
        """Test compact formatting with minutes."""
        assert format_time_compact(90) == "1:30"
        assert format_time_compact(120) == "2:00"

    def test_format_time_compact_only_seconds(self):
        """Test compact formatting with only seconds."""
        assert format_time_compact(45) == "45s"
        assert format_time_compact(0) == "0s"


class TestToSeconds:
    """Tests for to_seconds function."""
    
    def test_to_seconds_with_minutes_and_seconds(self):
        """Test converting time string with minutes and seconds."""
        assert to_seconds("1:30") == 90
        assert to_seconds("2:00") == 120
        assert to_seconds("1:05") == 65
    
    def test_to_seconds_with_only_seconds(self):
        """Test converting time string with only seconds."""
        assert to_seconds("45") == 45
        assert to_seconds("30 sec") == 30
        assert to_seconds("59") == 59
    
    def test_to_seconds_with_sec_suffix(self):
        """Test converting time string with 'sec' suffix."""
        assert to_seconds("45 sec") == 45
        assert to_seconds("30 sec") == 30
    
    def test_to_seconds_edge_cases(self):
        """Test edge cases."""
        assert to_seconds("0") == 0
        assert to_seconds("10:15") == 615


class TestEscapeMarkdown:
    """Tests for escape_markdown function."""

    def test_escape_underscore_and_asterisk(self):
        """Usernames with markdown special chars should be escaped."""
        assert escape_markdown("user_name") == "user\\_name"
        assert escape_markdown("user*name") == "user\\*name"
        assert escape_markdown("user*_name") == "user\\*\\_name"

    def test_escape_markdown_other_chars_unchanged(self):
        """Other characters should stay the same."""
        assert escape_markdown("user.name") == "user.name"


class DummyFromUser:
    def __init__(self, username):
        self.username = username


class DummyMessage:
    def __init__(self, username):
        self.from_user = DummyFromUser(username)


class TestValidateUser:
    """Tests for validate_user helper."""

    def test_validate_user_with_username(self):
        msg = DummyMessage("john")
        assert validate_user(msg) is True

    def test_validate_user_without_username(self):
        msg = DummyMessage(None)
        assert validate_user(msg) is False
