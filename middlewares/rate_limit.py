"""Rate Limiting Middleware for CampusBuzz Kenya"""

import time
from typing import Any, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message


class RateLimitMiddleware(BaseMiddleware):
    """Token bucket rate limiter — limits each user to `rate` messages per `period` seconds."""

    def __init__(self, rate: int = 5, period: int = 10):
        self.rate = rate        # max messages allowed
        self.period = period    # in seconds
        self.buckets: Dict[int, list] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable,
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None

        if user_id is None:
            return await handler(event, data)

        now = time.time()
        timestamps = self.buckets.get(user_id, [])

        # Remove timestamps outside the current window
        timestamps = [t for t in timestamps if now - t < self.period]

        if len(timestamps) >= self.rate:
            # Rate limit exceeded — silently drop the message
            return

        timestamps.append(now)
        self.buckets[user_id] = timestamps

        return await handler(event, data)
