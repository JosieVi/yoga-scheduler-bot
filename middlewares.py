from aiogram import types
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware
import logging

logger = logging.getLogger(__name__)

class AccessMiddleware(BaseMiddleware):
    def __init__(self, yoga_users: dict, plank_users: dict):
        super().__init__()
        self.yoga_users = yoga_users
        self.plank_users = plank_users

    async def __call__(self, handler, event: TelegramObject, data):
        # Only check messages and callbacks
        user = data.get("event_from_user")
        if not user or not user.username:
            # Ignore users without username
            logger.warning("User without username attempted to interact: %s", user)
            if hasattr(event, "answer"): # If it's a message or callback, try to answer
                 if isinstance(event, types.Message):
                    await event.answer("🚫 Access denied. Please set a username in Telegram.")
                 elif isinstance(event, types.CallbackQuery):
                    await event.answer("🚫 Access denied. Please set a username in Telegram.", show_alert=True)
            return

        username = user.username.lower()

        # If user is not in any access lists - block
        if username not in self.yoga_users and username not in self.plank_users:
            if hasattr(event, "answer"): # If it's a message or callback
                if isinstance(event, types.Message):
                    await event.answer("🚫 Access denied. You are not on the guest list.")
                elif isinstance(event, types.CallbackQuery):
                    await event.answer("🚫 Access denied. You are not on the guest list.", show_alert=True)
            return

        # If user is in lists, let them proceed to commands
        return await handler(event, data)
