"""Handlers for language selection and language changing."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import Database
from bot.keyboards import get_language_inline_keyboard, get_main_reply_keyboard
from bot.locales import (
    ALL_CHANGE_LANGUAGE_BTNS,
    SUPPORTED_LANGUAGES,
    get_text,
)

router = Router(name="language_router")


@router.message(F.text.in_(ALL_CHANGE_LANGUAGE_BTNS))
@router.message(Command("language", "lang"))
async def handle_change_language_button(message: Message, state: FSMContext, db: Database) -> None:
    """Handle reply keyboard button or command to change language."""
    await state.clear()
    user_lang = await db.get_user_language(message.from_user.id) or "uz"

    await message.answer(
        text=get_text("choose_language", lang=user_lang),
        reply_markup=get_language_inline_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("lang:"))
async def handle_language_callback(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Process language selection from inline keyboard."""
    lang_code = callback.data.split(":", 1)[1]

    if lang_code not in SUPPORTED_LANGUAGES:
        await callback.answer("Invalid language", show_alert=True)
        return

    await db.set_user_language(callback.from_user.id, lang_code)
    await callback.answer()

    # Send confirmation message with new main menu reply keyboard
    confirmation_text = get_text("language_changed", lang=lang_code)
    menu_text = get_text("main_menu", lang=lang_code)

    full_message = f"{confirmation_text}\n\n{menu_text}"

    # We send as a new message so the ReplyKeyboardMarkup updates in student's Telegram client
    await callback.message.answer(
        text=full_message,
        reply_markup=get_main_reply_keyboard(lang=lang_code),
        parse_mode="HTML",
    )
