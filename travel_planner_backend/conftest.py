"""
Pytest configuration for the Travel Planner backend.

Key goal: make tests hermetic by forcing SQLAlchemy to use a temporary SQLite DB
instead of the persisted on-disk DB committed in the repo.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="session", autouse=True)
def _use_temp_sqlite_db_for_tests(tmp_path_factory: pytest.TempPathFactory) -> Generator[None, None, None]:
    """
    Force backend to use a temporary SQLite DB for the entire pytest session.

    Implementation notes:
    - The app reads DB URL from BACKEND_DATABASE_URL (see src/storage/db.py).
    - src.storage.db keeps module-level singletons (_ENGINE and _SessionMaker).
      We must reset those after setting the env var so a new engine is created.
    - We initialize schema via init_db() so FastAPI endpoints have tables.

    This fixture is autouse so existing tests do not need to be modified.
    """
    tmp_dir: Path = tmp_path_factory.mktemp("sqlite_db")
    db_file = tmp_dir / "test.sqlite3"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    # Ensure the environment variable is set before any engine is created.
    os.environ["BACKEND_DATABASE_URL"] = db_url

    # Import after env var set, then reset any already-created singletons.
    from src.storage import db as storage_db  # local import to avoid early module import side effects

    storage_db._ENGINE = None
    storage_db._SessionMaker = None

    # Create schema on the temp DB.
    import asyncio

    asyncio.run(storage_db.init_db())

    try:
        yield
    finally:
        # Cleanup: dispose engine and clear env var so local runs aren't affected.
        # (In CI this is mostly redundant but keeps things tidy.)
        if storage_db._ENGINE is not None:
            asyncio.run(storage_db._ENGINE.dispose())
        storage_db._ENGINE = None
        storage_db._SessionMaker = None
        os.environ.pop("BACKEND_DATABASE_URL", None)
