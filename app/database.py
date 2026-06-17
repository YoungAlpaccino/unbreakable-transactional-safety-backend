"""
Async SQLAlchemy session factory (sketch).
"""
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

from app.config import settings

engine = create_async_engine(settings.db_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    from app.models import Submission, OutboxEntry, ReplayLog  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with SessionFactory() as s:
        yield s
