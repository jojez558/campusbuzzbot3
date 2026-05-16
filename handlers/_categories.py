"""
CampusBuzz Kenya - Category Handlers
Jobs, Freshers, Materials, Events, Hostels, Marketplace, Alumni, Settings, Trending
All follow the same pattern: filter groups by category and display paginated list.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select, func

from database.connection import AsyncSessionLocal
from database.models import WhatsAppGroup, GroupCategory, GroupStatus, User
from keyboards.welcome import groups_list_keyboard, settings_keyboard, _home, _btn
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings

# One router per "file" — combine them all here for brevity
# In production split into separate files

freshers_router   = Router()
jobs_router       = Router()
materials_router  = Router()
events_router     = Router()
hostels_router    = Router()
marketplace_router= Router()
alumni_router     = Router()
settings_router   = Router()
trending_router   = Router()

# Re-export under expected names for main.py
router = freshers_router   # placeholder; main.py imports each individually


# ── Generic category view helper ─────────────────────────────────────────────

async def _category_view(event, category: GroupCategory, title: str, emoji: str, page: int = 0):
    per_page = settings.GROUPS_PER_PAGE

    async with AsyncSessionLocal() as session:
        q = select(WhatsAppGroup).where(
            WhatsAppGroup.category == category,
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
        groups = (await session.execute(q.offset(page * per_page).limit(per_page))).scalars().all()

    if not groups:
        kb = InlineKeyboardBuilder()
        kb.row(_btn("➕ Submit Group", "nav:submit_group"), _home())
        msg = f"{emoji} <b>{title}</b>\n\nNo groups available yet. Be the first to submit!"
        if isinstance(event, Message):
            await event.answer(msg, reply_markup=kb.as_markup())
        else:
            await event.message.edit_text(msg, reply_markup=kb.as_markup())
            await event.answer()
        return

    msg = (
        f"{emoji} <b>{title}</b>\n"
        f"<i>{total} group(s) — Page {page+1}</i>\n\n"
        "✅ = Verified  🔥 = Trending\n"
        "Tap to view & join 👇"
    )
    kb = groups_list_keyboard(groups, page, total, per_page, "main_menu", f"group_open")
    if isinstance(event, Message):
        await event.answer(msg, reply_markup=kb)
    else:
        await event.message.edit_text(msg, reply_markup=kb)
        await event.answer()


# ── Freshers ──────────────────────────────────────────────────────────────────

@freshers_router.message(Command("freshers"))
@freshers_router.callback_query(F.data == "nav:freshers")
async def freshers_hub(event):
    await _category_view(event, GroupCategory.FRESHERS, "Freshers Hub", "🆕")


# ── Jobs & Internships ────────────────────────────────────────────────────────

@jobs_router.message(Command("jobs"))
@jobs_router.callback_query(F.data == "nav:jobs")
async def jobs_hub(event):
    await _category_view(event, GroupCategory.JOBS, "Jobs & Internships", "💼")


# ── Study Materials ───────────────────────────────────────────────────────────

@materials_router.message(Command("materials"))
@materials_router.callback_query(F.data == "nav:materials")
async def materials_hub(event):
    await _category_view(event, GroupCategory.NOTES, "Study Materials & Notes", "📚")


# ── Campus Events ─────────────────────────────────────────────────────────────

@events_router.message(Command("events"))
@events_router.callback_query(F.data == "nav:events")
async def events_hub(event):
    await _category_view(event, GroupCategory.EVENTS, "Campus Events & Gigs", "🎉")


# ── Hostels ───────────────────────────────────────────────────────────────────

@hostels_router.message(Command("hostels"))
@hostels_router.callback_query(F.data == "nav:hostels")
async def hostels_hub(event):
    await _category_view(event, GroupCategory.HOSTEL, "Hostels & Housing", "🏠")


# ── Marketplace ───────────────────────────────────────────────────────────────

@marketplace_router.message(Command("marketplace"))
@marketplace_router.callback_query(F.data == "nav:marketplace")
async def marketplace_hub(event):
    await _category_view(event, GroupCategory.MARKETPLACE, "Student Marketplace", "🛒")


# ── Alumni ────────────────────────────────────────────────────────────────────

@alumni_router.message(Command("alumni"))
@alumni_router.callback_query(F.data == "nav:alumni")
async def alumni_hub(event):
    await _category_view(event, GroupCategory.ALUMNI, "Alumni Network", "👨‍🎓")


# ── Trending ──────────────────────────────────────────────────────────────────

@trending_router.message(Command("trending"))
@trending_router.callback_query(F.data == "nav:trending")
async def trending_groups(event):
    per_page = settings.GROUPS_PER_PAGE
    async with AsyncSessionLocal() as session:
        q = select(WhatsAppGroup).where(
            WhatsAppGroup.status == GroupStatus.APPROVED,
            WhatsAppGroup.is_link_active == True,
            WhatsAppGroup.is_trending == True,
        ).order_by(WhatsAppGroup.view_count.desc())
        total  = (await session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        groups = (await session.execute(q.limit(per_page))).scalars().all()

    # Fallback: top by views
    if not groups:
        async with AsyncSessionLocal() as session:
            q = select(WhatsAppGroup).where(
                WhatsAppGroup.status == GroupStatus.APPROVED,
                WhatsAppGroup.is_link_active == True,
            ).order_by(WhatsAppGroup.view_count.desc())
            total  = (await session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
            groups = (await session.execute(q.limit(per_page))).scalars().all()

    msg = (
        "⭐ <b>Trending Groups This Week</b>\n"
        f"<i>Top {min(len(groups), per_page)} most popular groups</i>\n\n"
        "🔥 = Trending  ✅ = Verified\n"
        "Tap to join 👇"
    )
    kb = groups_list_keyboard(groups, 0, total, per_page, "main_menu", "group_open")
    if isinstance(event, Message):
        await event.answer(msg, reply_markup=kb)
    else:
        await event.message.edit_text(msg, reply_markup=kb)
        await event.answer()


# ── Settings ──────────────────────────────────────────────────────────────────

@settings_router.message(Command("settings"))
@settings_router.callback_query(F.data == "nav:settings")
async def show_settings(event):
    user_id = event.from_user.id
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        notif = user.notification_on if user else True
        lang  = user.language if user else "en"

    msg = (
        "⚙️ <b>Settings</b>\n\n"
        "Customize your CampusBuzz experience:"
    )
    kb = settings_keyboard(notif, lang)
    if isinstance(event, Message):
        await event.answer(msg, reply_markup=kb)
    else:
        await event.message.edit_text(msg, reply_markup=kb)
        await event.answer()


@settings_router.callback_query(F.data == "settings:toggle_notif")
async def toggle_notifications(call: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, call.from_user.id)
        if user:
            user.notification_on = not user.notification_on
            await session.commit()
            notif = user.notification_on
            lang  = user.language
        else:
            notif, lang = True, "en"

    await call.message.edit_reply_markup(reply_markup=settings_keyboard(notif, lang))
    status = "ON ✅" if notif else "OFF ❌"
    await call.answer(f"🔔 Notifications {status}")


@settings_router.callback_query(F.data == "settings:toggle_lang")
async def toggle_language(call: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, call.from_user.id)
        if user:
            user.language = "sw" if user.language == "en" else "en"
            await session.commit()
            notif = user.notification_on
            lang  = user.language
        else:
            notif, lang = True, "en"

    await call.message.edit_reply_markup(reply_markup=settings_keyboard(notif, lang))
    lang_name = "Kiswahili 🇰🇪" if lang == "sw" else "English 🇬🇧"
    await call.answer(f"🌐 Language: {lang_name}")


# ── Contact Admin ─────────────────────────────────────────────────────────────

@settings_router.message(Command("contactadmin"))
async def contact_admin(message: Message):
    await message.answer(
        "📞 <b>Contact Admin</b>\n\n"
        f"For support, feedback, or group submissions:\n\n"
        f"👤 Telegram: @{settings.ADMIN_USERNAME}\n\n"
        "<i>Response time: Usually within 24 hours.\n"
        "Powered by CampusBuzz Kenya 🇰🇪</i>",
        reply_markup=InlineKeyboardBuilder().row(
            __import__("aiogram").types.InlineKeyboardButton(
                text=f"📩 Message @{settings.ADMIN_USERNAME}",
                url=f"https://t.me/{settings.ADMIN_USERNAME}",
            )
        ).as_markup(),
    )


# ── By County ────────────────────────────────────────────────────────────────

@settings_router.callback_query(F.data == "nav:by_county")
async def by_county(call: CallbackQuery):
    from database.models import County
    from keyboards.welcome import counties_keyboard
    async with AsyncSessionLocal() as session:
        counties = (await session.execute(
            select(County).order_by(County.name)
        )).scalars().all()

    await call.message.edit_text(
        "📍 <b>Browse by County</b>\n\nSelect your county:",
        reply_markup=counties_keyboard(counties),
    )
    await call.answer()


@settings_router.callback_query(F.data.startswith("county:"))
async def county_universities(call: CallbackQuery):
    county_id = int(call.data.split(":")[1])
    from database.models import University, County
    from keyboards.welcome import universities_list_keyboard

    async with AsyncSessionLocal() as session:
        county = await session.get(County, county_id)
        unis = (await session.execute(
            select(University)
            .where(University.county_id == county_id, University.is_active == True)
            .order_by(University.name)
        )).scalars().all()

    if not unis:
        kb = InlineKeyboardBuilder()
        kb.row(_btn("◀️ Back", "nav:by_county"), _home())
        await call.message.edit_text(
            f"😔 No universities listed in <b>{county.name} County</b> yet.",
            reply_markup=kb.as_markup(),
        )
        await call.answer()
        return

    kb = InlineKeyboardBuilder()
    for uni in unis:
        kb.row(_btn(f"🎓 {uni.name}", f"uni:{uni.id}"))
    kb.row(_btn("◀️ Back", "nav:by_county"), _home())
    await call.message.edit_text(
        f"📍 <b>{county.name} County</b>\n"
        f"<i>{len(unis)} institution(s)</i>\n\n"
        "Tap to explore groups 👇",
        reply_markup=kb.as_markup(),
    )
    await call.answer()
