"""
CampusBuzz Kenya — Handler Registry
Import all sub-routers and re-export under clean names.
"""

from handlers._categories import (
    freshers_router   as freshers,
    jobs_router       as jobs,
    materials_router  as materials,
    events_router     as events,
    hostels_router    as hostels,
    marketplace_router as marketplace,
    alumni_router     as alumni,
    settings_router   as settings,
    trending_router   as trending,
)

from handlers import start, menu, universities, search, submit_group, report, profile, favorites

__all__ = [
    "start", "menu", "universities", "search",
    "freshers", "jobs", "materials", "events",
    "hostels", "marketplace", "alumni", "profile",
    "favorites", "submit_group", "report", "settings",
]
