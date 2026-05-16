"""
CampusBuzz Kenya - Submit Group Handler
Multi-step FSM for submitting a WhatsApp group for review.
"""

import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database.connection import AsyncSessionLocal
from database.models import WhatsAppGroup, University, GroupCategory, GroupStatus, User
from keyboards.welcome import submit_cancel_keyboard, _btn, _home
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings

router = Router()

WHATSAPP_PATTERN = re.compile(
    r"https://chat\.whatsapp\.com/[A-Za-z0-9]{20,}"
)


class SubmitStates(StatesGroup):
    link        = State()
    group_name  = State()
    university  = State()
    category    = State()
    description = State()
    rules       = State()
    confirm     = State()


CATEGORY_OPTIONS = [
    ("🏛️ Official / General",   GroupCategory.OFFICIAL),
    ("📖 Faculty / School",      GroupCategory.FACULTY),
    ("🏠 Hostel / Housing",      GroupCategory.HOSTEL),
    ("🆕 Freshers",              GroupCategory.FRESHERS),
    ("💼 Jobs & Attachments",    GroupCategory.JOBS),
    ("📚 Notes & PDFs",          GroupCategory.NOTES),
    ("🛒 Buy & Sell",            GroupCategory.MARKETPLACE),
    ("🎉 Events & Socials",      GroupCategory.EVENTS),
    ("👨‍🎓 Alumni",               GroupCategory.ALUMNI),
    ("🔘 General",               GroupCategory.GENERAL),
]


@router.message(Command("submitgroup"))
@router.callback_query(F.data == "nav:submit_group")
async def start_submit(event, state: FSMContext):
    await state.clear()
    msg = (
        "➕ <b>Submit a WhatsApp Group</b>\n\n"
        "Help grow the CampusBuzz directory!\n"
        "Your submission will be reviewed by admin before going live.\n\n"
        "📌 <b>Requirements:</b>\n"
        "• Must be a valid WhatsApp invite link\n"
        "• Must be campus-related\n"
        "• No spam or adult content groups\n\n"
        "Ready? Let's go! 🚀\n\n"
        "<b>Step 1/6:</b> Paste the WhatsApp group invite link:"
    )
    kb = submit_cancel_keyboard()

    if isinstance(event, Message):
        await event.answer(msg, reply_markup=kb)
    else:
        await event.message.edit_text(msg, reply_markup=kb)
        await event.answer()

    await state.set_state(SubmitStates.link)


@router.message(SubmitStates.link)
async def receive_link(message: Message, state: FSMContext):
    link = message.text.strip()
    if not WHATSAPP_PATTERN.match(link):
        await message.answer(
            "❌ Invalid link!\n\n"
            "Must be a WhatsApp invite link like:\n"
            "<code>https://chat.whatsapp.com/XXXXXXXX</code>\n\n"
            "Try again:",
            reply_markup=submit_cancel_keyboard(),
        )
        return

    await state.update_data(link=link)
    await state.set_state(SubmitStates.group_name)
    await message.answer(
        "✅ Link looks good!\n\n"
        "<b>Step 2/6:</b> What is the name of this WhatsApp group?\n"
        "<i>(e.g. 'JKUAT CS 2024 Freshers')</i>",
        reply_markup=submit_cancel_keyboard(),
    )


@router.message(SubmitStates.group_name)
async def receive_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 3 or len(name) > 200:
        await message.answer("❌ Group name must be 3–200 characters. Try again:")
        return

    await state.update_data(group_name=name)
    await state.set_state(SubmitStates.university)
    await message.answer(
        f"✅ Name saved: <b>{name}</b>\n\n"
        "<b>Step 3/6:</b> Which university or college is this group for?\n"
        "<i>(Type the university name, e.g. 'JKUAT', 'UoN', 'Strathmore')</i>",
        reply_markup=submit_cancel_keyboard(),
    )


@router.message(SubmitStates.university)
async def receive_university(message: Message, state: FSMContext):
    query = message.text.strip()

    async with AsyncSessionLocal() as session:
        unis = (await session.execute(
            select(University)
            .where(University.name.ilike(f"%{query}%"), University.is_active == True)
            .limit(5)
        )).scalars().all()

    if not unis:
        await message.answer(
            f"😔 No university found for <i>'{query}'</i>.\n\n"
            "Try a shorter name or check spelling:",
            reply_markup=submit_cancel_keyboard(),
        )
        return

    if len(unis) == 1:
        await state.update_data(university_id=unis[0].id, university_name=unis[0].name)
        await _ask_category(message, state)
        return

    # Multiple matches — let user pick
    kb = InlineKeyboardBuilder()
    for uni in unis:
        kb.row(_btn(f"🎓 {uni.name}", f"submit_uni:{uni.id}:{uni.name}"))
    kb.row(_btn("❌ Cancel", "submit:cancel"))
    await message.answer(
        f"🔍 Found {len(unis)} matches. Which one?",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data.startswith("submit_uni:"))
async def pick_university(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":", 2)
    uni_id, uni_name = int(parts[1]), parts[2]
    await state.update_data(university_id=uni_id, university_name=uni_name)
    await call.answer()
    await _ask_category(call.message, state)


async def _ask_category(message: Message, state: FSMContext):
    await state.set_state(SubmitStates.category)
    kb = InlineKeyboardBuilder()
    for label, cat in CATEGORY_OPTIONS:
        kb.row(_btn(label, f"submit_cat:{cat.value}"))
    kb.row(_btn("❌ Cancel", "submit:cancel"))
    await message.answer(
        "<b>Step 4/6:</b> What category best describes this group?",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data.startswith("submit_cat:"))
