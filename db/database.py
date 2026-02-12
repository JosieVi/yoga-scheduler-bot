import aiosqlite
from datetime import datetime
from config import DB_NAME

async def init_db():
    """Creates the database file and table if they don't exist yet"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS plank_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                duration INTEGER,
                date TEXT
            )
        ''')
        await db.commit()

async def save_plank_result(user_id, username, duration):
    """Saves the result and returns the record ID"""
    async with aiosqlite.connect(DB_NAME) as db:
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = await db.execute(
            "INSERT INTO plank_history (user_id, username, duration, date) VALUES (?, ?, ?, ?)",
            (user_id, username, duration, today)
        )
        last_id = cursor.lastrowid  # Get the ID of the newly created row
        await db.commit()
        return last_id


async def delete_plank_result(record_id):
    """Deletes a record by its ID"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM plank_history WHERE id = ?", (record_id,))
        await db.commit()


async def get_user_stats(user_id):
    stats = {}
    async with aiosqlite.connect(DB_NAME) as db:

        for days in [7, 30]:
            # SQL magic: fetch everything in one go
            query = f'''
                SELECT 
                    SUM(duration), 
                    COUNT(id), 
                    MAX(duration) 
                FROM plank_history 
                WHERE user_id = ? AND date >= date('now', '-{days} days')
            '''
            async with db.execute(query, (user_id,)) as cursor:
                row = await cursor.fetchone()
                
                total = row[0] if row[0] else 0
                count = row[1] if row[1] else 0
                maximum = row[2] if row[2] else 0
                
                # Calculate average manually to avoid floats like 33.333333 sec
                average = (total // count) if count > 0 else 0
                
                stats[days] = {
                    "total": total,
                    "count": count,
                    "max": maximum,
                    "avg": average
                }
                
    return stats
    

async def get_plank_history(user_id):
    """Returns a list of tuples (date, seconds) for 30 days"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Get date and duration, sorted from old to new
        async with db.execute('''
            SELECT date, duration 
            FROM plank_history 
            WHERE user_id = ? 
            ORDER BY date ASC 
            LIMIT 30
        ''', (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return rows # Returns a list like [('2023-10-01', 60), ('2023-10-02', 75)]


async def get_plank_details(user_id):
    """
    Returns a list of all attempts over the last 30 days.
    Sort: Most recent first.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''
            SELECT date, duration 
            FROM plank_history 
            WHERE user_id = ? AND date >= date('now', '-30 days')
            ORDER BY date DESC, id DESC
        ''', (user_id,)) as cursor:
            # Returns list of tuples: [('2023-10-05', 60), ('2023-10-05', 45), ...]
            return await cursor.fetchall()