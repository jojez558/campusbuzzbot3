"""
CampusBuzz Kenya - Start Handler
Premium animated-style welcome experience.
"""

import secrets
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.connection import AsyncSessionLocal
from database.models import User
from keyboards.welcome import welcome_keyboard, force_join_keyboard
from config import settings
from middlewares.force_join import check_membership

router = Router()


WELCOME_TEXT = """
🎓 <b>Welcome to CampusBuzz Kenya!</b>
<i>Your #1 student hub for WhatsApp groups across Kenya 🇰🇪</i>

━━━━━━━━━━━━━━━━━━━━━
<b>Discover & Join:</b>

📚 Course & Department groups
🏠 Hostel & accommodation groups  
💼 Internship & job alerts
🎉 Campus events & gigs
📝 Notes & PDF sharing
🆕 Freshers communities
👨‍🎓 Alumni networks
🛒 Student marketplace
━━━━━━━━━━━━━━━━━━━━━

<b>60+ universities · 500+ verified groups · 100% free</b>

Choose an option below to get started 👇
"""

RETURNING_TEXT = """
👋 <b>Welcome back, {name}!</b>

🎓 <b>CampusBuzz Kenya</b> — Your campus, connected.

⭐ You have <b>{xp} XP</b> | 🏅 Badge: <b>{badge}</b>

What are you looking for today?
"""


async def get_or_create_user(
    session: AsyncSession,
    tg_user,
    referral_code: str | None = None,
) -> User:
    user = await session.get(User, tg_user.id)

    if not user:
        # Generate unique referral code
        ref_code = secrets.token_urlsafe(6).upper()

        # Handle referral
        referrer_id = None
        if referral_code:
            result = await session.execute(
                select(User).where(User.referral_code == referral_code)
            )
            referrer = result.scalars().first()
            if referrer and referrer.id != tg_user.id:
                referrer_id = referrer.id
                referrer.xp_points += settings.XP_REFERRAL
                referrer.referral_count += 1

        user = User(
            id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name or "Student",
            referral_code=ref_code,
            referred_by=referrer_id,
        )
        session.add(user)
        await session.flush()
    else:
        # Update name/username if changed
        user.username = tg_user.username
        user.full_name = tg_user.full_name or user.full_name

    return user


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    tg_user = message.from_user

    # Extract referral code from /start payload
    args = message.text.split(maxsplit=1)
    ref_code = args[1].replace("ref_", "").strip() if len(args) > 1 and args[1].startswith("ref_") else None

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_user, ref_code)
        await session.commit()
        is_new = user.joined_at == user.last_active  # rough heuristic

    # Check membership first
    is_member = await check_membership(bot, tg_user.id)
    if not is_member and tg_user.id != settings.ADMIN_ID:
        await message.answer(
            "🚫 <b>Join Required!</b>\n\n"
            "Before using <b>CampusBuzz Kenya</b> 🇰🇪,\n"
            f"you must join our official community:\n\n"
            f"👉 <b>{settings.REQUIRED_CHANNEL_NAME}</b>",
            reply_markup=force_join_keyboard(),
        )
        return

    text = WELCOME_TEXT if is_new else RETURNING_TEXT.format(
        name=tg_user.first_name,
        xp=0,  # will be loaded from user object in production
        badge="🌱 Newcomer",
    )
    await message.answer(text, reply_markup=welcome_keyboard())


@router.callback_query(F.data == "check_join")
async def check_join_callback(call: CallbackQuery, bot: Bot):
    """User pressed 'I Joined' button — recheck membership."""
    is_member = await check_membership(bot, call.from_user.id)

    if is_member:
        await call.answer("✅ Verified! Welcome to CampusBuzz Kenya!", show_alert=False)
        tg_user = call.from_user
        async with AsyncSessionLocal() as session:
            await get_or_create_user(session, tg_user)
            await session.commit()
        await call.message.edit_text(WELCOME_TEXT, reply_markup=welcome_keyboard())
    else:
        await call.answer(
            "❌ You haven't joined yet!\n\nPlease join the channel first, then try again.",
            show_alert=True,
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "❓ <b>CampusBuzz Kenya — Help & FAQ</b>\n\n"
        "<b>Commands:</b>\n"
        "/start — Restart the bot\n"
        "/menu — Open the main menu\n"
        "/universities — Browse all universities\n"
        "/search — Search for groups\n"
        "/trending — View trending groups\n"
        "/freshers — Freshers hub\n"
        "/jobs — Jobs & internships\n"
        "/materials — Study materials\n"
        "/events — Campus events\n"
        "/hostels — Hostel groups\n"
        "/marketplace — Student marketplace\n"
        "/alumni — Alumni network\n"
        "/profile — Your profile & XP\n"
        "/favorites — Saved groups\n"
        "/submitgroup — Submit a WhatsApp group\n"
        "/report — Report a group\n"
        "/settings — Bot settings\n"
        "/contactadmin — Contact @DevMwaura\n"
        "/about — About CampusBuzz\n\n"
        "<b>FAQ:</b>\n"
        "• <i>How do I join a group?</i> — Browse → click group → tap Join\n"
        "• <i>How do I submit my group?</i> — /submitgroup and follow the steps\n"
        "• <i>How do I earn XP?</i> — Daily check-ins, referrals, submissions\n\n"
        f"For more help, contact <b>@{settings.ADMIN_USERNAME}</b>"
    )
    await message.answer(help_text)


@router.message(Command("about"))
async def cmd_about(message: Message):
    await message.answer(
        "ℹ️ <b>About CampusBuzz Kenya</b>\n\n"
        "CampusBuzz Kenya is the #1 Telegram bot for discovering and joining "
        "verified WhatsApp groups for universities and colleges across Kenya.\n\n"
        "🎯 <b>Mission:</b> Connect every Kenyan student with their campus community.\n\n"
        "📊 <b>Stats:</b>\n"
        "• 60+ universities listed\n"
        "• Growing group directory\n"
        "• Verified & moderated groups\n\n"
        "👨‍💻 <b>Built by:</b> @DevMwaura\n"
        "📢 <b>Channel:</b> @CampusBuzz\n\n"
        "<i>Powered by CampusBuzz Kenya 🇰🇪\n"
        "Connecting Kenyan students smarter.</i>"
    )
