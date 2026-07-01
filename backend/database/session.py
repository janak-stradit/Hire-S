"""Async SQLAlchemy session factory used by every API/service boundary."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config.settings import get_settings

settings = get_settings()

# `pool_pre_ping=True` avoids stale PostgreSQL connections during long-running
# local/dev sessions, which is important for validator batches that may process
# hundreds or thousands of candidates.
engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield one request-scoped async DB session for FastAPI dependencies."""
    async with AsyncSessionLocal() as session:
        yield session
