"""
CampusBuzz Kenya - Profile Handler
XP, badges, referrals, daily check-in, leaderboard.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select, func
from datetime import datetime, date

from database.connection import AsyncSessionLocal
from database.models import User, WhatsAppGroup, Favorite, UserBadge
from keyboards.welcome import profile_keyboard, _home, _btn
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings

router = Router()

BADGE_INFO = {
    UserBadge.NEWCOMER:       ("🌱", "Newcomer",      "Just getting started"),
    UserBadge.CONTRIBUTOR:    ("⭐", "Contributor",    "Submitted 3+ groups"),
    UserBadge.VERIFIED:       ("✅", "Verified",       "Identity verified"),
    UserBadge.CAMPUS_LEGEND:  ("🏆", "Campus Legend",  "500+ XP earned"),
    UserBadge.AMBASSADOR:     ("🦁", "Ambassador",     "5+ referrals"),
    UserBadge.ADMIN:          ("🛡", "Admin",          "CampusBuzz admin"),
}

XP_THRESHOLDS = {
    100:  UserBadge.CONTRIBUTOR,
    500:  UserBadge.CAMPUS_LEGEND,
}


def compute_badge(user: User) -> UserBadge:
    if user.is_admin:
        return UserBadge.ADMIN
    if user.referral_count >= 5:
        return UserBadge.AMBASSADOR
    for xp_needed, badge in sorted(XP_THRESHOLDS.items(), reverse=True):
        if user.xp_points >= xp_needed:
            return badge
    return UserBadge.NEWCOMER


@router.message(Command("profile"))
@router.callback_query(F.data == "nav:profile")
async def show_profile(event):
    user_id = event.from_user.id

    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            if isinstance(event, Message):
                await event.answer("❌ Profile not found. Use /start to register.")
            return

        fav_count = (await session.execute(
            select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        )).scalar_one()

        sub_count = (await session.execute(
            select(func.count(WhatsAppGroup.id))
            .where(WhatsAppGroup.submitter_id == user_id)
        )).scalar_one()

        # Update badge dynamically
        new_badge = compute_badge(user)
        if user.badge != new_badge:
            user.badge = new_badge
            await session.commit()

        badge_em, badge_name, _ = BADGE_INFO.get(user.badge, ("🌱", "Newcomer", ""))

    ref_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user.referral_code}"

    text = (
        f"👤 <b>My Profile</b>\n\n"
        f"👋 <b>Name:</b> {user.full_name}\n"
        f"📌 <b>Username:</b> @{user.username or 'N/A'}\n"
        f"🎓 <b>University:</b> {'Set in settings' if not user.university_id else 'Linked'}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{badge_em} <b>Badge:</b> {badge_name}\n"
        f"⭐ <b>XP Points:</b> {user.xp_points:,}\n"
        f"❤️ <b>Saved Groups:</b> {fav_count}\n"
        f"➕ <b>Submitted:</b> {sub_count} group(s)\n"
        f"🔗 <b>Referrals:</b> {user.referral_count}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🎁 <b>Your Referral Link:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"<i>Share your link and earn {settings.XP_REFERRAL} XP per referral!</i>"
    )

    kb = profile_keyboard(user_id)
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)
        await event.answer()


@router.callback_query(F.data == "profile:daily")
async def daily_checkin(call: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, call.from_user.id)
        if not user:
            await call.answer("Profile not found.", show_alert=True)
            return

        today = date.today()
        last = user.last_daily.date() if user.last_daily else None

        if last == today:
            await call.answer("✅ Already checked in today! Come back tomorrow.", show_alert=True)
            return

        user.xp_points += settings.XP_JOIN_DAILY
        user.last_daily = datetime.utcnow()
        await session.commit()

    await call.answer(f"🎁 +{settings.XP_JOIN_DAILY} XP! See you tomorrow!", show_alert=True)


@router.callback_query(F.data == "profile:leaderboard")
async def leaderboard(call: CallbackQuery):
    async with AsyncSessionLocal() as session:
        top = (await session.execute(
            select(User).order_by(User.xp_points.desc()).limit(10)
        )).scalars().all()

    lines = ["🏆 <b>CampusBuzz Leaderboard</b>\n"]
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    for i, u in enumerate(top):
        badge_em = BADGE_INFO.get(u.badge, ("⭐",))[0]
        name = f"@{u.username}" if u.username else u.full_name[:15]
        lines.append(f"{medals[i]} <b>{name}</b> — {u.xp_points:,} XP {badge_em}")

    kb = InlineKeyboardBuilder()
    kb.row(_btn("◀️ Back", "nav:profile"), _home())
    await call.message.edit_text("\n".join(lines), reply_markup=kb.as_markup())
    await call.answer()
