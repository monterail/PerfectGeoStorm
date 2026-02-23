"""Async SQLite database connection and initialization."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

DATABASE_PATH: str = os.environ.get("DATABASE_URL", "./data/geo-storm.db")

_MIGRATIONS_DIR: Path = Path(__file__).resolve().parent.parent / "migrations"


@asynccontextmanager
async def get_db_connection() -> AsyncIterator[aiosqlite.Connection]:
    """Yield an async SQLite connection with foreign keys enabled."""
    db = await aiosqlite.connect(DATABASE_PATH)
    try:
        await db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = aiosqlite.Row
        yield db
    finally:
        await db.close()


async def initialize_database() -> None:
    """Create the data directory, apply migrations, and enable WAL mode."""
    data_dir = Path(DATABASE_PATH).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(DATABASE_PATH)
    try:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys = ON")

        migration_file = _MIGRATIONS_DIR / "001_initial_schema.sql"
        schema_sql = migration_file.read_text()
        await db.executescript(schema_sql)

        await db.commit()
        logger.info("Database initialized at %s", DATABASE_PATH)
    finally:
        await db.close()
