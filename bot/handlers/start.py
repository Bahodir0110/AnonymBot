"""Handler for /start command."""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database import Database
from bot.keyboards import get_language_inline_keyboard, get_main_reply_keyboard
from bot.locales import get_text

router = Router(name="start_router")
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def handle_start_command(message: Message, state: FSMContext, db: Database) -> None:
    """Handle /start command by greeting student and prompting language selection."""
    await state.clear()

    user_lang = await db.get_user_language(message.from_user.id)
    lang = user_lang or "uz"

    # Send welcome text with inline language selection keyboard
    welcome_text = get_text("start_welcome", lang=lang)
    await message.answer(
        text=welcome_text,
        reply_markup=get_language_inline_keyboard(),
        parse_mode="HTML",
    )

    # If user already had a language configured, also ensure main reply keyboard is visible
    if user_lang:
        await message.answer(
            text=get_text("main_menu", lang=lang),
            reply_markup=get_main_reply_keyboard(lang=lang),
            parse_mode="HTML",
        )
