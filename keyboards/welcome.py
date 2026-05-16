"""
CampusBuzz Kenya - Keyboard Layouts
Premium inline keyboard designs for all menus.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings
from typing import Optional


# ── Helpers ──────────────────────────────────────────────────────────────────

def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)

def _url(text: str, url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, url=url)

def _back(target: str = "main_menu") -> InlineKeyboardButton:
    return _btn("◀️ Back", f"nav:{target}")

def _home() -> InlineKeyboardButton:
    return _btn("🏠 Home", "nav:main_menu")


# ── Force Join Keyboard ───────────────────────────────────────────────────────

def force_join_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        _url(f"🚀 Join {settings.REQUIRED_CHANNEL_NAME}", settings.REQUIRED_CHANNEL_LINK)
    )
    kb.row(_btn("✅ I Joined — Check Now", "check_join"))
    kb.row(_url("📞 Contact Admin", f"https://t.me/{settings.ADMIN_USERNAME}"))
    return kb.as_markup()


# ── Welcome / Start Keyboard ──────────────────────────────────────────────────

def welcome_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        _btn("🎓 Browse Universities", "nav:universities"),
        _btn("🔍 Search Groups",       "nav:search"),
    )
    kb.row(
        _btn("⭐ Trending Groups",     "nav:trending"),
        _btn("🆕 Freshers Hub",        "nav:freshers"),
    )
    kb.row(
        _btn("📋 Full Menu",           "nav:main_menu"),
    )
    kb.row(
        _url("📢 CampusBuzz Channel", settings.REQUIRED_CHANNEL_LINK),
        _url("📞 Admin",              f"https://t.me/{settings.ADMIN_USERNAME}"),
    )
    return kb.as_markup()


# ── Main Menu Keyboard ────────────────────────────────────────────────────────

def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    # Row 1
    kb.row(
        _btn("🎓 Universities",         "nav:universities"),
        _btn("🔍 Search Group",         "nav:search"),
    )
    # Row 2
    kb.row(
        _btn("📍 By County",            "nav:by_county"),
        _btn("🆕 Freshers Hub",         "nav:freshers"),
    )
    # Row 3
    kb.row(
        _btn("💼 Jobs & Internships",   "nav:jobs"),
        _btn("📚 Study Materials",      "nav:materials"),
    )
    # Row 4
    kb.row(
        _btn("🏠 Hostels & Housing",    "nav:hostels"),
        _btn("🎉 Campus Events",        "nav:events"),
    )
    # Row 5
    kb.row(
        _btn("🛒 Student Marketplace",  "nav:marketplace"),
        _btn("👨‍🎓 Alumni Network",      "nav:alumni"),
    )
    # Row 6
    kb.row(
        _btn("⭐ Trending Groups",      "nav:trending"),
        _btn("❤️ My Favorites",         "nav:favorites"),
    )
    # Row 7
    kb.row(
        _btn("➕ Submit Group",          "nav:submit_group"),
        _btn("🛡 Report Group",          "nav:report"),
    )
    # Row 8
    kb.row(
        _btn("👤 My Profile",           "nav:profile"),
        _btn("⚙️ Settings",             "nav:settings"),
    )
    # Row 9
    kb.row(
        _url("📞 Contact Admin",        f"https://t.me/{settings.ADMIN_USERNAME}"),
    )
    return kb.as_markup()


# ── Universities Menu ─────────────────────────────────────────────────────────

def universities_category_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        _btn("🏛️ Public Universities",  "uni_type:public"),
    )
    kb.row(
        _btn("🏫 Private Universities", "uni_type:private"),
    )
    kb.row(
        _btn("🔧 TVETs & Colleges",     "uni_type:tvet"),
    )
    kb.row(
        _btn("🔍 Search University",    "nav:search"),
        _btn("📍 By County",            "nav:by_county"),
    )
    kb.row(_back(), _home())
    return kb.as_markup()


def universities_list_keyboard(
    universities: list,
    page: int = 0,
    total: int = 0,
    per_page: int = 8,
    uni_type: str = "public",
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for uni in universities:
        kb.row(_btn(f"🎓 {uni.name}", f"uni:{uni.id}"))

    # Pagination
    nav_btns = []
    if page > 0:
        nav_btns.append(_btn("⬅️ Prev", f"uni_list:{uni_type}:{page-1}"))
    if (page + 1) * per_page < total:
        nav_btns.append(_btn("Next ➡️", f"uni_list:{uni_type}:{page+1}"))
    if nav_btns:
        kb.row(*nav_btns)

    kb.row(_back("universities"), _home())
    return kb.as_markup()


def university_detail_keyboard(uni_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        _btn("🏛️ Official Groups",     f"unicat:{uni_id}:official"),
        _btn("📖 Faculty Groups",       f"unicat:{uni_id}:faculty"),
    )
    kb.row(
        _btn("🏠 Hostel Groups",        f"unicat:{uni_id}:hostel"),
        _btn("🆕 Freshers Groups",      f"unicat:{uni_id}:freshers"),
    )
    kb.row(
        _btn("💼 Jobs & Attachments",   f"unicat:{uni_id}:jobs"),
        _btn("📚 Notes Sharing",        f"unicat:{uni_id}:notes"),
    )
    kb.row(
        _btn("🛒 Buy & Sell",           f"unicat:{uni_id}:marketplace"),
        _btn("👨‍🎓 Alumni",              f"unicat:{uni_id}:alumni"),
    )
    kb.row(_back("universities"), _home())
    return kb.as_markup()


# ── Group Card Keyboard ───────────────────────────────────────────────────────

def group_card_keyboard(
    group_id: int,
    whatsapp_link: str,
    is_favorited: bool = False,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(_url("📲 Join WhatsApp Group", whatsapp_link))
    fav_text = "💔 Remove Favorite" if is_favorited else "❤️ Save to Favorites"
    kb.row(
        _btn(fav_text,             f"fav:toggle:{group_id}"),
        _btn("🛡 Report",           f"report:group:{group_id}"),
    )
    kb.row(
        _btn("🔗 Share Group",      f"share:{group_id}"),
        _btn("ℹ️ More Info",        f"group:info:{group_id}"),
    )
    kb.row(_btn("◀️ Back to List",  "nav:back_list"), _home())
    return kb.as_markup()


# ── Groups List Keyboard ──────────────────────────────────────────────────────

def groups_list_keyboard(
    groups: list,
    page: int = 0,
    total: int = 0,
    per_page: int = 5,
    back_target: str = "main_menu",
    cb_prefix: str = "group_open",
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for g in groups:
        verified = "✅ " if g.is_verified else ""
        trending = "🔥 " if g.is_trending else ""
        kb.row(_btn(f"{trending}{verified}{g.name}", f"{cb_prefix}:{g.id}"))

    nav = []
    if page > 0:
        nav.append(_btn("⬅️ Prev", f"page:{cb_prefix}:{page-1}"))
    if (page + 1) * per_page < total:
        nav.append(_btn("Next ➡️", f"page:{cb_prefix}:{page+1}"))
    if nav:
        kb.row(*nav)

    kb.row(_back(back_target), _home())
    return kb.as_markup()


# ── County List Keyboard ──────────────────────────────────────────────────────

def counties_keyboard(counties: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i in range(0, len(counties), 2):
        row = [_btn(f"📍 {counties[i].name}", f"county:{counties[i].id}")]
        if i + 1 < len(counties):
            row.append(_btn(f"📍 {counties[i+1].name}", f"county:{counties[i+1].id}"))
        kb.row(*row)
    kb.row(_back(), _home())
    return kb.as_markup()


# ── Search Keyboard ───────────────────────────────────────────────────────────

def search_type_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        _btn("🎓 By University", "search:university"),
        _btn("📚 By Course",     "search:course"),
    )
    kb.row(
        _btn("📍 By County",     "search:county"),
        _btn("🆕 By Year",       "search:year"),
    )
    kb.row(_btn("🔤 By Keyword", "search:keyword"))
    kb.row(_back(), _home())
    return kb.as_markup()


# ── Submit Group Keyboard ─────────────────────────────────────────────────────

def submit_group_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(_btn("➕ Submit a New Group", "submit:start"))
    kb.row(_btn("📋 My Submissions",     "submit:my_list"))
    kb.row(_back(), _home())
    return kb.as_markup()


def submit_cancel_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(_btn("❌ Cancel Submission", "submit:cancel"))
    return kb.as_markup()


# ── Profile Keyboard ──────────────────────────────────────────────────────────

def profile_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        _btn("❤️ My Favorites",      "nav:favorites"),
        _btn("📋 My Submissions",     "submit:my_list"),
    )
    kb.row(
        _btn("🏆 My Badges",          "profile:badges"),
        _btn("🎁 Daily Check-in",     "profile:daily"),
    )
    kb.row(
        _btn("🔗 My Referral Link",   "profile:referral"),
        _btn("📊 Leaderboard",        "profile:leaderboard"),
    )
    kb.row(_btn("✏️ Edit Profile",    "profile:edit"))
    kb.row(_back(), _home())
    return kb.as_markup()


# ── Report Keyboard ───────────────────────────────────────────────────────────

def report_reason_keyboard(group_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    reasons = [
        ("🔗 Broken / Expired Link", "broken_link"),
        ("🤡 Fake / Impersonating",  "fake_group"),
        ("📨 Spam Content",          "spam"),
        ("💸 Scam / Fraud",          "scam"),
        ("🔞 Inappropriate Content", "inappropriate"),
        ("🔘 Other",                 "other"),
    ]
    for label, code in reasons:
        kb.row(_btn(label, f"report:reason:{group_id}:{code}"))
    kb.row(_btn("❌ Cancel", "nav:main_menu"))
    return kb.as_markup()


# ── Settings Keyboard ─────────────────────────────────────────────────────────

def settings_keyboard(notif_on: bool = True, lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    notif_text = "🔔 Notifications: ON  ✅" if notif_on else "🔕 Notifications: OFF ❌"
    kb.row(_btn(notif_text, "settings:toggle_notif"))
    lang_text = "🌐 Language: English 🇬🇧" if lang == "en" else "🌐 Language: Kiswahili 🇰🇪"
    kb.row(_btn(lang_text, "settings:toggle_lang"))
    kb.row(
        _btn("🗑 Clear History",        "settings:clear_history"),
        _btn("📤 Export My Data",       "settings:export"),
    )
    kb.row(_back(), _home())
    return kb.as_markup()


# ── Admin Panel Keyboard ──────────────────────────────────────────────────────

def admin_panel_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        _btn("📋 Pending Groups",       "admin:pending"),
        _btn("📊 Analytics",            "admin:analytics"),
    )
    kb.row(
        _btn("📢 Broadcast",            "admin:broadcast"),
        _btn("🚫 Ban User",             "admin:ban"),
    )
    kb.row(
        _btn("🔥 Set Trending",         "admin:trending"),
        _btn("✅ Verify Group",          "admin:verify"),
    )
    kb.row(
        _btn("🛡 View Reports",         "admin:reports"),
        _btn("🗑 Delete Group",          "admin:delete"),
    )
    kb.row(
        _btn("📅 Schedule Broadcast",   "admin:schedule"),
        _btn("📈 User Stats",           "admin:stats"),
    )
    return kb.as_markup()


def admin_approve_reject_keyboard(group_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        _btn("✅ Approve",   f"admin:approve:{group_id}"),
        _btn("❌ Reject",    f"admin:reject:{group_id}"),
    )
    kb.row(
        _btn("✏️ Edit",     f"admin:edit:{group_id}"),
        _btn("👁 Preview",  f"admin:preview:{group_id}"),
    )
    kb.row(_btn("◀️ Back to Pending", "admin:pending"))
    return kb.as_markup()
