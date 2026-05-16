"""
CampusBuzz Kenya - Main Entry Point
A premium Telegram bot connecting Kenyan university students
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.connection import init_db
from handlers.start import router as start_router
from handlers.menu import router as menu_router
from handlers.universities import router as universities_router
from handlers.search import router as search_router
from handlers.profile import router as profile_router
from handlers.favorites import router as favorites_router
from handlers.submit_group import router as submit_group_router
from handlers.report import router as report_router
from handlers.admin import router as admin_router
from handlers._categories import (
    freshers_router, jobs_router, materials_router, events_router,
    hostels_router, marketplace_router, alumni_router,
    settings_router, trending_router,
)
from middlewares.force_join import ForceJoinMiddleware
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.anti_spam import AntiSpamMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CampusBuzz")


async def build_storage():
    redis_url = getattr(settings, "REDIS_URL", None) or ""
    if redis_url.strip():
        try:
            from aiogram.fsm.storage.redis import RedisStorage
            import redis.asyncio as aioredis
            client = aioredis.from_url(redis_url, socket_connect_timeout=3)
            await client.ping()
            await client.aclose()
            logger.info("💾 Storage: RedisStorage (%s)", redis_url)
            return RedisStorage.from_url(redis_url)
        except Exception as e:
            logger.warning("⚠️  Redis not reachable (%s) — falling back to MemoryStorage", e)

    logger.info("💾 Storage: MemoryStorage (local dev mode)")
    return MemoryStorage()


async def on_startup(bot: Bot):
    logger.info("🚀 CampusBuzz Kenya is starting up...")
    await init_db()
    logger.info("✅ Database initialized")

    from aiogram.types import BotCommand, BotCommandScopeDefault
    commands = [
        BotCommand(command="start",        description="🏠 Start CampusBuzz"),
        BotCommand(command="menu",         description="📋 Main menu"),
        BotCommand(command="universities", description="🎓 Browse universities"),
        BotCommand(command="search",       description="🔍 Search groups"),
        BotCommand(command="trending",     description="⭐ Trending groups"),
        BotCommand(command="freshers",     description="🆕 Freshers hub"),
        BotCommand(command="jobs",         description="💼 Jobs & internships"),
        BotCommand(command="materials",    description="📚 Study materials"),
        BotCommand(command="events",       description="🎉 Campus events"),
        BotCommand(command="hostels",      description="🏠 Hostels & housing"),
        BotCommand(command="marketplace",  description="🛒 Student marketplace"),
        BotCommand(command="alumni",       description="👨‍🎓 Alumni network"),
        BotCommand(command="profile",      description="👤 My profile"),
        BotCommand(command="favorites",    description="❤️ Saved groups"),
        BotCommand(command="submitgroup",  description="➕ Submit a group"),
        BotCommand(command="report",       description="🛡 Report a group"),
        BotCommand(command="settings",     description="⚙️ Settings"),
        BotCommand(command="contactadmin", description="📞 Contact admin"),
        BotCommand(command="about",        description="ℹ️ About CampusBuzz"),
        BotCommand(command="help",         description="❓ Help & FAQ"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("✅ Bot commands registered")

    try:
        await bot.send_message(
            settings.ADMIN_ID,
            "🟢 <b>CampusBuzz Kenya is ONLINE</b>\n"
            f"⏰ Started at: {asyncio.get_event_loop().time():.0f}s uptime\n"
            "📡 Webhook/Polling active.",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass


async def on_shutdown(bot: Bot):
    logger.info("🔴 CampusBuzz Kenya is shutting down...")


async def main():
    # ── Token diagnostics ────────────────────────────────────────────────────
    token = settings.BOT_TOKEN
    if not token:
        logger.critical(
            "❌ BOT_TOKEN is not set or is empty. "
            "Make sure the BOT_TOKEN environment variable is configured in Railway."
        )
        return
    if ":" not in token:
        logger.critical(
            "❌ BOT_TOKEN looks malformed (no ':' separator found). "
            "A valid token looks like '123456789:ABCdef...'. "
            "Current value starts with: %r",
            token[:10] + "..." if len(token) > 10 else token,
        )
        return
    token_id, _, token_secret = token.partition(":")
    if not token_id.isdigit():
        logger.critical(
            "❌ BOT_TOKEN prefix (before ':') is not a numeric bot ID. "
            "Current prefix: %r",
            token_id,
        )
        return
    logger.info(
        "✅ BOT_TOKEN present — bot ID prefix: %s, secret length: %d",
        token_id,
        len(token_secret),
    )
    # ── End token diagnostics ────────────────────────────────────────────────

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=await build_storage())

    # Register middlewares (order matters)
    dp.message.middleware(RateLimitMiddleware(rate=1, period=1))
    dp.message.middleware(AntiSpamMiddleware())
    dp.message.middleware(ForceJoinMiddleware())
    dp.callback_query.middleware(ForceJoinMiddleware())

    # Register routers (admin last so it never swallows general commands)
    dp.include_routers(
        start_router,
        menu_router,
        universities_router,
        search_router,
        trending_router,
        freshers_router,
        jobs_router,
        materials_router,
        events_router,
        hostels_router,
        marketplace_router,
        alumni_router,
        profile_router,
        favorites_router,
        submit_group_router,
        report_router,
        settings_router,
        admin_router,
    )

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if getattr(settings, "WEBHOOK_URL", None):
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        from aiohttp import web

        app = web.Application()
        handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        handler.register(app, path=f"/webhook/{settings.BOT_TOKEN}")
        setup_application(app, dp, bot=bot)

        await bot.set_webhook(
            url=f"{settings.WEBHOOK_URL}/webhook/{settings.BOT_TOKEN}",
            drop_pending_updates=True
        )
        web.run_app(app, host="0.0.0.0", port=settings.PORT)
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())