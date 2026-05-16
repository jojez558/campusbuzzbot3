"""
CampusBuzz Kenya - Database Models
Full schema for all entities
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class UniversityType(str, enum.Enum):
    PUBLIC      = "public"
    PRIVATE     = "private"
    TVET        = "tvet"

class GroupCategory(str, enum.Enum):
    OFFICIAL        = "official"
    FACULTY         = "faculty"
    DEPARTMENT      = "department"
    FRESHERS        = "freshers"
    HOSTEL          = "hostel"
    MARKETPLACE     = "marketplace"
    JOBS            = "jobs"
    NOTES           = "notes"
    ALUMNI          = "alumni"
    EVENTS          = "events"
    GENERAL         = "general"

class GroupStatus(str, enum.Enum):
    PENDING     = "pending"
    APPROVED    = "approved"
    REJECTED    = "rejected"
    SUSPENDED   = "suspended"
    EXPIRED     = "expired"

class UserBadge(str, enum.Enum):
    NEWCOMER        = "newcomer"
    CONTRIBUTOR     = "contributor"
    VERIFIED        = "verified"
    CAMPUS_LEGEND   = "campus_legend"
    AMBASSADOR      = "ambassador"
    ADMIN           = "admin"

class ReportReason(str, enum.Enum):
    FAKE_GROUP      = "fake_group"
    SPAM            = "spam"
    SCAM            = "scam"
    BROKEN_LINK     = "broken_link"
    INAPPROPRIATE   = "inappropriate"
    OTHER           = "other"


# ── Models ────────────────────────────────────────────────────────────────────

class County(Base):
    __tablename__ = "counties"

    id:   Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    universities: Mapped[List["University"]] = relationship(back_populates="county")


class University(Base):
    __tablename__ = "universities"

    id:          Mapped[int]            = mapped_column(Integer, primary_key=True)
    name:        Mapped[str]            = mapped_column(String(200), unique=True, nullable=False)
    short_name:  Mapped[Optional[str]]  = mapped_column(String(50))
    type:        Mapped[UniversityType] = mapped_column(Enum(UniversityType), default=UniversityType.PUBLIC)
    county_id:   Mapped[Optional[int]]  = mapped_column(ForeignKey("counties.id"))
    website:     Mapped[Optional[str]]  = mapped_column(String(300))
    description: Mapped[Optional[str]]  = mapped_column(Text)
    logo_url:    Mapped[Optional[str]]  = mapped_column(String(500))
    is_active:   Mapped[bool]           = mapped_column(Boolean, default=True)
    created_at:  Mapped[datetime]       = mapped_column(DateTime, server_default=func.now())

    county:   Mapped[Optional["County"]]   = relationship(back_populates="universities")
    groups:   Mapped[List["WhatsAppGroup"]]= relationship(back_populates="university")
    faculties:Mapped[List["Faculty"]]      = relationship(back_populates="university")


class Faculty(Base):
    __tablename__ = "faculties"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True)
    university_id: Mapped[int]           = mapped_column(ForeignKey("universities.id"))
    name:          Mapped[str]           = mapped_column(String(200), nullable=False)
    short_name:    Mapped[Optional[str]] = mapped_column(String(50))

    university:   Mapped["University"]          = relationship(back_populates="faculties")
    departments:  Mapped[List["Department"]]    = relationship(back_populates="faculty")
    groups:       Mapped[List["WhatsAppGroup"]] = relationship(back_populates="faculty")


class Department(Base):
    __tablename__ = "departments"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    faculty_id: Mapped[int]           = mapped_column(ForeignKey("faculties.id"))
    name:       Mapped[str]           = mapped_column(String(200), nullable=False)

    faculty: Mapped["Faculty"]               = relationship(back_populates="departments")
    groups:  Mapped[List["WhatsAppGroup"]]   = relationship(back_populates="department")


class User(Base):
    __tablename__ = "users"

    id:              Mapped[int]            = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    username:        Mapped[Optional[str]]  = mapped_column(String(100))
    full_name:       Mapped[str]            = mapped_column(String(200), nullable=False)
    university_id:   Mapped[Optional[int]]  = mapped_column(ForeignKey("universities.id"))
    course:          Mapped[Optional[str]]  = mapped_column(String(200))
    year_of_study:   Mapped[Optional[int]]  = mapped_column(Integer)
    xp_points:       Mapped[int]            = mapped_column(Integer, default=0)
    badge:           Mapped[UserBadge]      = mapped_column(Enum(UserBadge), default=UserBadge.NEWCOMER)
    referral_code:   Mapped[str]            = mapped_column(String(20), unique=True, nullable=False)
    referred_by:     Mapped[Optional[int]]  = mapped_column(BigInteger, ForeignKey("users.id"))
    referral_count:  Mapped[int]            = mapped_column(Integer, default=0)
    spam_strikes:    Mapped[int]            = mapped_column(Integer, default=0)
    is_banned:       Mapped[bool]           = mapped_column(Boolean, default=False)
    is_admin:        Mapped[bool]           = mapped_column(Boolean, default=False)
    language:        Mapped[str]            = mapped_column(String(10), default="en")
    last_daily:      Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_active:     Mapped[datetime]       = mapped_column(DateTime, server_default=func.now())
    joined_at:       Mapped[datetime]       = mapped_column(DateTime, server_default=func.now())
    notification_on: Mapped[bool]           = mapped_column(Boolean, default=True)

    university:      Mapped[Optional["University"]]     = relationship()
    favorites:       Mapped[List["Favorite"]]           = relationship(back_populates="user")
    submissions:     Mapped[List["WhatsAppGroup"]]      = relationship(back_populates="submitter")
    reports:         Mapped[List["Report"]]             = relationship(back_populates="reporter")
    activity_log:    Mapped[List["ActivityLog"]]        = relationship(back_populates="user")


class WhatsAppGroup(Base):
    __tablename__ = "whatsapp_groups"

    id:             Mapped[int]             = mapped_column(Integer, primary_key=True)
    name:           Mapped[str]             = mapped_column(String(300), nullable=False)
    description:    Mapped[Optional[str]]   = mapped_column(Text)
    link:           Mapped[str]             = mapped_column(String(500), nullable=False)
    university_id:  Mapped[Optional[int]]   = mapped_column(ForeignKey("universities.id"))
    faculty_id:     Mapped[Optional[int]]   = mapped_column(ForeignKey("faculties.id"))
    department_id:  Mapped[Optional[int]]   = mapped_column(ForeignKey("departments.id"))
    category:       Mapped[GroupCategory]   = mapped_column(Enum(GroupCategory), default=GroupCategory.GENERAL)
    status:         Mapped[GroupStatus]     = mapped_column(Enum(GroupStatus), default=GroupStatus.PENDING)
    submitter_id:   Mapped[Optional[int]]   = mapped_column(BigInteger, ForeignKey("users.id"))
    is_verified:    Mapped[bool]            = mapped_column(Boolean, default=False)
    is_sponsored:   Mapped[bool]            = mapped_column(Boolean, default=False)
    is_trending:    Mapped[bool]            = mapped_column(Boolean, default=False)
    member_count:   Mapped[Optional[int]]   = mapped_column(Integer)
    rules:          Mapped[Optional[str]]   = mapped_column(Text)
    tags:           Mapped[Optional[str]]   = mapped_column(String(500))       # comma-separated
    view_count:     Mapped[int]             = mapped_column(Integer, default=0)
    join_count:     Mapped[int]             = mapped_column(Integer, default=0)
    report_count:   Mapped[int]             = mapped_column(Integer, default=0)
    last_checked:   Mapped[Optional[datetime]] = mapped_column(DateTime)       # link health
    is_link_active: Mapped[bool]            = mapped_column(Boolean, default=True)
    expires_at:     Mapped[Optional[datetime]] = mapped_column(DateTime)       # auto-expiring
    created_at:     Mapped[datetime]        = mapped_column(DateTime, server_default=func.now())
    updated_at:     Mapped[datetime]        = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    university:     Mapped[Optional["University"]]  = relationship(back_populates="groups")
    faculty:        Mapped[Optional["Faculty"]]     = relationship(back_populates="groups")
    department:     Mapped[Optional["Department"]]  = relationship(back_populates="groups")
    submitter:      Mapped[Optional["User"]]        = relationship(back_populates="submissions")
    favorites:      Mapped[List["Favorite"]]        = relationship(back_populates="group")
    reports:        Mapped[List["Report"]]          = relationship(back_populates="group")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "group_id"),)

    id:         Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    group_id:   Mapped[int] = mapped_column(Integer, ForeignKey("whatsapp_groups.id"))
    saved_at:   Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user:  Mapped["User"]           = relationship(back_populates="favorites")
    group: Mapped["WhatsAppGroup"]  = relationship(back_populates="favorites")


class Report(Base):
    __tablename__ = "reports"

    id:          Mapped[int]          = mapped_column(Integer, primary_key=True)
    reporter_id: Mapped[int]          = mapped_column(BigInteger, ForeignKey("users.id"))
    group_id:    Mapped[int]          = mapped_column(Integer, ForeignKey("whatsapp_groups.id"))
    reason:      Mapped[ReportReason] = mapped_column(Enum(ReportReason))
    description: Mapped[Optional[str]]= mapped_column(Text)
    is_resolved: Mapped[bool]         = mapped_column(Boolean, default=False)
    created_at:  Mapped[datetime]     = mapped_column(DateTime, server_default=func.now())

    reporter: Mapped["User"]          = relationship(back_populates="reports")
    group:    Mapped["WhatsAppGroup"] = relationship(back_populates="reports")


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    message:     Mapped[str]           = mapped_column(Text, nullable=False)
    sent_by:     Mapped[int]           = mapped_column(BigInteger, ForeignKey("users.id"))
    target:      Mapped[str]           = mapped_column(String(50), default="all")  # all/uni_id/county
    sent_count:  Mapped[int]           = mapped_column(Integer, default=0)
    fail_count:  Mapped[int]           = mapped_column(Integer, default=0)
    scheduled_at:Mapped[Optional[datetime]] = mapped_column(DateTime)
    sent_at:     Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at:  Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int]           = mapped_column(BigInteger, ForeignKey("users.id"))
    action:     Mapped[str]           = mapped_column(String(100), nullable=False)
    details:    Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="activity_log")


class BotStat(Base):
    """Daily snapshot for analytics."""
    __tablename__ = "bot_stats"

    id:              Mapped[int]      = mapped_column(Integer, primary_key=True)
    date:            Mapped[datetime] = mapped_column(DateTime, unique=True, nullable=False)
    total_users:     Mapped[int]      = mapped_column(Integer, default=0)
    new_users:       Mapped[int]      = mapped_column(Integer, default=0)
    active_users:    Mapped[int]      = mapped_column(Integer, default=0)
    total_groups:    Mapped[int]      = mapped_column(Integer, default=0)
    new_groups:      Mapped[int]      = mapped_column(Integer, default=0)
    total_clicks:    Mapped[int]      = mapped_column(Integer, default=0)
    total_messages:  Mapped[int]      = mapped_column(Integer, default=0)
