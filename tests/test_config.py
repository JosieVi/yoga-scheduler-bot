import pytest
from config import (
    DB_NAME,
    MIN_PARTICIPANTS,
    DEFAULT_SLOTS_UTC,
    PLANK_MIN_SECONDS,
    PLANK_INITIAL_SECONDS,
    BOT_COMMANDS,
    YOGA_JOKES,
    PLANK_MOTIVATION,
)


class TestConfigConstants:
    """Tests for configuration constants."""
    
    def test_db_name_is_string(self):
        """Test that DB_NAME is a string."""
        assert isinstance(DB_NAME, str)
        assert len(DB_NAME) > 0
    
    def test_min_participants_is_positive(self):
        """Test that MIN_PARTICIPANTS is a positive integer."""
        assert isinstance(MIN_PARTICIPANTS, int)
        assert MIN_PARTICIPANTS > 0
    
    def test_default_slots_utc_is_list(self):
        """Test that DEFAULT_SLOTS_UTC is a list of time strings."""
        assert isinstance(DEFAULT_SLOTS_UTC, list)
        assert len(DEFAULT_SLOTS_UTC) > 0
        for slot in DEFAULT_SLOTS_UTC:
            assert isinstance(slot, str)
            assert ":" in slot  # Basic time format check
    
    def test_plank_constants_are_positive(self):
        """Test that plank constants are positive integers."""
        assert isinstance(PLANK_MIN_SECONDS, int)
        assert isinstance(PLANK_INITIAL_SECONDS, int)
        assert PLANK_MIN_SECONDS > 0
        assert PLANK_INITIAL_SECONDS > PLANK_MIN_SECONDS
    
    def test_bot_commands_is_list_of_tuples(self):
        """Test that BOT_COMMANDS contains valid command tuples."""
        assert isinstance(BOT_COMMANDS, list)
        assert len(BOT_COMMANDS) > 0
        for cmd, desc in BOT_COMMANDS:
            assert isinstance(cmd, str)
            assert isinstance(desc, str)
            assert len(cmd) > 0
            assert len(desc) > 0
    
    def test_joke_lists_not_empty(self):
        """Test that joke and motivation lists are not empty."""
        assert len(YOGA_JOKES) > 0
        assert len(PLANK_MOTIVATION) > 0
        
        for joke in YOGA_JOKES:
            assert isinstance(joke, str)
        
        for motivation in PLANK_MOTIVATION:
            assert isinstance(motivation, str)
