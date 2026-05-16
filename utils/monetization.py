"""
CampusBuzz Kenya - Monetization Manager
Sponsored groups, premium placement, partner promotions.
Toggle with ENABLE_MONETIZATION=true in .env
"""

from datetime import datetime, timedelta
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import WhatsAppGroup, GroupStatus
import logging

logger = logging.getLogger("Monetization")


class SponsoredSlot:
    """Represents a paid sponsored group slot."""

    DAILY_RATE_KES   = 200    # KES per day for sponsored placement
    WEEKLY_RATE_KES  = 1000   # KES per week
    MONTHLY_RATE_KES = 3000   # KES per month

    @staticmethod
    async def activate(group_id: int, days: int = 7) -> bool:
        """Mark a group as sponsored for N days."""
        expires = datetime.utcnow() + timedelta(days=days)
        async with AsyncSessionLocal() as session:
            g = await session.get(WhatsAppGroup, group_id)
            if not g or g.status != GroupStatus.APPROVED:
                return False
            g.is_sponsored = True
            g.expires_at   = expires
            await session.commit()
        logger.info(f"💎 Group {group_id} sponsored for {days} days")
        return True

    @staticmethod
    async def deactivate_expired():
        """Remove sponsorship from expired slots."""
        now = datetime.utcnow()
        async with AsyncSessionLocal() as session:
            expired = (await session.execute(
                select(WhatsAppGroup).where(
                    WhatsAppGroup.is_sponsored == True,
                    WhatsAppGroup.expires_at <= now,
                )
            )).scalars().all()
            for g in expired:
                g.is_sponsored = False
                logger.info(f"⌛ Sponsorship expired for group {g.id}: {g.name}")
            if expired:
                await session.commit()
        return len(expired)


# ── Pricing display helper ────────────────────────────────────────────────────

PRICING_TEXT = """
💎 <b>Sponsor Your Group on CampusBuzz Kenya</b>

Get <b>premium placement</b> at the top of all listings!

📦 <b>Packages:</b>
┌─────────────────────────────┐
│ 🗓 Daily     → KES 200/day  │
│ 📅 Weekly   → KES 1,000/wk │
│ 📆 Monthly  → KES 3,000/mo │
└─────────────────────────────┘

✅ Your group appears <b>first</b> in all searches
✅ 💎 Sponsored badge displayed
✅ Priority in trending lists
✅ Featured in broadcast announcements

<i>Payment via M-Pesa. Contact @DevMwaura to activate.</i>
"""


def get_pricing_text() -> str:
    return PRICING_TEXT
