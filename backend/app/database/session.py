"""
Database session factory using SQLAlchemy 2.0 async engine.
Falls back to SQLite with aiosqlite for zero-dependency local development.
"""
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

from sqlalchemy import event

# Convert sync postgres URL to async if needed
_url = settings.DATABASE_URL
if _url.startswith("postgresql://"):
    _url = _url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _url.startswith("sqlite:///"):
    _url = _url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
elif not _url or "supabase" in _url:
    _url = "sqlite+aiosqlite:///./kisansetu.db"

engine = create_async_engine(
    _url,
    echo=settings.DEBUG,
    future=True,
    # SQLite-specific pool config
    **({} if "postgresql" in _url else {"connect_args": {"check_same_thread": False}}),
)

if "sqlite" in _url:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency that provides an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
