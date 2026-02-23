"""Async SQLite database connection and initialization."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from src.config import get_settings

logger = logging.getLogger(__name__)

_MIGRATIONS_DIR: Path = Path(__file__).resolve().parent.parent / "migrations"


def _get_db_path() -> str:
    return get_settings().database_url


@asynccontextmanager
async def get_db_connection() -> AsyncIterator[aiosqlite.Connection]:
    """Yield an async SQLite connection with foreign keys enabled."""
    db = await aiosqlite.connect(_get_db_path())
    try:
        await db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = aiosqlite.Row
        yield db
    finally:
        await db.close()


async def check_database_health() -> bool:
    """Return True if the database is reachable."""
    try:
        async with get_db_connection() as db:
            await db.execute("SELECT 1")
    except Exception:  # noqa: BLE001
        return False
    return True


async def initialize_database() -> None:
    """Create the data directory, apply migrations, and enable WAL mode."""
    db_path = _get_db_path()
    data_dir = Path(db_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(db_path)
    try:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys = ON")

        migration_file = _MIGRATIONS_DIR / "001_initial_schema.sql"
        schema_sql = migration_file.read_text()
        await db.executescript(schema_sql)

        await db.commit()
        logger.info("Database initialized at %s", db_path)
    finally:
        await db.close()
