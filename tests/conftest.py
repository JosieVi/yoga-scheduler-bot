import pytest
import aiosqlite
from datetime import date, timedelta
from db import database as db


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("test_data")
    return temp_dir / "TEST_yoga_community.db"


@pytest.fixture(scope="session", autouse=True)
async def initialize_test_db_schema(test_db_path):
    original_db_name = db.DB_NAME
    db.DB_NAME = str(test_db_path)

    if hasattr(db, "init_db"):
        await db.init_db()

    yield

    db.DB_NAME = original_db_name


@pytest.fixture(autouse=True)
async def isolated_db_session(monkeypatch, test_db_path):
    monkeypatch.setattr(db, "DB_NAME", str(test_db_path))

    yield

    async with aiosqlite.connect(str(test_db_path)) as conn:
        try:
            await conn.execute("DELETE FROM plank_history")

            await conn.execute("DELETE FROM sqlite_sequence WHERE name='plank_history'")

            await conn.commit()
        except Exception:
            pass


@pytest.fixture
def sample_user_map():
    return {"mark": 3, "ivan": -5, "grigoriy": 0}


@pytest.fixture
def sample_plank_data():
    today = date.today()
    return [((today - timedelta(days=i)).isoformat(), 60 + i * 5) for i in range(5)]
