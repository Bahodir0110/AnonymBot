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
    assert "created_at" in columns

    # Strict anonymity check: user_id must NOT be stored in appeals
    assert "user_id" not in columns
    assert "student_id" not in columns
    assert "sender_id" not in columns
