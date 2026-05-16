"""
CampusBuzz Kenya - Rate Limit & Anti-Spam Middlewares
"""

import time
from collections import defaultdict, deque
from typing import Callable, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """Token-bucket rate limiter per user."""

    def __init__(self, rate: int = 1, period: int = 1):
        self.rate = rate        # allowed messages
        self.period = period    # per N seconds
        self._buckets: dict[int, deque] = defaultdict(deque)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if not user or user.id == settings.ADMIN_ID:
            return await handler(event, data)

        now = time.time()
        bucket = self._buckets[user.id]

        # Remove timestamps outside the window
        while bucket and bucket[0] < now - self.period:
            bucket.popleft()

        if len(bucket) >= settings.RATE_LIMIT_MESSAGES:
            await event.answer("⏳ Slow down! You're sending messages too fast.")
            return

        bucket.append(now)
        return await handler(event, data)


class AntiSpamMiddleware(BaseMiddleware):
    """Detects repeated identical messages and suspicious links."""

    SUSPICIOUS_PATTERNS = [
        "bit.ly", "tinyurl", "earn money", "free iphone",
        "click here", "limited offer", "winner", "bitcoin"
    ]

    def __init__(self):
        self._last_messages: dict[int, list[str]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        if not isinstance(event, Message) or not event.text:
            return await handler(event, data)

        user = event.from_user
        if not user or user.id == settings.ADMIN_ID:
            return await handler(event, data)

        text = event.text.lower()

        # Suspicious link detection
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in text:
                logger.warning(f"Suspicious message from {user.id}: {text[:80]}")
                await event.answer(
                    "🛡 <b>Suspicious content detected.</b>\n"
                    "This message has been flagged. Repeated violations may result in a ban.",
                )
                return

        # Duplicate spam detection
        history = self._last_messages[user.id]
        if history.count(text) >= 3:
            await event.answer("🚫 Stop spamming! Your account may be restricted.")
            return

        history.append(text)
        if len(history) > 10:
            history.pop(0)

        return await handler(event, data)
