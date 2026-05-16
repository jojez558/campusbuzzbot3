"""
CampusBuzz Kenya - Force Join Middleware
Blocks usage until user joins the required Telegram channel.
"""

from typing import Callable, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.exceptions import TelegramBadRequest
from config import settings
from keyboards.welcome import force_join_keyboard
import logging

logger = logging.getLogger(__name__)

# Commands that skip force-join check
EXEMPT_COMMANDS = {"/start", "/help"}

# Admin bypass
ADMIN_IDS = {settings.ADMIN_ID}


async def check_membership(bot: Bot, user_id: int) -> bool:
    """Returns True if user is a member of the required channel."""
    try:
        member = await bot.get_chat_member(settings.REQUIRED_CHANNEL, user_id)
        status = member.status
        logger.info(f"✅ Membership check for {user_id}: status={status}")
        return status not in ("left", "kicked", "banned")
    except TelegramBadRequest as e:
        logger.error(f"❌ Membership check failed for {user_id}: {e}")
        logger.error(f"   Channel ID: {settings.REQUIRED_CHANNEL}")
        logger.error(f"   Error details: {e.message if hasattr(e, 'message') else str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error checking membership for {user_id}: {type(e).__name__}: {e}")
        return False  # Fail safe: block


class ForceJoinMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        # Determine user id
        if isinstance(event, Message):
            user = event.from_user
            text = event.text or ""
            # Exempt specific commands
            if any(text.startswith(cmd) for cmd in EXEMPT_COMMANDS):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            # Allow the "check membership" callback to proceed
            if event.data and event.data.startswith("check_join"):
                pass  # fall through to check
        else:
            return await handler(event, data)

        if not user:
            return await handler(event, data)

        # Admins always bypass
        if user.id in ADMIN_IDS:
            return await handler(event, data)

        bot: Bot = data["bot"]
        is_member = await check_membership(bot, user.id)

        if not is_member:
            msg = (
                "🚫 <b>Access Restricted!</b>\n\n"
                f"To use <b>CampusBuzz Kenya</b> 🇰🇪, you must first join our official community:\n\n"
                f"👉 <b>{settings.REQUIRED_CHANNEL_NAME}</b>\n\n"
                "Click the button below to join, then press <b>✅ I Joined</b> to continue."
            )
            kb = force_join_keyboard()

            if isinstance(event, Message):
                await event.answer(msg, reply_markup=kb)
            elif isinstance(event, CallbackQuery):
                await event.message.edit_text(msg, reply_markup=kb)
                await event.answer("⚠️ Please join CampusBuzz first!", show_alert=True)
            return  # Block handler
