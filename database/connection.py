"""
CampusBuzz Kenya - Database Connection
Async SQLAlchemy + PostgreSQL
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from config import settings
from database.models import Base
from database.seed import seed_universities
import logging

logger = logging.getLogger(__name__)


def _ensure_asyncpg_url(url: str) -> str:
    """
    Normalise the DATABASE_URL so it always uses the asyncpg driver.

    Railway's Postgres service exposes the connection string with the
    psycopg2 dialect (postgresql+psycopg2://) or the bare scheme
    (postgresql://).  create_async_engine() requires asyncpg, so we
    rewrite the scheme here before the engine is created.
    """
    for prefix in ("postgresql+psycopg2://", "postgres+psycopg2://"):
        if url.startswith(prefix):
            converted = "postgresql+asyncpg://" + url[len(prefix):]
            logger.info("DATABASE_URL dialect rewritten: %s → postgresql+asyncpg://", prefix)
            return converted
    # bare postgresql:// or postgres:// (no explicit driver)
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            converted = "postgresql+asyncpg://" + url[len(prefix):]
            logger.info("DATABASE_URL dialect rewritten: %s → postgresql+asyncpg://", prefix)
            return converted
    return url


_database_url = _ensure_asyncpg_url(settings.DATABASE_URL)

engine = create_async_engine(
    _database_url,
    echo=False,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncSession:
    """Dependency: yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables and seed initial data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Tables created / verified")
    
    async with AsyncSessionLocal() as session:
        await seed_universities(session)
    logger.info("✅ Seed data loaded")
