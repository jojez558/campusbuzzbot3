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

engine = create_async_engine(
    settings.DATABASE_URL,
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
