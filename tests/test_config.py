import re
import pytest
from config import (
    DB_NAME,
    MIN_PARTICIPANTS,
    DEFAULT_SLOTS_UTC,
    PLANK_MIN_SECONDS,
    PLANK_INITIAL_SECONDS,
    BOT_COMMANDS,
    PLANK_MOTIVATION_OPTIONS,
)


def test_database_config():
    assert DB_NAME.endswith(".db"), "Database name must be an SQLite file"


def test_yoga_logic():
    assert MIN_PARTICIPANTS >= 1

    assert DEFAULT_SLOTS_UTC == sorted(DEFAULT_SLOTS_UTC)
    assert len(DEFAULT_SLOTS_UTC) > 0


def test_plank_logic():
    assert PLANK_MIN_SECONDS > 0
    assert PLANK_INITIAL_SECONDS >= PLANK_MIN_SECONDS


@pytest.mark.parametrize("slot", DEFAULT_SLOTS_UTC)
def test_time_slots_format(slot):
    assert re.match(
        r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", slot
    ), f"Invalid time format: {slot}"


def test_bot_commands_structure():
    commands_dict = dict(BOT_COMMANDS)
    assert len(commands_dict) > 0

    for cmd, desc in BOT_COMMANDS:
        assert cmd.islower(), f"Command /{cmd} must be lowercase"
        assert " " not in cmd, f"Command /{cmd} must not contain spaces"
        assert desc.strip(), f"Command /{cmd} must have a description"


def test_motivation_messages():
    assert len(PLANK_MOTIVATION_OPTIONS) > 0, "Motivation options list is empty"

    for option in PLANK_MOTIVATION_OPTIONS:
        # Проверяем, что элемент является словарем
        assert isinstance(option, dict), "Motivation option must be a dictionary"

        # Проверяем наличие нужных ключей
        assert "image" in option, "Motivation option missing 'image' key"
        assert "caption" in option, "Motivation option missing 'caption' key"

        # Проверяем, что значения не пустые строки
        assert (
            isinstance(option["image"], str) and option["image"].strip()
        ), "Image value must be a non-empty string"
        assert (
            isinstance(option["caption"], str) and option["caption"].strip()
        ), "Caption value must be a non-empty string"
