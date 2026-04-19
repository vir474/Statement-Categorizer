"""
Database engine and session factory.
Supports SQLite (local) and PostgreSQL (server) via DATABASE_URL env var.

SQLite paths are resolved to absolute paths anchored at the backend/ directory,
so the same database is always used regardless of which directory uvicorn is
started from.
"""

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

# backend/ directory — two levels up from this file (app/core/db.py)
_BACKEND_DIR = Path(__file__).parent.parent.parent.resolve()


def _resolve_db_url(url: str) -> str:
    """
    Convert a relative sqlite:///./... URL to an absolute path so the database
    is always found regardless of the working directory uvicorn is started from.
    PostgreSQL URLs are returned unchanged.
    """
    if not url.startswith("sqlite"):
        return url

    # Strip the sqlite:/// prefix to get the file path portion
    prefix = "sqlite:///"
    file_part = url[len(prefix):]

    path = Path(file_part)
    if not path.is_absolute():
        # Anchor relative paths to the backend/ directory
        path = (_BACKEND_DIR / path).resolve()

    return f"sqlite:///{path}"


def _build_engine() -> AsyncEngine:
    url = _resolve_db_url(settings.database_url)

    if url.startswith("sqlite"):
        # Ensure the data directory exists before SQLite tries to create the file
        db_path = Path(url.removeprefix("sqlite:///"))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        async_url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return create_async_engine(
            async_url,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
        "postgres://", "postgresql+asyncpg://", 1
    )
    return create_async_engine(async_url, echo=False, pool_pre_ping=True)


engine = _build_engine()


async def init_db() -> None:
    """Create all tables on startup (dev convenience — prod uses Alembic migrations)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
