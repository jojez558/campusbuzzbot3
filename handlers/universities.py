"""
CampusBuzz Kenya - Universities Handler
Browse all universities, paginated, by type, with group categories.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select, func

from database.connection import AsyncSessionLocal
from database.models import University, WhatsAppGroup, UniversityType, GroupCategory, GroupStatus
from keyboards.welcome import (
    universities_category_keyboard,
    universities_list_keyboard,
    university_detail_keyboard,
    groups_list_keyboard,
    group_card_keyboard,
)
from config import settings

router = Router()

TYPE_LABELS = {
    "public":  ("🏛️", "Public Universities"),
    "private": ("🏫", "Private Universities"),
    "tvet":    ("🔧", "TVETs & Colleges"),
}

CAT_LABELS = {
    "official":    "🏛️ Official Groups",
    "faculty":     "📖 Faculty Groups",
    "hostel":      "🏠 Hostel Groups",
    "freshers":    "🆕 Freshers Groups",
    "jobs":        "💼 Jobs & Attachments",
    "notes":       "📚 Notes Sharing",
    "marketplace": "🛒 Buy & Sell",
    "alumni":      "👨‍🎓 Alumni",
}


# ── /universities command ─────────────────────────────────────────────────────

@router.message(Command("universities"))
async def cmd_universities(message: Message):
    await message.answer(
        "🎓 <b>Universities & Colleges</b>\n\n"
        "Choose a category to browse:",
        reply_markup=universities_category_keyboard(),
    )


@router.callback_query(F.data == "nav:universities")
async def nav_universities(call: CallbackQuery):
    await call.message.edit_text(
        "🎓 <b>Universities & Colleges</b>\n\n"
        "Choose a category to browse:",
        reply_markup=universities_category_keyboard(),
    )
    await call.answer()


# ── Type selection → paginated list ─────────────────────────────────────────

@router.callback_query(F.data.startswith("uni_type:"))
async def uni_type_list(call: CallbackQuery):
    uni_type = call.data.split(":")[1]  # public / private / tvet
    await _show_uni_list(call, uni_type, page=0)


@router.callback_query(F.data.startswith("uni_list:"))
async def uni_list_page(call: CallbackQuery):
    _, uni_type, page = call.data.split(":")
    await _show_uni_list(call, uni_type, page=int(page))


async def _show_uni_list(call: CallbackQuery, uni_type: str, page: int):
    per_page = settings.ITEMS_PER_PAGE
    emoji, label = TYPE_LABELS.get(uni_type, ("🎓", "Universities"))

    async with AsyncSessionLocal() as session:
        q = select(University).where(
            University.type == uni_type,
            University.is_active == True,
        ).order_by(University.name)

        total_q = select(func.count()).select_from(q.subquery())
        total = (await session.execute(total_q)).scalar_one()

        unis = (await session.execute(
            q.offset(page * per_page).limit(per_page)
        )).scalars().all()

    text = (
        f"{emoji} <b>{label}</b>\n"
        f"<i>Showing {page*per_page+1}–{min((page+1)*per_page, total)} of {total}</i>\n\n"
        "Tap a university to explore its WhatsApp groups 👇"
    )
    kb = universities_list_keyboard(unis, page, total, per_page, uni_type)
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()


# ── University detail page ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("uni:"))
async def uni_detail(call: CallbackQuery):
    uni_id = int(call.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        uni = await session.get(University, uni_id)
        if not uni:
            await call.answer("University not found.", show_alert=True)
            return

        # Count total groups
        count_q = select(func.count()).where(
            WhatsAppGroup.university_id == uni_id,
            WhatsAppGroup.status == GroupStatus.APPROVED,
        )
        group_count = (await session.execute(count_q)).scalar_one()

    text = (
        f"🎓 <b>{uni.name}</b>\n"
        f"{'(' + uni.short_name + ')' if uni.short_name else ''}\n\n"
        f"📁 <b>{group_count} WhatsApp groups</b> available\n\n"
        "Select a category to browse groups 👇"
    )
    await call.message.edit_text(text, reply_markup=university_detail_keyboard(uni_id))
    await call.answer()


# ── Category inside a university ──────────────────────────────────────────────

@router.callback_query(F.data.startswith("unicat:"))
async def uni_category_groups(call: CallbackQuery):
    _, uni_id_str, cat = call.data.split(":")
    uni_id = int(uni_id_str)
    page = 0
    await _show_category_groups(call, uni_id, cat, page)


@router.callback_query(F.data.startswith("page:group_open:"))
async def groups_next_page(call: CallbackQuery):
    parts = call.data.split(":")
    # format: page:group_open:{page}  (we need context — use state in production)
    await call.answer("Use the back button to navigate.", show_alert=False)


async def _show_category_groups(
    call: CallbackQuery, uni_id: int, cat: str, page: int
):
    per_page = settings.GROUPS_PER_PAGE
    cat_label = CAT_LABELS.get(cat, "Groups")

    async with AsyncSessionLocal() as session:
        uni = await session.get(University, uni_id)
        uni_name = uni.name if uni else "University"

        q = select(WhatsAppGroup).where(
            WhatsAppGroup.university_id == uni_id,
            WhatsAppGroup.category == cat,
            WhatsAppGroup.status == GroupStatus.APPROVED,
            WhatsAppGroup.is_link_active == True,
        ).order_by(
            WhatsAppGroup.is_sponsored.desc(),
            WhatsAppGroup.is_verified.desc(),
            WhatsAppGroup.join_count.desc(),
        )

        total = (await session.execute(
            select(func.count()).select_from(q.subquery())
        )).scalar_one()

        groups = (await session.execute(
            q.offset(page * per_page).limit(per_page)
        )).scalars().all()

    if not groups:
        from keyboards.welcome import _back, _home
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        kb = InlineKeyboardBuilder()
        kb.row(_back(f"uni:{uni_id}"))
        kb.row(_home())
        await call.message.edit_text(
            f"😔 <b>No {cat_label} groups yet</b> for {uni_name}.\n\n"
            "Be the first to submit one! /submitgroup",
            reply_markup=kb.as_markup(),
        )
        await call.answer()
        return

    text = (
        f"📁 <b>{uni_name}</b>\n"
        f"📂 {cat_label}\n\n"
        f"<i>{total} group(s) found — Showing page {page+1}</i>\n\n"
        "✅ = Verified  🔥 = Trending  💎 = Sponsored\n"
        "Tap a group to view & join 👇"
    )
    kb = groups_list_keyboard(
        groups, page, total, per_page,
        back_target=f"uni:{uni_id}",
        cb_prefix=f"group_open",
    )
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()


# ── Group detail / card ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("group_open:"))
async def open_group(call: CallbackQuery):
    group_id = int(call.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        group = await session.get(WhatsAppGroup, group_id)
        if not group:
            await call.answer("Group not found.", show_alert=True)
            return

        # Increment view count
        group.view_count += 1
        await session.commit()

        uni = await session.get(University, group.university_id) if group.university_id else None

        # Check if user favorited
        from database.models import Favorite
        fav_q = select(Favorite).where(
            Favorite.user_id == call.from_user.id,
            Favorite.group_id == group_id,
        )
        is_fav = bool((await session.execute(fav_q)).scalars().first())

    badges = []
    if group.is_verified:  badges.append("✅ Verified")
    if group.is_trending:  badges.append("🔥 Trending")
    if group.is_sponsored: badges.append("💎 Sponsored")

    text = (
        f"{'  '.join(badges)}\n\n" if badges else ""
        f"📱 <b>{group.name}</b>\n\n"
        f"🏫 <b>University:</b> {uni.name if uni else 'N/A'}\n"
        f"📂 <b>Category:</b> {group.category.value.title()}\n"
        f"👁 <b>Views:</b> {group.view_count:,}  |  🚀 <b>Joins:</b> {group.join_count:,}\n\n"
        f"{'📝 ' + group.description + chr(10) + chr(10) if group.description else ''}"
        f"{'📜 <b>Rules:</b> ' + group.rules[:200] + chr(10) + chr(10) if group.rules else ''}"
        f"⚠️ <i>Always verify before sharing personal info in any group.</i>"
    )
    kb = group_card_keyboard(group_id, group.link, is_fav)
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()
