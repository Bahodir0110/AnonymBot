"""Database management module using aiosqlite."""

import math
import os
import time
from typing import Optional, Tuple
import aiosqlite

from bot.utils import format_reference_id


class Database:
    """Async SQLite database manager for user settings and appeals."""

    def __init__(self, db_path: str = "data/bot.db") -> None:
        self.db_path = db_path

    async def init(self) -> None:
        """Initialize database tables and performance pragmas."""
        parent_dir = os.path.dirname(self.db_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")

            # Users table: stores user language and cooldown timestamp
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    language_code TEXT NOT NULL DEFAULT 'uz',
                    last_appeal_at REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Appeals table: stores sequential references and metadata WITHOUT student identity
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS appeals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reference_code TEXT NOT NULL,
                    language_code TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            await db.commit()

    async def get_user_language(self, user_id: int) -> Optional[str]:
        """Fetch user's preferred language, or None if user not registered yet."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT language_code FROM users WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                return None

    async def set_user_language(self, user_id: int, language_code: str) -> None:
        """Upsert user language selection."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (user_id, language_code, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    language_code = excluded.language_code,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (user_id, language_code),
            )
            await db.commit()

    async def get_rate_limit_remaining(self, user_id: int, cooldown_seconds: int) -> int:
        """Check if user is on cooldown.

        Returns 0 if allowed to submit, or positive seconds remaining.
        """
        if cooldown_seconds <= 0:
            return 0

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT last_appeal_at FROM users WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row or row[0] is None or row[0] == 0:
                    return 0

                last_time = float(row[0])
                elapsed = time.time() - last_time
                remaining = math.ceil(cooldown_seconds - elapsed)
                return max(0, remaining)

    async def update_last_appeal_time(self, user_id: int, appeal_time: Optional[float] = None) -> None:
        """Update last appeal timestamp for user for rate-limiting."""
        if appeal_time is None:
            appeal_time = time.time()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (user_id, last_appeal_at, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    last_appeal_at = excluded.last_appeal_at,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (user_id, appeal_time),
            )
            await db.commit()

    async def create_appeal(self, language_code: str, content_type: str) -> Tuple[int, str]:
        """Create new appeal record and return (id, reference_code) e.g. (1, '#TT-0001')."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                INSERT INTO appeals (reference_code, language_code, content_type)
                VALUES ('PENDING', ?, ?);
                """,
                (language_code, content_type),
            ) as cursor:
                appeal_id = cursor.lastrowid
                ref_code = format_reference_id(appeal_id)

            await db.execute(
                "UPDATE appeals SET reference_code = ? WHERE id = ?;",
                (ref_code, appeal_id),
            )
            await db.commit()
            return appeal_id, ref_code

    async def get_appeal_count(self) -> int:
        """Return total number of appeals submitted."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM appeals;") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
