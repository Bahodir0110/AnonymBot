"""Unit tests for SQLite database operations."""

import time
import pytest
import aiosqlite
from bot.database import Database


@pytest.fixture
async def temp_db(tmp_path):
    """Fixture to create an initialized test database."""
    db_file = tmp_path / "test_bot.db"
    db = Database(str(db_file))
    await db.init()
    return db


@pytest.mark.asyncio
async def test_user_language_lifecycle(temp_db):
    """Test getting and updating user language."""
    # Initially user does not exist
    assert await temp_db.get_user_language(1001) is None

    # Set to uz
    await temp_db.set_user_language(1001, "uz")
    assert await temp_db.get_user_language(1001) == "uz"

    # Update to ru
    await temp_db.set_user_language(1001, "ru")
    assert await temp_db.get_user_language(1001) == "ru"

    # Update to en
    await temp_db.set_user_language(1001, "en")
    assert await temp_db.get_user_language(1001) == "en"


@pytest.mark.asyncio
async def test_rate_limiting_cooldown(temp_db):
    """Test rate limit cooldown calculation."""
    user_id = 2002
    cooldown = 60

    # Never appealed: remaining cooldown is 0
    assert await temp_db.get_rate_limit_remaining(user_id, cooldown) == 0

    # Record appeal just now
    await temp_db.update_last_appeal_time(user_id)
    remaining = await temp_db.get_rate_limit_remaining(user_id, cooldown)
    assert 55 <= remaining <= 60

    # Simulate past appeal (70 seconds ago)
    past_time = time.time() - 70
    await temp_db.update_last_appeal_time(user_id, appeal_time=past_time)
    assert await temp_db.get_rate_limit_remaining(user_id, cooldown) == 0


@pytest.mark.asyncio
async def test_sequential_appeal_ids(temp_db):
    """Test that appeals generate strictly sequential reference IDs like #TT-0001, #TT-0002."""
    id1, ref1 = await temp_db.create_appeal(language_code="uz", content_type="text")
    assert id1 == 1
    assert ref1 == "#TT-0001"

    id2, ref2 = await temp_db.create_appeal(language_code="ru", content_type="photo")
    assert id2 == 2
    assert ref2 == "#TT-0002"

    id3, ref3 = await temp_db.create_appeal(language_code="en", content_type="document")
    assert id3 == 3
    assert ref3 == "#TT-0003"

    count = await temp_db.get_appeal_count()
    assert count == 3


@pytest.mark.asyncio
async def test_database_anonymity_schema(temp_db):
    """Verify that appeals table schema contains NO user_id column for zero-knowledge anonymity."""
    async with aiosqlite.connect(temp_db.db_path) as conn:
        async with conn.execute("PRAGMA table_info(appeals);") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]

    assert "id" in columns
    assert "reference_code" in columns
    assert "language_code" in columns
    assert "content_type" in columns
    assert "is_anonymous" in columns
    assert "full_name" in columns
    assert "contact_info" in columns
    assert "telegram_username" in columns
    assert "created_at" in columns

    # Strict check: telegram user_id must NOT be stored in appeals
    assert "user_id" not in columns
    assert "student_id" not in columns
    assert "sender_id" not in columns


@pytest.mark.asyncio
async def test_open_appeal_storage(temp_db):
    """Verify storing open appeal records with student name, contact details, and username."""
    aid, ref = await temp_db.create_appeal(
        language_code="uz",
        content_type="text",
        is_anonymous=False,
        full_name="Bobur Mirzo",
        contact_info="+998901234567",
        telegram_username="@bobur_dev",
    )
    assert aid == 1
    assert ref == "#TT-0001"

    row = await temp_db.get_appeal(aid)
    assert row is not None
    assert row["is_anonymous"] == 0
    assert row["full_name"] == "Bobur Mirzo"
    assert row["contact_info"] == "+998901234567"
    assert row["telegram_username"] == "bobur_dev"

    # Anonymous appeal
    aid2, ref2 = await temp_db.create_appeal(
        language_code="ru",
        content_type="photo",
        is_anonymous=True,
        telegram_username="should_be_ignored",
    )
    row2 = await temp_db.get_appeal(aid2)
    assert row2 is not None
    assert row2["is_anonymous"] == 1
    assert row2["full_name"] is None
    assert row2["contact_info"] is None
    assert row2["telegram_username"] is None


@pytest.mark.asyncio
async def test_database_safe_migration(tmp_path):
    """Verify that existing database tables without is_anonymous/full_name/contact_info/telegram_username are safely migrated."""
    old_db_file = tmp_path / "old_bot.db"

    # Create old schema table without the new columns
    async with aiosqlite.connect(str(old_db_file)) as conn:
        await conn.execute(
            """
            CREATE TABLE appeals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_code TEXT NOT NULL,
                language_code TEXT NOT NULL,
                content_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await conn.execute(
            "INSERT INTO appeals (reference_code, language_code, content_type) VALUES ('#TT-0001', 'uz', 'text');"
        )
        await conn.commit()

    # Now init using our Database class
    migrated_db = Database(str(old_db_file))
    await migrated_db.init()

    # Verify columns were added
    async with aiosqlite.connect(str(old_db_file)) as conn:
        async with conn.execute("PRAGMA table_info(appeals);") as cursor:
            cols = [r[1] for r in await cursor.fetchall()]

    assert "is_anonymous" in cols
    assert "full_name" in cols
    assert "contact_info" in cols
    assert "telegram_username" in cols

    # Verify old data survived
    old_row = await migrated_db.get_appeal(1)
    assert old_row is not None
    assert old_row["reference_code"] == "#TT-0001"
    assert old_row["is_anonymous"] == 1
