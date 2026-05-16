"""
CampusBuzz Kenya - Link Health Monitor
Periodically checks all WhatsApp group invite links and marks dead ones.
Schedule with APScheduler or run as a standalone cron job.
"""

import asyncio
import logging
from datetime import datetime

import httpx
from sqlalchemy import select

from database.connection import AsyncSessionLocal
from database.models import WhatsAppGroup, GroupStatus

logger = logging.getLogger("LinkMonitor")

# WhatsApp returns a 200 even for expired links, but the og:title changes
DEAD_INDICATORS = [
    "invalid link",
    "link may have expired",
    "this invite link is no longer valid",
    "link has expired",
]

TIMEOUT = httpx.Timeout(10.0, connect=5.0)
CONCURRENCY = 10   # parallel checks


async def check_link(client: httpx.AsyncClient, link: str) -> bool:
    """Return True if the link appears active, False if dead/expired."""
    try:
        resp = await client.get(link, timeout=TIMEOUT, follow_redirects=True)
        body = resp.text.lower()
        if resp.status_code == 404:
            return False
        for indicator in DEAD_INDICATORS:
            if indicator in body:
                return False
        return True
    except Exception as e:
        logger.warning(f"Check failed for {link}: {e}")
        return True  # Don't wrongly kill on network error


async def run_health_check():
    """Check all approved groups and update is_link_active status."""
    logger.info("🔍 Starting link health check...")

    async with AsyncSessionLocal() as session:
        groups = (await session.execute(
            select(WhatsAppGroup).where(
                WhatsAppGroup.status == GroupStatus.APPROVED
            )
        )).scalars().all()

    if not groups:
        logger.info("No groups to check.")
        return

    logger.info(f"Checking {len(groups)} groups...")

    semaphore = asyncio.Semaphore(CONCURRENCY)
    results: dict[int, bool] = {}

    async def bounded_check(g: WhatsAppGroup):
        async with semaphore:
            active = await check_link(client, g.link)
            results[g.id] = active
            if not active:
                logger.warning(f"💀 Dead link: [{g.id}] {g.name} — {g.link}")

    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
        await asyncio.gather(*[bounded_check(g) for g in groups])

    # Bulk update
    dead_count = 0
    async with AsyncSessionLocal() as session:
        for g in groups:
            is_active = results.get(g.id, True)
            db_group = await session.get(WhatsAppGroup, g.id)
            if db_group:
                db_group.is_link_active = is_active
                db_group.last_checked = datetime.utcnow()
                if not is_active:
                    dead_count += 1
        await session.commit()

    logger.info(
        f"✅ Health check complete: "
        f"{len(groups) - dead_count} active, {dead_count} dead"
    )
    return {"total": len(groups), "dead": dead_count}


async def schedule_health_checks(interval_hours: int = 6):
    """Run health checks every N hours."""
    while True:
        try:
            await run_health_check()
        except Exception as e:
            logger.error(f"Health check error: {e}")
        await asyncio.sleep(interval_hours * 3600)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_health_check())
