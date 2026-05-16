"""
CampusBuzz Kenya - Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── Bot Credentials ──────────────────────────────────────────────────────
    BOT_TOKEN: str
    ADMIN_ID: int
    ADMIN_USERNAME: str = "DevMwaura"
    BOT_USERNAME: str = "CampusBuzzKEBot"

    # ── Force Join ───────────────────────────────────────────────────────────
    REQUIRED_CHANNEL: str = "@CampusBuzz"
    REQUIRED_CHANNEL_LINK: str = "https://t.me/CampusBuzz"
    REQUIRED_CHANNEL_NAME: str = "CampusBuzz"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://campusbuzz:password@localhost/campusbuzz"
    # FIX: Optional so an empty or missing REDIS_URL in .env
    #      doesn't fall back to the localhost default.
    #      Set to a real URL in production, leave unset for local dev.
    REDIS_URL: Optional[str] = None

    # ── Webhook (leave empty for polling) ────────────────────────────────────
    WEBHOOK_URL: Optional[str] = None
    PORT: int = 8080

    # ── Pagination ───────────────────────────────────────────────────────────
    ITEMS_PER_PAGE: int = 8
    GROUPS_PER_PAGE: int = 5

    # ── Rate Limiting ────────────────────────────────────────────────────────
    RATE_LIMIT_MESSAGES: int = 5
    RATE_LIMIT_PERIOD: int = 10
    MAX_SPAM_STRIKES: int = 3

    # ── Gamification ─────────────────────────────────────────────────────────
    XP_JOIN_DAILY: int = 10
    XP_SUBMIT_GROUP: int = 50
    XP_REFERRAL: int = 100
    XP_REPORT_VALID: int = 25

    # ── Features ─────────────────────────────────────────────────────────────
    ENABLE_AI_SUGGESTIONS: bool = False
    ENABLE_MONETIZATION: bool = False
    MAINTENANCE_MODE: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()