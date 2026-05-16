"""
CampusBuzz Kenya - Menu & Navigation Handler
Handles /menu command and all nav: callbacks.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.welcome import main_menu_keyboard

router = Router()

MENU_TEXT = (
    "📋 <b>CampusBuzz Kenya — Main Menu</b>\n\n"
    "🇰🇪 <i>Your campus, connected. Choose a category below:</i>\n\n"
    "🎓 Universities &nbsp;·&nbsp; 🔍 Search &nbsp;·&nbsp; ⭐ Trending\n"
    "💼 Jobs &nbsp;·&nbsp; 📚 Notes &nbsp;·&nbsp; 🏠 Hostels &nbsp;·&nbsp; 🎉 Events\n"
    "🛒 Marketplace &nbsp;·&nbsp; 👨‍🎓 Alumni &nbsp;·&nbsp; ❤️ Favourites"
)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(MENU_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "nav:main_menu")
async def nav_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(MENU_TEXT, reply_markup=main_menu_keyboard())
    await call.answer()


# Generic back navigation — specific screens register their own
@router.callback_query(F.data.startswith("nav:back"))
async def nav_back(call: CallbackQuery):
    """Fallback: go home."""
    await call.message.edit_text(MENU_TEXT, reply_markup=main_menu_keyboard())
    await call.answer()
