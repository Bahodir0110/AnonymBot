"""Handlers package for Tash Tech Rector Anonymous Bot."""

from aiogram import Router
from bot.handlers.start import router as start_router
from bot.handlers.language import router as language_router
from bot.handlers.appeal import router as appeal_router


def get_main_router() -> Router:
    """Combine and return all application routers."""
    main_router = Router(name="main_router")
    # Order matters: language and appeal buttons take priority over general fallbacks
    main_router.include_router(start_router)
    main_router.include_router(language_router)
    main_router.include_router(appeal_router)
    return main_router
