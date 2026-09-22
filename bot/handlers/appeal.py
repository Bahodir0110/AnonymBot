"""Handlers for appeal submission flow, rate limiting, and anonymous forwarding."""

import logging
from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import Settings
from bot.database import Database
from bot.keyboards import get_cancel_reply_keyboard, get_main_reply_keyboard
from bot.locales import (
    ALL_CANCEL_BTNS,
    ALL_CHANGE_LANGUAGE_BTNS,
    ALL_SEND_APPEAL_BTNS,
    get_language_display_name,
    get_text,
)
from bot.states import AppealStates
from bot.utils import (
    build_rector_header,
    escape_html,
    format_tashkent_time,
    split_text_chunks,
)

logger = logging.getLogger(__name__)

router = Router(name="appeal_router")


@router.message(F.text.in_(ALL_CANCEL_BTNS))
@router.message(Command("cancel"))
async def handle_cancel_appeal(message: Message, state: FSMContext, db: Database) -> None:
    """Abort writing appeal and return student to main menu."""
    await state.clear()
    user_lang = await db.get_user_language(message.from_user.id) or "uz"

    await message.answer(
        text=get_text("appeal_cancelled", lang=user_lang),
        reply_markup=get_main_reply_keyboard(lang=user_lang),
        parse_mode="HTML",
    )


@router.message(F.text.in_(ALL_SEND_APPEAL_BTNS))
@router.message(Command("appeal"))
async def handle_start_appeal(
    message: Message,
    state: FSMContext,
    db: Database,
    config: Settings,
) -> None:
    """Initiate appeal submission flow with rate-limit check."""
    user_lang = await db.get_user_language(message.from_user.id) or "uz"

    # Check anti-spam cooldown
    remaining_seconds = await db.get_rate_limit_remaining(
        user_id=message.from_user.id,
        cooldown_seconds=config.rate_limit_seconds,
    )
    if remaining_seconds > 0:
        warning_text = get_text(
            "rate_limit_warning",
            lang=user_lang,
            remaining=remaining_seconds,
        )
        await message.answer(
            text=warning_text,
            reply_markup=get_main_reply_keyboard(lang=user_lang),
            parse_mode="HTML",
        )
        return

    # Enter waiting for appeal state
    await state.set_state(AppealStates.waiting_for_appeal)
    await message.answer(
        text=get_text("appeal_prompt", lang=user_lang),
        reply_markup=get_cancel_reply_keyboard(lang=user_lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(AppealStates.waiting_for_appeal))
async def handle_appeal_content(
    message: Message,
    state: FSMContext,
    bot: Bot,
    db: Database,
    config: Settings,
) -> None:
    """Process submitted appeal content (text or media) and deliver to Rector."""
    # If student pressed Change Language button while writing appeal, route to language handler
    if message.text in ALL_CHANGE_LANGUAGE_BTNS:
        await state.clear()
        user_lang = await db.get_user_language(message.from_user.id) or "uz"
        from bot.keyboards import get_language_inline_keyboard
        await message.answer(
            text=get_text("choose_language", lang=user_lang),
            reply_markup=get_language_inline_keyboard(),
            parse_mode="HTML",
        )
        return

    user_lang = await db.get_user_language(message.from_user.id) or "uz"

    # Secondary rate-limit check
    remaining_seconds = await db.get_rate_limit_remaining(
        user_id=message.from_user.id,
        cooldown_seconds=config.rate_limit_seconds,
    )
    if remaining_seconds > 0:
        warning_text = get_text(
            "rate_limit_warning",
            lang=user_lang,
            remaining=remaining_seconds,
        )
        await message.answer(
            text=warning_text,
            reply_markup=get_cancel_reply_keyboard(lang=user_lang),
            parse_mode="HTML",
        )
        return

    # Identify content type
    content_type = None
    if message.text:
        content_type = "text"
    elif message.photo:
        content_type = "photo"
    elif message.document:
        content_type = "document"
    elif message.voice:
        content_type = "voice"
    elif message.video:
        content_type = "video"
    elif message.audio:
        content_type = "audio"
    elif message.video_note:
        content_type = "video_note"

    if content_type is None:
        await message.answer(
            text=get_text("unsupported_content", lang=user_lang),
            reply_markup=get_cancel_reply_keyboard(lang=user_lang),
            parse_mode="HTML",
        )
        return

    # Create appeal record in DB and obtain sequential reference ID (e.g. #TT-0001)
    appeal_id, ref_code = await db.create_appeal(
        language_code=user_lang,
        content_type=content_type,
    )

    # Update cooldown timestamp for student
    await db.update_last_appeal_time(message.from_user.id)

    # Clear state so student is back to ready state
    await state.clear()

    # Format notification header for Rector
    timestamp_str = format_tashkent_time(tz_name=config.timezone)
    lang_name = get_language_display_name(user_lang)
    header = build_rector_header(
        reference_id=ref_code,
        timestamp_str=timestamp_str,
        language_name=lang_name,
    )

    # Deliver to Rector chat ID (and optional thread/topic)
    try:
        rector_chat_id = config.rector_chat_id
        thread_id = config.rector_thread_id

        if content_type == "text":
            full_text = f"{header}\n\n📝 <b>Murojaat matni:</b>\n{escape_html(message.text)}"
            if len(full_text) <= 4096:
                await bot.send_message(
                    chat_id=rector_chat_id,
                    message_thread_id=thread_id,
                    text=full_text,
                    parse_mode="HTML",
                )
            else:
                # Text exceeds single message limit; send header then message chunks
                await bot.send_message(
                    chat_id=rector_chat_id,
                    message_thread_id=thread_id,
                    text=header,
                    parse_mode="HTML",
                )
                for chunk in split_text_chunks(escape_html(message.text)):
                    await bot.send_message(
                        chat_id=rector_chat_id,
                        message_thread_id=thread_id,
                        text=chunk,
                        parse_mode="HTML",
                    )
        else:
            # Media attachment: anonymously copy to Rector without sender info
            student_caption = message.caption or ""
            if student_caption:
                combined_caption = f"{header}\n\n📝 <b>Izoh:</b>\n{escape_html(student_caption)}"
            else:
                combined_caption = header

            if len(combined_caption) <= 1024:
                await bot.copy_message(
                    chat_id=rector_chat_id,
                    message_thread_id=thread_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                    caption=combined_caption,
                    parse_mode="HTML",
                )
            else:
                # Caption too long to attach directly to media, send header separately
                await bot.send_message(
                    chat_id=rector_chat_id,
                    message_thread_id=thread_id,
                    text=header,
                    parse_mode="HTML",
                )
                await bot.copy_message(
                    chat_id=rector_chat_id,
                    message_thread_id=thread_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                )

        logger.info("Delivered appeal %s (type: %s) to Rector chat %s", ref_code, content_type, rector_chat_id)

        # Send confirmation to student matching UI requirement
        confirmation_msg = get_text("appeal_submitted", lang=user_lang)
        await message.answer(
            text=confirmation_msg,
            reply_markup=get_main_reply_keyboard(lang=user_lang),
            parse_mode="HTML",
        )

    except Exception as exc:
        logger.exception("Failed to deliver appeal %s to Rector: %s", ref_code, exc)
        await message.answer(
            text=get_text("general_error", lang=user_lang),
            reply_markup=get_main_reply_keyboard(lang=user_lang),
            parse_mode="HTML",
        )