async def receive_category(call: CallbackQuery, state: FSMContext):
    cat = call.data.split(":")[1]
    await state.update_data(category=cat)
    await state.set_state(SubmitStates.description)
    await call.message.edit_text(
        f"✅ Category saved!\n\n"
        "<b>Step 5/6:</b> Give a short description of this group:\n"
        "<i>(What's it about? Who should join? Max 300 chars)</i>",
        reply_markup=submit_cancel_keyboard(),
    )
    await call.answer()


@router.message(SubmitStates.description)
async def receive_description(message: Message, state: FSMContext):
    desc = message.text.strip()[:300]
    await state.update_data(description=desc)
    await state.set_state(SubmitStates.rules)
    await message.answer(
        "✅ Description saved!\n\n"
        "<b>Step 6/6 (Optional):</b> Any group rules to display?\n"
        "Type the rules or send <b>'skip'</b> to continue:",
        reply_markup=submit_cancel_keyboard(),
    )


@router.message(SubmitStates.rules)
async def receive_rules(message: Message, state: FSMContext):
    rules = None if message.text.lower().strip() == "skip" else message.text.strip()[:500]
    await state.update_data(rules=rules)
    await _show_confirmation(message, state)


async def _show_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(SubmitStates.confirm)

    text = (
        "📋 <b>Review Your Submission</b>\n\n"
        f"📱 <b>Group Name:</b> {data['group_name']}\n"
        f"🔗 <b>Link:</b> <code>{data['link']}</code>\n"
        f"🎓 <b>University:</b> {data['university_name']}\n"
        f"📂 <b>Category:</b> {data['category'].title()}\n"
        f"📝 <b>Description:</b> {data.get('description', 'N/A')}\n"
        f"📜 <b>Rules:</b> {data.get('rules') or 'None'}\n\n"
        "<i>Your submission will be reviewed by @DevMwaura before going live.</i>\n\n"
        "Confirm submission?"
    )
    kb = InlineKeyboardBuilder()
    kb.row(
        _btn("✅ Submit for Review", "submit:confirm"),
        _btn("❌ Cancel",            "submit:cancel"),
    )
    await message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "submit:confirm")
async def confirm_submission(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        group = WhatsAppGroup(
            name=data["group_name"],
            link=data["link"],
            university_id=data.get("university_id"),
            category=data["category"],
            description=data.get("description"),
            rules=data.get("rules"),
            status=GroupStatus.PENDING,
            submitter_id=call.from_user.id,
        )
        session.add(group)

        # Award XP
        user = await session.get(User, call.from_user.id)
        if user:
            user.xp_points += settings.XP_SUBMIT_GROUP

        await session.commit()
        group_id = group.id

    await call.message.edit_text(
        "🎉 <b>Submission received!</b>\n\n"
        f"✅ <b>'{data['group_name']}'</b> has been submitted for review.\n\n"
        f"🏅 You earned <b>+{settings.XP_SUBMIT_GROUP} XP</b>!\n\n"
        "The admin will review and approve your group shortly.\n"
        "You'll be notified once it goes live. 🚀",
        reply_markup=InlineKeyboardBuilder().row(_home()).as_markup(),
    )
    await call.answer("✅ Submitted!")

    # Notify admin
    try:
        await bot.send_message(
            settings.ADMIN_ID,
            f"📥 <b>New Group Submission</b>\n\n"
            f"👤 From: @{call.from_user.username or call.from_user.id}\n"
            f"📱 Group: <b>{data['group_name']}</b>\n"
            f"🎓 University ID: {data.get('university_id')}\n"
            f"📂 Category: {data['category']}\n"
            f"🔗 Link: <code>{data['link']}</code>\n\n"
            f"Group ID: #{group_id}",
            reply_markup=_admin_group_review_kb(group_id),
        )
    except Exception:
        pass


def _admin_group_review_kb(group_id: int):
    kb = InlineKeyboardBuilder()
    kb.row(
        _btn("✅ Approve", f"admin:approve:{group_id}"),
        _btn("❌ Reject",  f"admin:reject:{group_id}"),
    )
    return kb.as_markup()


@router.callback_query(F.data == "submit:cancel")
async def cancel_submit(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "❌ Submission cancelled.\n\nYou can restart anytime with /submitgroup",
        reply_markup=InlineKeyboardBuilder().row(_home()).as_markup(),
    )
    await call.answer()


@router.callback_query(F.data == "submit:my_list")
async def my_submissions(call: CallbackQuery):
    async with AsyncSessionLocal() as session:
        groups = (await session.execute(
            select(WhatsAppGroup)
            .where(WhatsAppGroup.submitter_id == call.from_user.id)
            .order_by(WhatsAppGroup.created_at.desc())
            .limit(10)
        )).scalars().all()

    if not groups:
        await call.message.edit_text(
            "📋 <b>My Submissions</b>\n\n"
            "You haven't submitted any groups yet.\n\n"
            "Tap /submitgroup to add your first group!",
            reply_markup=InlineKeyboardBuilder().row(_home()).as_markup(),
        )
        await call.answer()
        return

    STATUS_EMOJI = {
        GroupStatus.PENDING:   "⏳",
        GroupStatus.APPROVED:  "✅",
        GroupStatus.REJECTED:  "❌",
        GroupStatus.SUSPENDED: "🚫",
    }

    lines = ["📋 <b>My Submissions</b>\n"]
    for g in groups:
        em = STATUS_EMOJI.get(g.status, "❓")
        lines.append(f"{em} <b>{g.name}</b> — {g.status.value.title()}")

    kb = InlineKeyboardBuilder()
    kb.row(_btn("➕ Submit New Group", "submit:start"), _home())
    await call.message.edit_text("\n".join(lines), reply_markup=kb.as_markup())
    await call.answer()
