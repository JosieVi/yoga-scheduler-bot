import aiosqlite
from datetime import datetime
from config import DB_NAME


async def init_db():
    """Create the database file and plank_history table if missing."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS plank_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                duration INTEGER,
                date TEXT
            )
        """
        )
        await db.commit()


async def save_plank_result(user_id, username, duration):
    """Save plank result and return the inserted record ID."""
    async with aiosqlite.connect(DB_NAME) as db:
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = await db.execute(
            "INSERT INTO plank_history (user_id, username, duration, date) VALUES (?, ?, ?, ?)",
            (user_id, username, duration, today),
        )
        last_id = cursor.lastrowid
        await db.commit()
        return last_id


async def delete_plank_result(record_id):
    """Delete a plank result by its ID."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM plank_history WHERE id = ?", (record_id,))
        await db.commit()


async def get_user_stats(user_id):
    """Return user statistics for the past 7 and 30 days."""
    stats = {}
    async with aiosqlite.connect(DB_NAME) as db:
        for days in [7, 30]:
            query = f"""
                SELECT
                    SUM(duration),
                    COUNT(id),
                    MAX(duration)
                FROM plank_history
                WHERE user_id = ? AND date >= date('now', '-{days} days')
            """
            async with db.execute(query, (user_id,)) as cursor:
                row = await cursor.fetchone()

                total = row[0] if row[0] else 0
                count = row[1] if row[1] else 0
                maximum = row[2] if row[2] else 0

                average = (total // count) if count > 0 else 0

                stats[days] = {
                    "total": total,
                    "count": count,
                    "max": maximum,
                    "avg": average,
                }

    return stats


async def get_plank_history(user_id):
    """Return last 30 plank entries as (date, seconds) tuples."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """
            SELECT date, duration
            FROM plank_history
            WHERE user_id = ?
            ORDER BY date ASC
            LIMIT 30
        """,
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return rows


async def get_plank_details(user_id):
    """Return all attempts for the last 30 days, newest first."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """
            SELECT date, duration
            FROM plank_history
            WHERE user_id = ? AND date >= date('now', '-30 days')
            ORDER BY date DESC, id DESC
        """,
            (user_id,),
        ) as cursor:
            return await cursor.fetchall()
