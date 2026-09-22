"""Main entry point for Tash Tech Rector Anonymous Telegram Bot."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import get_settings
from bot.database import Database
from bot.handlers import get_main_router


async def setup_bot_commands(bot: Bot) -> None:
    """Set default bot commands in Telegram menu."""
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish / Start"),
        BotCommand(command="appeal", description="Murojaat yuborish / Send appeal"),
        BotCommand(command="language", description="Tilni o'zgartirish / Change language"),
        BotCommand(command="cancel", description="Bekor qilish / Cancel"),
    ]
    try:
        await bot.set_my_commands(commands)
    except Exception as exc:
        logging.warning("Failed to set bot commands: %s", exc)


async def main() -> None:
    """Initialize dependencies and start polling."""
    # Load configuration
    try:
        config = get_settings()
    except Exception as exc:
        print(f"CRITICAL: Failed to load configuration: {exc}", file=sys.stderr)
        print("Please make sure .env is configured properly based on .env.example", file=sys.stderr)
        sys.exit(1)

    # Configure logging
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("tashtech_bot")
    logger.info("Starting Tash Tech Rector Anonymous Bot...")

    # Initialize SQLite Database
    db = Database(db_path=config.db_path)
    await db.init()
    logger.info("Database initialized at %s", config.db_path)

    # Initialize Bot and Dispatcher
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register dependency injection objects in Dispatcher workflow data
    dp["db"] = db
    dp["config"] = config

    # Register routers
    main_router = get_main_router()
    dp.include_router(main_router)

    # Setup bot menu commands
    await setup_bot_commands(bot)

    # Delete any pending updates before polling to start clean
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Pending webhook/updates cleared.")
    except Exception as exc:
        logger.warning("Could not delete webhook: %s", exc)

    logger.info("Bot started polling successfully.")
    try:
        await dp.start_polling(bot, db=db, config=config)
    finally:
        await bot.session.close()
        logger.info("Bot session closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot terminated gracefully.")
