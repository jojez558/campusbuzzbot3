"""
CampusBuzz Kenya - Search Handler
Smart multi-step search with FSM.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, or_, func

from database.connection import AsyncSessionLocal
from database.models import University, WhatsAppGroup, GroupStatus
from keyboards.welcome import search_type_keyboard, groups_list_keyboard, _btn, _home, _back
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings

router = Router()


class SearchStates(StatesGroup):
    waiting_for_query = State()
    search_type       = State()


@router.message(Command("search"))
@router.callback_query(F.data == "nav:search")
async def start_search(event, state: FSMContext):
    await state.clear()
    msg = (
        "🔍 <b>Search WhatsApp Groups</b>\n\n"
        "Choose how you'd like to search:"
    )
    kb = search_type_keyboard()

    if isinstance(event, Message):
        await event.answer(msg, reply_markup=kb)
    else:
        await event.message.edit_text(msg, reply_markup=kb)
        await event.answer()


# ── Search by keyword ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "search:keyword")
async def search_keyword(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_query)
    await state.update_data(search_type="keyword")
    await call.message.edit_text(
        "🔤 <b>Keyword Search</b>\n\n"
        "Type your search term (e.g. <i>'nursing'</i>, <i>'cs students'</i>, <i>'nairobi hostel'</i>):"
    )
    await call.answer()


@router.callback_query(F.data == "search:university")
async def search_university(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_query)
    await state.update_data(search_type="university")
    await call.message.edit_text(
        "🎓 <b>Search by University</b>\n\n"
        "Type the university name (e.g. <i>'Nairobi'</i>, <i>'JKUAT'</i>, <i>'Strathmore'</i>):"
    )
    await call.answer()


@router.callback_query(F.data == "search:course")
async def search_course(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_query)
    await state.update_data(search_type="course")
    await call.message.edit_text(
        "📚 <b>Search by Course</b>\n\n"
        "Type the course or department name (e.g. <i>'Computer Science'</i>, <i>'Engineering'</i>, <i>'Nursing'</i>):"
    )
    await call.answer()


@router.callback_query(F.data == "search:year")
async def search_year(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_query)
    await state.update_data(search_type="year")
    await call.message.edit_text(
        "🆕 <b>Search by Year / Freshers</b>\n\n"
        "Type your year of study or 'freshers' (e.g. <i>'2024 freshers'</i>, <i>'1st year'</i>):"
    )
    await call.answer()


# ── Process search query ──────────────────────────────────────────────────────

@router.message(SearchStates.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext):
    data = await state.get_data()
    search_type = data.get("search_type", "keyword")
    query = message.text.strip()

    if len(query) < 2:
        await message.answer("❌ Search term too short. Please enter at least 2 characters.")
        return

    await state.clear()
    await _execute_search(message, query, search_type)


async def _execute_search(message: Message, query: str, search_type: str):
    per_page = settings.GROUPS_PER_PAGE

    async with AsyncSessionLocal() as session:
        if search_type == "university":
            # Find matching universities first
            uni_q = select(University).where(
                University.name.ilike(f"%{query}%"),
                University.is_active == True,
            ).limit(5)
            unis = (await session.execute(uni_q)).scalars().all()

            if unis:
                kb = InlineKeyboardBuilder()
                for uni in unis:
                    kb.row(_btn(f"🎓 {uni.name}", f"uni:{uni.id}"))
                kb.row(_back("search"), _home())
                await message.answer(
                    f"🔍 Found <b>{len(unis)}</b> universities matching <i>'{query}'</i>:\n\n"
                    "Tap to explore groups 👇",
                    reply_markup=kb.as_markup(),
                )
                return
            else:
                await message.answer(f"😔 No universities found matching <i>'{query}'</i>.\nTry a shorter term.")
                return

        # For keyword/course/year — search groups directly
        group_q = select(WhatsAppGroup).where(
            WhatsAppGroup.status == GroupStatus.APPROVED,
            WhatsAppGroup.is_link_active == True,
            or_(
                WhatsAppGroup.name.ilike(f"%{query}%"),
                WhatsAppGroup.description.ilike(f"%{query}%"),
                WhatsAppGroup.tags.ilike(f"%{query}%"),
            )
        ).order_by(
            WhatsAppGroup.is_verified.desc(),
            WhatsAppGroup.join_count.desc(),
        )

        total = (await session.execute(
            select(func.count()).select_from(group_q.subquery())
        )).scalar_one()

        groups = (await session.execute(
            group_q.limit(per_page)
        )).scalars().all()

    if not groups:
        kb = InlineKeyboardBuilder()
        kb.row(_btn("🔍 Try Again", "nav:search"))
        kb.row(_btn("➕ Submit Group", "nav:submit_group"), _home())
        await message.answer(
            f"😔 No groups found for <i>'{query}'</i>\n\n"
            "Can't find what you're looking for? Submit your group!",
            reply_markup=kb.as_markup(),
        )
        return

    kb = groups_list_keyboard(
        groups, 0, total, per_page,
        back_target="search",
        cb_prefix="group_open",
    )
    await message.answer(
        f"🔍 <b>Search results for:</b> <i>'{query}'</i>\n"
        f"📊 Found <b>{total}</b> group(s) — showing first {min(total, per_page)}\n\n"
        "Tap a group to view & join 👇",
        reply_markup=kb,
    )
