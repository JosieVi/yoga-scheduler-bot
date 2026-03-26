import asyncio
import logging
import os
import json
from dotenv import load_dotenv
from db.database import init_db
from config import BOT_COMMANDS, LOG_LEVEL, LOG_FORMAT

from aiogram import F, types, Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from middlewares import AccessMiddleware
from handlers.yoga import yoga_router
from handlers.plank import plank_router

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN not found!")

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


def load_users(filename: str) -> dict:
    """Load timezone offsets from JSON file or return empty dict on error."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        logger.warning("Failed to load %s: %s", filename, e)
    return {}


YOGA_USERS = load_users("users_yoga.json")
PLANK_USERS = load_users("users_plank.json")


logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


dp.update.outer_middleware(
    AccessMiddleware(yoga_users=YOGA_USERS, plank_users=PLANK_USERS)
)


dp["yoga_users_map"] = YOGA_USERS
dp["plank_users_map"] = PLANK_USERS


dp.include_router(yoga_router)
dp.include_router(plank_router)


@dp.message(F.photo)
@plank_router.message(F.photo)
async def catch_photo_id(message: types.Message):
    photo_id = message.photo[-1].file_id
    await message.reply(f"`{photo_id}`", parse_mode="Markdown")


async def main():
    """Start the bot and run the polling loop."""
    await init_db()

    commands = [BotCommand(command=cmd, description=desc) for cmd, desc in BOT_COMMANDS]
    await bot.set_my_commands(commands)

    logger.info("🚀 Bot started and Database initialized!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
