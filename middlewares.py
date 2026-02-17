import logging

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)


class AccessMiddleware(BaseMiddleware):
    def __init__(self, yoga_users: dict, plank_users: dict):
        super().__init__()
        self.yoga_users = yoga_users
        self.plank_users = plank_users

    async def __call__(self, handler, event: TelegramObject, data):
        user = data.get("event_from_user")
        if not user or not user.username:
            logger.warning("User without username attempted to interact: %s", user)
            if isinstance(event, types.Message):
                await event.answer(
                    "🚫 Access denied. Please set a username in Telegram."
                )
            elif isinstance(event, types.CallbackQuery):
                await event.answer(
                    "🚫 Access denied. Please set a username in Telegram.",
                    show_alert=True,
                )
            return

        username = user.username.lower()

        if username not in self.yoga_users and username not in self.plank_users:
            if isinstance(event, types.Message):
                await event.answer("🚫 Access denied. You are not on the guest list.")
            elif isinstance(event, types.CallbackQuery):
                await event.answer(
                    "🚫 Access denied. You are not on the guest list.", show_alert=True
                )
            return

        return await handler(event, data)
