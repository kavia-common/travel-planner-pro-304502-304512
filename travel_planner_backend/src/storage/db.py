import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.storage.models import Base

DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(__file__), "travel_planner.sqlite3")


def _get_db_url() -> str:
    """
    Compute the database URL.

    We intentionally keep this backend self-contained: by default it uses a SQLite file
    within the repository container. If you want to override, set BACKEND_DATABASE_URL
    (e.g., sqlite+aiosqlite:////absolute/path.db).

    NOTE: The container env list provided did not include a DB URL; this keeps the app working
    without any additional environment variables.
    """
    db_url = os.getenv("BACKEND_DATABASE_URL")
    if db_url:
        return db_url

    # aiosqlite requires 4 slashes for an absolute path; we use absolute for reliability.
    abs_path = os.path.abspath(DEFAULT_SQLITE_PATH)
    return f"sqlite+aiosqlite:///{abs_path}"


_ENGINE: AsyncEngine | None = None
_SessionMaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return a singleton async SQLAlchemy engine."""
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_async_engine(_get_db_url(), echo=False, future=True)
    return _ENGINE


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return a singleton async SQLAlchemy sessionmaker."""
    global _SessionMaker
    if _SessionMaker is None:
        _SessionMaker = async_sessionmaker(bind=get_engine(), expire_on_commit=False, class_=AsyncSession)
    return _SessionMaker


async def init_db() -> None:
    """Create all tables if they do not exist."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an AsyncSession."""
    session_maker = get_sessionmaker()
    async with session_maker() as session:
        yield session
