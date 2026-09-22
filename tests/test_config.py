"""Unit tests for bot configuration."""

import pytest
from pydantic import ValidationError
from bot.config import Settings


def test_valid_settings():
    """Verify that settings load correctly with valid inputs."""
    settings = Settings(
        BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        RECTOR_CHAT_ID=-1001234567890,
        RECTOR_THREAD_ID="42",
        RATE_LIMIT_SECONDS="120",
        DB_PATH="test_data/test.db",
        TIMEZONE="Asia/Tashkent",
        LOG_LEVEL="DEBUG",
    )
    assert settings.bot_token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    assert settings.rector_chat_id == -1001234567890
    assert settings.rector_thread_id == 42
    assert settings.rate_limit_seconds == 120
    assert settings.db_path == "test_data/test.db"
    assert settings.timezone == "Asia/Tashkent"
    assert settings.log_level == "DEBUG"


def test_empty_rector_thread_id():
    """Verify that empty string in RECTOR_THREAD_ID is parsed as None."""
    settings = Settings(
        BOT_TOKEN="test_token",
        RECTOR_CHAT_ID=987654321,
        RECTOR_THREAD_ID="",
    )
    assert settings.rector_thread_id is None


def test_default_values():
    """Verify default values when optional fields are omitted."""
    settings = Settings(
        BOT_TOKEN="test_token",
        RECTOR_CHAT_ID=12345,
    )
    assert settings.rector_thread_id is None
    assert settings.rate_limit_seconds == 60
    assert settings.db_path == "data/bot.db"
    assert settings.timezone == "Asia/Tashkent"
    assert settings.log_level == "INFO"


def test_missing_required_fields():
    """Verify ValidationError is raised when required fields are missing."""
    with pytest.raises(ValidationError):
        Settings()
