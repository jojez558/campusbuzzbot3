"""
CampusBuzz Kenya - Favorites Handler
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select

from database.connection import AsyncSessionLocal
from database.models import Favorite, WhatsAppGroup
from keyboards.welcome import _btn, _home
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


@router.message(Command("favorites"))
@router.callback_query(F.data == "nav:favorites")
async def show_favorites(event):
    user_id = event.from_user.id

    async with AsyncSessionLocal() as session:
        favs = (await session.execute(
            select(WhatsAppGroup)
            .join(Favorite, Favorite.group_id == WhatsAppGroup.id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.saved_at.desc())
            .limit(20)
        )).scalars().all()

    if not favs:
        msg = (
            "❤️ <b>My Favorites</b>\n\n"
            "You haven't saved any groups yet!\n\n"
            "Browse groups and tap ❤️ to save them here."
        )
        kb = InlineKeyboardBuilder()
        kb.row(_btn("🎓 Browse Universities", "nav:universities"), _home())
        if isinstance(event, Message):
            await event.answer(msg, reply_markup=kb.as_markup())
        else:
            await event.message.edit_text(msg, reply_markup=kb.as_markup())
            await event.answer()
        return

    kb = InlineKeyboardBuilder()
    for g in favs:
        verified = "✅ " if g.is_verified else ""
        kb.row(_btn(f"{verified}{g.name}", f"group_open:{g.id}"))
    kb.row(_home())

    msg = f"❤️ <b>My Favorites ({len(favs)})</b>\n\nTap any group to view or join:"
    if isinstance(event, Message):
        await event.answer(msg, reply_markup=kb.as_markup())
    else:
        await event.message.edit_text(msg, reply_markup=kb.as_markup())
        await event.answer()


@router.callback_query(F.data.startswith("fav:toggle:"))
async def toggle_favorite(call: CallbackQuery):
    group_id = int(call.data.split(":")[2])
    user_id  = call.from_user.id

    async with AsyncSessionLocal() as session:
        existing = (await session.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.group_id == group_id,
            )
        )).scalars().first()

        if existing:
            await session.delete(existing)
            msg = "💔 Removed from favorites"
        else:
            session.add(Favorite(user_id=user_id, group_id=group_id))
            msg = "❤️ Saved to favorites!"
        await session.commit()

    await call.answer(msg, show_alert=False)
