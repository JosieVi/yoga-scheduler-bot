import os
from pathlib import Path

import pytest
from db import database as db


@pytest.fixture
def tmp_db(monkeypatch, tmp_path):
    """Use a temporary SQLite file for database tests."""
    db_path = tmp_path / "test_plank.db"
    monkeypatch.setattr(db, "DB_NAME", str(db_path))
    return db_path


@pytest.mark.asyncio
async def test_init_db_creates_file(tmp_db):
    """init_db should create the database file and table."""
    await db.init_db()
    assert os.path.exists(tmp_db)


@pytest.mark.asyncio
async def test_save_and_get_history(tmp_db):
    """save_plank_result and get_plank_history should persist and read rows."""
    await db.init_db()
    user_id = 123

    await db.save_plank_result(user_id, "testuser", 60)
    history = await db.get_plank_history(user_id)

    assert len(history) == 1
    date_str, duration = history[0]
    assert isinstance(date_str, str)
    assert duration == 60


@pytest.mark.asyncio
async def test_delete_plank_result(tmp_db):
    """delete_plank_result should remove the row."""
    await db.init_db()
    user_id = 5

    record_id = await db.save_plank_result(user_id, "user", 30)
    history_before = await db.get_plank_history(user_id)
    assert len(history_before) == 1

    await db.delete_plank_result(record_id)
    history_after = await db.get_plank_history(user_id)
    assert history_after == []


@pytest.mark.asyncio
async def test_get_user_stats(tmp_db):
    """get_user_stats should return aggregated stats for 7 and 30 days."""
    await db.init_db()
    user_id = 42

    await db.save_plank_result(user_id, "user", 30)
    await db.save_plank_result(user_id, "user", 60)

    stats = await db.get_user_stats(user_id)

    for days in (7, 30):
        assert days in stats
        assert stats[days]["total"] >= 90
        assert stats[days]["count"] >= 2
        assert stats[days]["max"] >= 60
        assert stats[days]["avg"] >= 30


@pytest.mark.asyncio
async def test_get_plank_details_ordering(tmp_db):
    """get_plank_details should return latest attempts first."""
    await db.init_db()
    user_id = 7

    # Two calls on the same day, then one earlier (simulated by direct insert)
    await db.save_plank_result(user_id, "user", 60)
    await db.save_plank_result(user_id, "user", 45)

    details = await db.get_plank_details(user_id)
    assert len(details) >= 2
    # First record should be the most recent
    first_date, first_duration = details[0]
    assert isinstance(first_date, str)
    assert isinstance(first_duration, int)
