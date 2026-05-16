"""
CampusBuzz Kenya - Admin Panel Handler
Restricted to ADMIN_ID. Full management dashboard.
"""

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from datetime import datetime, timedelta

from database.connection import AsyncSessionLocal
from database.models import (
    User, WhatsAppGroup, GroupStatus, Report, BotStat, ActivityLog
)
from keyboards.welcome import admin_panel_keyboard, admin_approve_reject_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings

router = Router()


def admin_only(func_):
    """Decorator: restrict handler to admin user."""
    import functools

    @functools.wraps(func_)
    async def wrapper(event, *args, **kwargs):
        user_id = (
            event.from_user.id
            if isinstance(event, (Message, CallbackQuery))
            else None
        )
        if user_id != settings.ADMIN_ID:
            if isinstance(event, Message):
                await event.answer("🚫 Admin only.")
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫 Admin only.", show_alert=True)
            return
        return await func_(event, *args, **kwargs)

    return wrapper


# ── Admin entry point ────────────────────────────────────────────────────────

@router.message(Command("admin"))
@admin_only
async def cmd_admin(message: Message):
    async with AsyncSessionLocal() as session:
        total_users  = (await session.execute(select(func.count(User.id)))).scalar_one()
        total_groups = (await session.execute(
            select(func.count(WhatsAppGroup.id))
            .where(WhatsAppGroup.status == GroupStatus.APPROVED)
        )).scalar_one()
        pending_count = (await session.execute(
            select(func.count(WhatsAppGroup.id))
            .where(WhatsAppGroup.status == GroupStatus.PENDING)
        )).scalar_one()
        open_reports = (await session.execute(
            select(func.count(Report.id)).where(Report.is_resolved == False)
        )).scalar_one()

    await message.answer(
        "🛡 <b>CampusBuzz Kenya — Admin Panel</b>\n\n"
        f"👥 Total Users: <b>{total_users:,}</b>\n"
        f"📁 Approved Groups: <b>{total_groups:,}</b>\n"
        f"⏳ Pending Review: <b>{pending_count}</b>\n"
        f"🚨 Open Reports: <b>{open_reports}</b>\n\n"
        "Choose an action 👇",
        reply_markup=admin_panel_keyboard(),
    )


