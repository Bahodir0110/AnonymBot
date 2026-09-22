"""Handlers for appeal submission flow, rate limiting, media group collection, and anonymous forwarding."""

import asyncio
import logging
from typing import Dict, List, Optional
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
# Restrict student interactions to private chats; do not handle or leak into Rector groups/channels
router.message.filter(F.chat.type == "private")


class MediaGroupCollector:
    """Collects messages arriving with the same media_group_id over a debounce window."""

    def __init__(self, delay_seconds: float = 0.6) -> None:
        self.delay_seconds = delay_seconds
        self._buffers: Dict[str, List[Message]] = {}

    async def add_message(self, message: Message) -> Optional[List[Message]]:
        """Add a message to the group.

        Returns the complete list of Messages if this invocation is the leader,
        or None if this is a follower message that was buffered.
        """
        group_id = getattr(message, "media_group_id", None)
        if not group_id:
            return [message]

        if group_id in self._buffers:
            self._buffers[group_id].append(message)
            return None

        # Leader message: initialize buffer and wait for followers
        self._buffers[group_id] = [message]
        await asyncio.sleep(self.delay_seconds)
        return self._buffers.pop(group_id, [message])


media_group_collector = MediaGroupCollector()


def detect_content_type(message: Message) -> Optional[str]:
    """Detect supported content type from an incoming message."""
    if getattr(message, "text", None):
        return "text"
    if getattr(message, "photo", None):
        return "photo"
    if getattr(message, "document", None):
        return "document"
    if getattr(message, "voice", None):
        return "voice"
    if getattr(message, "video", None):
        return "video"
    if getattr(message, "audio", None):
        return "audio"
    if getattr(message, "video_note", None):
        return "video_note"
    if getattr(message, "animation", None):
        return "animation"
    return None


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

    # Check content type
    content_type = detect_content_type(message)
    if content_type is None:
        await message.answer(
            text=get_text("unsupported_content", lang=user_lang),
            reply_markup=get_cancel_reply_keyboard(lang=user_lang),
            parse_mode="HTML",
        )
        return

    # Handle media groups (albums)
    messages = await media_group_collector.add_message(message)
    if messages is None:
        # Follower message in album: buffered, leader will handle
        return

    # Ensure state is still waiting_for_appeal
    current_state = await state.get_state()
    if current_state != AppealStates.waiting_for_appeal.state:
        return

    is_album = len(messages) > 1
    recorded_content_type = "album" if is_album else content_type

    # Create appeal record in DB and obtain sequential reference ID (e.g. #TT-0001)
    appeal_id, ref_code = await db.create_appeal(
        language_code=user_lang,
        content_type=recorded_content_type,
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

        if is_album:
            album_caption = next((m.caption for m in messages if m.caption), "")
            if album_caption:
                full_header = f"{header}\n\n📝 <b>Izoh:</b>\n{escape_html(album_caption)}"
            else:
                full_header = header

            if len(full_header) <= 4096:
                await bot.send_message(
                    chat_id=rector_chat_id,
                    message_thread_id=thread_id,
                    text=full_header,
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    chat_id=rector_chat_id,
                    message_thread_id=thread_id,
                    text=header,
                    parse_mode="HTML",
                )
                for chunk in split_text_chunks(escape_html(album_caption)):
                    await bot.send_message(
                        chat_id=rector_chat_id,
                        message_thread_id=thread_id,
                        text=chunk,
                        parse_mode="HTML",
                    )

            msg_ids = [m.message_id for m in messages]
            try:
                await bot.copy_messages(
                    chat_id=rector_chat_id,
                    message_thread_id=thread_id,
                    from_chat_id=messages[0].chat.id,
                    message_ids=msg_ids,
                    remove_caption=True,
                )
            except Exception:
                for m in messages:
                    await bot.copy_message(
                        chat_id=rector_chat_id,
                        message_thread_id=thread_id,
                        from_chat_id=m.chat.id,
                        message_id=m.message_id,
                        caption="",
                    )
        elif content_type == "text":
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
            # Single media attachment
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
                # Header + caption exceeds 1024 chars (Telegram media caption limit).
                # Deliver header and student caption as text message(s) first,
                # then copy media with empty caption to avoid 400 Bad Request errors.
                caption_text = f"{header}\n\n📝 <b>Izoh:</b>\n{escape_html(student_caption)}"
                if len(caption_text) <= 4096:
                    await bot.send_message(
                        chat_id=rector_chat_id,
                        message_thread_id=thread_id,
                        text=caption_text,
                        parse_mode="HTML",
                    )
                else:
                    await bot.send_message(
                        chat_id=rector_chat_id,
                        message_thread_id=thread_id,
                        text=header,
                        parse_mode="HTML",
                    )
                    for chunk in split_text_chunks(escape_html(student_caption)):
                        await bot.send_message(
                            chat_id=rector_chat_id,
                            message_thread_id=thread_id,
                            text=chunk,
                            parse_mode="HTML",
                        )

                await bot.copy_message(
                    chat_id=rector_chat_id,
                    message_thread_id=thread_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                    caption="",
                )

        logger.info("Delivered appeal %s (type: %s) to Rector chat %s", ref_code, recorded_content_type, rector_chat_id)

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


@router.message()
async def handle_unhandled_message(message: Message, db: Database) -> None:
    """Guide student back to main menu when receiving message outside active appeal state."""
    user_lang = await db.get_user_language(message.from_user.id) or "uz"
    await message.answer(
        text=get_text("main_menu", lang=user_lang),
        reply_markup=get_main_reply_keyboard(lang=user_lang),
        parse_mode="HTML",
    )
