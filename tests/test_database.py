import pytest
from db import database as db

TEST_USER_ID = 666


@pytest.mark.asyncio
async def test_plank_lifecycle():
    record_id = await db.save_plank_result(TEST_USER_ID, "tester", 60)
    assert record_id is not None

    history = await db.get_plank_history(TEST_USER_ID)
    assert len(history) == 1
    assert history[0][1] == 60

    await db.delete_plank_result(record_id)
    history_after = await db.get_plank_history(TEST_USER_ID)
    assert len(history_after) == 0


@pytest.mark.asyncio
async def test_user_stats_calculation():
    await db.save_plank_result(TEST_USER_ID, "math_user", 30)
    await db.save_plank_result(TEST_USER_ID, "math_user", 60)

    stats = await db.get_user_stats(TEST_USER_ID)

    stat_7 = stats.get(7)
    assert stat_7 is not None

    assert stat_7["total"] == 90
    assert stat_7["count"] == 2
    assert stat_7["max"] == 60
    assert stat_7["avg"] == 45.0
