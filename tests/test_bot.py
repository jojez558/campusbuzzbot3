"""
CampusBuzz Kenya — Test Suite
Run with: pytest tests/ -v
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock()
    bot.send_message    = AsyncMock()
    return bot


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id         = 123456789
    user.username   = "test_student"
    user.full_name  = "Test Student"
    user.first_name = "Test"
    return user


@pytest.fixture
def mock_message(mock_user, mock_bot):
    msg = AsyncMock()
    msg.from_user = mock_user
    msg.text      = "/start"
    msg.answer    = AsyncMock()
    msg.bot       = mock_bot
    return msg


# ── Force Join Middleware Tests ───────────────────────────────────────────────

class TestForceJoinMiddleware:

    @pytest.mark.asyncio
    async def test_member_passes_through(self, mock_bot, mock_message):
        from middlewares.force_join import ForceJoinMiddleware, check_membership

        member_mock = MagicMock()
        member_mock.status = "member"
        mock_bot.get_chat_member.return_value = member_mock

        handler = AsyncMock(return_value="ok")
        middleware = ForceJoinMiddleware()

        with patch("middlewares.force_join.check_membership", return_value=True):
            result = await middleware(handler, mock_message, {"bot": mock_bot})

        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_member_blocked(self, mock_bot, mock_message):
        from middlewares.force_join import ForceJoinMiddleware

        handler = AsyncMock(return_value="ok")
        middleware = ForceJoinMiddleware()

        with patch("middlewares.force_join.check_membership", return_value=False):
            with patch("config.settings.ADMIN_ID", 999999):  # not the test user
                result = await middleware(handler, mock_message, {"bot": mock_bot})

        handler.assert_not_called()
        mock_message.answer.assert_called_once()


# ── Rate Limit Tests ──────────────────────────────────────────────────────────

class TestRateLimitMiddleware:

    @pytest.mark.asyncio
    async def test_normal_rate_passes(self, mock_message):
        from middlewares.rate_limit import RateLimitMiddleware

        middleware = RateLimitMiddleware()
        handler = AsyncMock(return_value="ok")

        result = await middleware(handler, mock_message, {})
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_flood_is_blocked(self, mock_message):
        from middlewares.rate_limit import RateLimitMiddleware
        import config
        config.settings.RATE_LIMIT_MESSAGES = 3

        middleware = RateLimitMiddleware()
        handler = AsyncMock(return_value="ok")

        # Send 3 messages fast — all pass
        for _ in range(3):
            await middleware(handler, mock_message, {})

        # 4th message should be rate-limited
        handler.reset_mock()
        mock_message.answer.reset_mock()
        await middleware(handler, mock_message, {})

        handler.assert_not_called()


# ── Anti-Spam Tests ───────────────────────────────────────────────────────────

class TestAntiSpamMiddleware:

    @pytest.mark.asyncio
    async def test_suspicious_link_blocked(self, mock_message):
        from middlewares.anti_spam import AntiSpamMiddleware

        mock_message.text = "Click here to earn free money: bit.ly/scam"
        handler = AsyncMock()
        middleware = AntiSpamMiddleware()

        with patch("config.settings.ADMIN_ID", 999999):
            await middleware(handler, mock_message, {})

        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_clean_message_passes(self, mock_message):
        from middlewares.anti_spam import AntiSpamMiddleware

        mock_message.text = "Hey, looking for CS freshers group at UoN"
        handler = AsyncMock()
        middleware = AntiSpamMiddleware()

        await middleware(handler, mock_message, {})
        handler.assert_called_once()


# ── WhatsApp Link Validation ──────────────────────────────────────────────────

class TestLinkValidation:

    def test_valid_whatsapp_link(self):
        import re
        from handlers.submit_group import WHATSAPP_PATTERN

        valid = "https://chat.whatsapp.com/ABCDEFGHIJ1234567890"
        assert WHATSAPP_PATTERN.match(valid)

    def test_invalid_link_rejected(self):
        from handlers.submit_group import WHATSAPP_PATTERN

        invalid_links = [
            "https://wa.me/254700000000",
            "https://chat.whatsapp.com/short",
            "https://t.me/somechannel",
            "not a link at all",
        ]
        for link in invalid_links:
            assert not WHATSAPP_PATTERN.match(link), f"Should be invalid: {link}"


# ── Gamification / XP Tests ───────────────────────────────────────────────────

class TestGamification:

    def test_badge_progression(self):
        from handlers.profile import compute_badge
        from database.models import User, UserBadge

        user = MagicMock(spec=User)

        user.is_admin      = False
        user.referral_count = 0
        user.xp_points     = 0
        assert compute_badge(user) == UserBadge.NEWCOMER

        user.xp_points = 100
        assert compute_badge(user) == UserBadge.CONTRIBUTOR

        user.xp_points = 500
        assert compute_badge(user) == UserBadge.CAMPUS_LEGEND

        user.referral_count = 5
        assert compute_badge(user) == UserBadge.AMBASSADOR

        user.is_admin = True
        assert compute_badge(user) == UserBadge.ADMIN


# ── Database Seed Tests ───────────────────────────────────────────────────────

class TestSeedData:

    def test_counties_count(self):
        from database.seed import COUNTIES
        assert len(COUNTIES) == 47, "Kenya has exactly 47 counties"

    def test_universities_have_required_fields(self):
        from database.seed import UNIVERSITIES
        for uni in UNIVERSITIES:
            assert "name"   in uni, f"Missing 'name' in {uni}"
            assert "type"   in uni, f"Missing 'type' in {uni}"
            assert "county" in uni, f"Missing 'county' in {uni}"

    def test_university_names_unique(self):
        from database.seed import UNIVERSITIES
        names = [u["name"] for u in UNIVERSITIES]
        assert len(names) == len(set(names)), "Duplicate university names found"
