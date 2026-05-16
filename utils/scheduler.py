"""
CampusBuzz Kenya - Scheduled Tasks
Daily analytics, trending computation, link health checks.
Run alongside the bot using asyncio tasks.
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from sqlalchemy import select, func, update

from database.connection import AsyncSessionLocal
from database.models import (
    WhatsAppGroup, GroupStatus, User, BotStat
)
from utils.link_monitor import run_health_check

logger = logging.getLogger("Scheduler")


async def compute_trending():
    """
    Mark top groups by view_count in the last 7 days as trending.
    Resets trending flag and re-assigns top 20.
    """
    async with AsyncSessionLocal() as session:
        # Reset all trending
        await session.execute(
            update(WhatsAppGroup).values(is_trending=False)
        )

        # Top 20 by view_count
        top = (await session.execute(
            select(WhatsAppGroup.id)
            .where(WhatsAppGroup.status == GroupStatus.APPROVED)
            .order_by(WhatsAppGroup.view_count.desc())
            .limit(20)
        )).scalars().all()

        for gid in top:
            g = await session.get(WhatsAppGroup, gid)
            if g:
                g.is_trending = True

        await session.commit()
    logger.info(f"✅ Trending updated: {len(top)} groups marked")


async def snapshot_daily_stats():
    """Save a daily analytics snapshot to bot_stats table."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)

    async with AsyncSessionLocal() as session:
        total_users  = (await session.execute(select(func.count(User.id)))).scalar_one()
        new_users    = (await session.execute(
            select(func.count(User.id)).where(User.joined_at >= yesterday)
        )).scalar_one()
        total_groups = (await session.execute(
            select(func.count(WhatsAppGroup.id))
            .where(WhatsAppGroup.status == GroupStatus.APPROVED)
        )).scalar_one()
        new_groups   = (await session.execute(
            select(func.count(WhatsAppGroup.id))
            .where(
                WhatsAppGroup.status == GroupStatus.APPROVED,
                WhatsAppGroup.created_at >= yesterday,
            )
        )).scalar_one()
        total_views  = (await session.execute(
            select(func.sum(WhatsAppGroup.view_count))
        )).scalar_one() or 0

        stat = BotStat(
            date=today,
            total_users=total_users,
            new_users=new_users,
            total_groups=total_groups,
            new_groups=new_groups,
            total_clicks=total_views,
        )
        session.add(stat)
        try:
            await session.commit()
            logger.info(
                f"📊 Daily snapshot: {total_users} users, "
                f"{total_groups} groups, {new_users} new users"
            )
        except Exception:
            await session.rollback()  # Duplicate date key — already snapshotted


async def expire_old_links():
    """Mark groups whose expires_at has passed as expired."""
    now = datetime.utcnow()
    async with AsyncSessionLocal() as session:
        expired = (await session.execute(
            select(WhatsAppGroup).where(
                WhatsAppGroup.expires_at <= now,
                WhatsAppGroup.status == GroupStatus.APPROVED,
            )
        )).scalars().all()

        for g in expired:
            g.status = GroupStatus.EXPIRED
            g.is_link_active = False

        if expired:
            await session.commit()
            logger.info(f"⏰ Expired {len(expired)} group(s) past their expiry date")


async def run_all_scheduled():
    """Main scheduler loop — runs all tasks on their respective intervals."""
    logger.info("⏰ Scheduler started")

    async def every(coro_factory, hours: float, name: str):
        while True:
            try:
                logger.info(f"▶ Running: {name}")
                await coro_factory()
                logger.info(f"✅ Done: {name}")
            except Exception as e:
                logger.error(f"❌ {name} failed: {e}")
            await asyncio.sleep(hours * 3600)

    await asyncio.gather(
        every(compute_trending,     hours=1,  name="compute_trending"),
        every(snapshot_daily_stats, hours=24, name="daily_stats"),
        every(expire_old_links,     hours=6,  name="expire_links"),
        every(run_health_check,     hours=6,  name="link_health"),
    )
