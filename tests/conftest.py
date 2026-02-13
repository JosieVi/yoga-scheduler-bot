import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from the bot
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture
def sample_user_map():
    """Fixture providing sample user timezone map."""
    return {
        "john": 3.5,
        "alice": -5.0,
        "bob": 0.0,
    }


@pytest.fixture
def sample_plank_data():
    """Fixture providing sample plank history data."""
    return [
        ("2025-10-01", 60),
        ("2025-10-02", 75),
        ("2025-10-03", 65),
        ("2025-10-04", 80),
        ("2025-10-05", 90),
    ]


@pytest.fixture
def sample_raw_plank_data():
    """Fixture providing raw plank data (multiple entries per date)."""
    return [
        ("2025-10-05", 60),
        ("2025-10-05", 45),
        ("2025-10-04", 75),
        ("2025-10-03", 60),
        ("2025-10-03", 55),
    ]