# ── Pending groups ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:pending")
@admin_only
async def admin_pending(call: CallbackQuery):
    async with AsyncSessionLocal() as session:
        groups = (await session.execute(
            select(WhatsAppGroup)
            .where(WhatsAppGroup.status == GroupStatus.PENDING)
            .order_by(WhatsAppGroup.created_at.asc())
            .limit(10)
        )).scalars().all()

    if not groups:
        await call.message.edit_text(
            "✅ <b>No pending submissions!</b> All caught up.",
            reply_markup=InlineKeyboardBuilder().row(
                InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel")
            ).as_markup(),
        )
        await call.answer()
        return

    kb = InlineKeyboardBuilder()
    for g in groups:
        kb.row(InlineKeyboardButton(
            text=f"📋 {g.name[:40]}",
            callback_data=f"admin:review:{g.id}"
        ))
    from aiogram.types import InlineKeyboardButton
    kb.row(InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel"))
    await call.message.edit_text(
        f"⏳ <b>Pending Submissions ({len(groups)})</b>\n\nTap to review:",
        reply_markup=kb.as_markup(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:review:"))
@admin_only
async def admin_review_group(call: CallbackQuery):
    group_id = int(call.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        g = await session.get(WhatsAppGroup, group_id)
        if not g:
            await call.answer("Group not found.", show_alert=True)
            return
        submitter_name = f"User #{g.submitter_id}"
        if g.submitter_id:
            user = await session.get(User, g.submitter_id)
            if user:
                submitter_name = f"@{user.username}" if user.username else user.full_name

    await call.message.edit_text(
        f"📋 <b>Review Group #{group_id}</b>\n\n"
        f"📱 <b>Name:</b> {g.name}\n"
        f"🔗 <b>Link:</b> <code>{g.link}</code>\n"
        f"📂 <b>Category:</b> {g.category.value}\n"
        f"📝 <b>Description:</b> {g.description or 'N/A'}\n"
        f"📜 <b>Rules:</b> {g.rules or 'N/A'}\n"
        f"👤 <b>Submitted by:</b> {submitter_name}\n"
        f"📅 <b>Submitted:</b> {g.created_at.strftime('%Y-%m-%d %H:%M')}\n",
        reply_markup=admin_approve_reject_keyboard(group_id),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:approve:"))
@admin_only
async def admin_approve(call: CallbackQuery, bot: Bot):
    group_id = int(call.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        g = await session.get(WhatsAppGroup, group_id)
        if not g:
            await call.answer("Not found.", show_alert=True)
            return
        g.status = GroupStatus.APPROVED
        submitter_id = g.submitter_id
        group_name = g.name
        await session.commit()

    await call.message.edit_text(f"✅ <b>Approved:</b> {group_name}")
    await call.answer("✅ Approved!")

    # Notify submitter
    if submitter_id:
        try:
            await bot.send_message(
                submitter_id,
                f"🎉 <b>Your group was approved!</b>\n\n"
                f"✅ <b>'{group_name}'</b> is now live on CampusBuzz Kenya!\n"
                f"Students can now discover and join it. Thank you! 🙌"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("admin:reject:"))
@admin_only
async def admin_reject(call: CallbackQuery, bot: Bot):
    group_id = int(call.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        g = await session.get(WhatsAppGroup, group_id)
        if not g:
            await call.answer("Not found.", show_alert=True)
            return
        g.status = GroupStatus.REJECTED
        submitter_id = g.submitter_id
        group_name = g.name
        await session.commit()

    await call.message.edit_text(f"❌ <b>Rejected:</b> {group_name}")
    await call.answer("❌ Rejected")

    if submitter_id:
        try:
            await bot.send_message(
                submitter_id,
                f"😔 <b>Submission not approved</b>\n\n"
                f"Your group <b>'{group_name}'</b> was not approved.\n"
                f"Common reasons: spam, invalid link, off-topic.\n\n"
                f"Contact @{settings.ADMIN_USERNAME} for more info."
            )
        except Exception:
            pass


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:analytics")
@admin_only
async def admin_analytics(call: CallbackQuery):
    week_ago = datetime.utcnow() - timedelta(days=7)
    async with AsyncSessionLocal() as session:
        total_users   = (await session.execute(select(func.count(User.id)))).scalar_one()
        new_users_wk  = (await session.execute(
            select(func.count(User.id)).where(User.joined_at >= week_ago)
        )).scalar_one()
        total_groups  = (await session.execute(
            select(func.count(WhatsAppGroup.id))
            .where(WhatsAppGroup.status == GroupStatus.APPROVED)
        )).scalar_one()
        total_views   = (await session.execute(
            select(func.sum(WhatsAppGroup.view_count))
        )).scalar_one() or 0
        total_joins   = (await session.execute(
            select(func.sum(WhatsAppGroup.join_count))
        )).scalar_one() or 0
        top_groups    = (await session.execute(
            select(WhatsAppGroup)
            .where(WhatsAppGroup.status == GroupStatus.APPROVED)
            .order_by(WhatsAppGroup.view_count.desc())
            .limit(5)
        )).scalars().all()

    lines = [
        "📊 <b>CampusBuzz Analytics</b>\n",
        f"👥 Total Users: <b>{total_users:,}</b>",
        f"🆕 New This Week: <b>{new_users_wk:,}</b>",
        f"📁 Approved Groups: <b>{total_groups:,}</b>",
        f"👁 Total Views: <b>{total_views:,}</b>",
        f"🚀 Total Joins: <b>{total_joins:,}</b>",
        "",
        "🔥 <b>Top 5 Groups by Views:</b>",
    ]
    for i, g in enumerate(top_groups, 1):
        lines.append(f"{i}. {g.name} — {g.view_count:,} views")

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="◀️ Back", callback_data="admin:panel"))
    await call.message.edit_text("\n".join(lines), reply_markup=kb.as_markup())
    await call.answer()


# ── Broadcast ─────────────────────────────────────────────────────────────────

class BroadcastState(StatesGroup):
    compose = State()
    confirm = State()


@router.callback_query(F.data == "admin:broadcast")
@admin_only
async def admin_broadcast_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastState.compose)
    await call.message.edit_text(
        "📢 <b>Compose Broadcast</b>\n\n"
        "Type the message you want to send to ALL users.\n"
        "Supports HTML formatting.\n\n"
        "Send /cancel to abort:"
    )
    await call.answer()


@router.message(BroadcastState.compose)
@admin_only
async def admin_broadcast_compose(message: Message, state: FSMContext):
    await state.update_data(broadcast_msg=message.text)
    await state.set_state(BroadcastState.confirm)
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="📢 Send to All", callback_data="admin:broadcast_send"),
        InlineKeyboardButton(text="❌ Cancel",       callback_data="admin:panel"),
    )
    from aiogram.types import InlineKeyboardButton
    await message.answer(
        f"📋 <b>Broadcast Preview:</b>\n\n{message.text}\n\n"
        "Confirm sending to all users?",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data == "admin:broadcast_send")
@admin_only
async def admin_broadcast_send(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg_text = data.get("broadcast_msg", "")
    await state.clear()

    async with AsyncSessionLocal() as session:
        users = (await session.execute(
            select(User.id).where(User.is_banned == False, User.notification_on == True)
        )).scalars().all()

    await call.message.edit_text(f"📢 Broadcasting to {len(users):,} users...")
    await call.answer()

    sent = failed = 0
    for uid in users:
        try:
            await bot.send_message(uid, msg_text)
            sent += 1
        except Exception:
            failed += 1

    await bot.send_message(
        settings.ADMIN_ID,
        f"📊 <b>Broadcast Complete</b>\n✅ Sent: {sent:,}\n❌ Failed: {failed:,}"
    )


# ── Ban user ──────────────────────────────────────────────────────────────────

class BanState(StatesGroup):
    user_id = State()


@router.callback_query(F.data == "admin:ban")
@admin_only
async def admin_ban_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(BanState.user_id)
    await call.message.edit_text(
        "🚫 <b>Ban User</b>\n\nEnter the Telegram User ID to ban:"
    )
    await call.answer()


@router.message(BanState.user_id)
@admin_only
async def admin_ban_execute(message: Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid ID. Enter a numeric Telegram user ID:")
        return

    async with AsyncSessionLocal() as session:
        user = await session.get(User, target_id)
        if not user:
            await message.answer("❌ User not found in database.")
            await state.clear()
            return
        user.is_banned = True
        await session.commit()

    await state.clear()
    await message.answer(f"✅ User <code>{target_id}</code> has been banned.")


@router.callback_query(F.data == "admin:panel")
@admin_only
async def admin_panel_back(call: CallbackQuery):
    await call.message.edit_text(
        "🛡 <b>Admin Panel</b>",
        reply_markup=admin_panel_keyboard()
    )
    await call.answer()


# Missing import fix
from aiogram.types import InlineKeyboardButton  # noqa
