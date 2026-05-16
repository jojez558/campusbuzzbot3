"""
CampusBuzz Kenya - Report Handler
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database.connection import AsyncSessionLocal
from database.models import Report, WhatsAppGroup, ReportReason
from keyboards.welcome import report_reason_keyboard, _home
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings

router = Router()


class ReportState(StatesGroup):
    group_id    = State()
    description = State()


@router.message(Command("report"))
@router.callback_query(F.data == "nav:report")
async def start_report(event, state: FSMContext):
    await state.set_state(ReportState.group_id)
    msg = (
        "🛡 <b>Report a Group</b>\n\n"
        "Enter the group ID or name you want to report:\n"
        "<i>(You can find the group ID in its detail page)</i>"
    )
    if isinstance(event, Message):
        await event.answer(msg)
    else:
        await event.message.edit_text(msg)
        await event.answer()


@router.callback_query(F.data.startswith("report:group:"))
async def report_specific(call: CallbackQuery, state: FSMContext):
    group_id = int(call.data.split(":")[2])
    await state.update_data(group_id=group_id)
    await call.message.edit_text(
        "🛡 <b>Report Group</b>\n\nSelect the reason for your report:",
        reply_markup=report_reason_keyboard(group_id),
    )
    await call.answer()


@router.callback_query(F.data.startswith("report:reason:"))
async def receive_reason(call: CallbackQuery, state: FSMContext, bot: Bot):
    parts  = call.data.split(":")
    group_id = int(parts[2])
    reason   = parts[3]

    async with AsyncSessionLocal() as session:
        group = await session.get(WhatsAppGroup, group_id)
        group_name = group.name if group else f"Group #{group_id}"

        report = Report(
            reporter_id=call.from_user.id,
            group_id=group_id,
            reason=reason,
        )
        session.add(report)
        if group:
            group.report_count += 1
        await session.commit()

    await call.message.edit_text(
        f"✅ <b>Report submitted!</b>\n\n"
        f"Thank you for reporting <b>{group_name}</b>.\n"
        f"Our admin @{settings.ADMIN_USERNAME} will review it shortly.\n\n"
        f"🏅 You earned <b>+{settings.XP_REPORT_VALID} XP</b> for helping keep CampusBuzz safe!",
        reply_markup=InlineKeyboardBuilder().row(
            InlineKeyboardButton(text="🏠 Home", callback_data="nav:main_menu")
        ).as_markup(),
    )
    await call.answer("Report submitted!")

    try:
        await bot.send_message(
            settings.ADMIN_ID,
            f"🚨 <b>New Report</b>\n\n"
            f"Group: <b>{group_name}</b> (ID: {group_id})\n"
            f"Reason: <b>{reason}</b>\n"
            f"By: @{call.from_user.username or call.from_user.id}",
        )
    except Exception:
        pass


from aiogram.types import InlineKeyboardButton  # noqa
