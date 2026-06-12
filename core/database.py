from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from core.config import get_settings

# Base class for models
Base = declarative_base()


def get_engine():
    """Get async engine with current settings."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        future=True,
    )


def get_async_session_local():
    """Get async session factory with current settings."""
    settings = get_settings()
    engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# Lazy-initialized engine and session factory
_engine = None
_AsyncSessionLocal = None


def get_db_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


def get_db_session_local():
    """Get or create the async session factory."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = get_async_session_local()
    return _AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    AsyncSessionLocal = get_db_session_local()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()