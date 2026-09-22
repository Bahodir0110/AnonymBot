import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    bot_token: str = Field(..., description="Telegram bot API token")
    rector_chat_id: int = Field(..., description="Telegram chat ID for Rector delivery")
    rector_thread_id: Optional[int] = Field(
        default=None,
        description="Optional message thread ID for supergroup forum topic"
    )
    rate_limit_seconds: int = Field(
        default=60,
        ge=0,
        description="Cooldown duration in seconds between submissions per student"
    )
    db_path: str = Field(
        default="data/bot.db",
        description="Path to SQLite database"
    )
    timezone: str = Field(
        default="Asia/Tashkent",
        description="Timezone for timestamps (UTC+5)"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    @field_validator("rector_thread_id", mode="before")
    @classmethod
    def parse_optional_int(cls, v):
        if v is None or v == "" or (isinstance(v, str) and not v.strip()):
            return None
        return int(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


def get_settings() -> Settings:
    """Return an instance of application settings."""
    return Settings()
