"""Keyboards module for Tash Tech Rector Anonymous Bot."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from bot.locales import (
    BTN_ANONYMOUS,
    BTN_CANCEL,
    BTN_CHANGE_LANGUAGE,
    BTN_OPEN,
    BTN_SEND_APPEAL,
)


def get_language_inline_keyboard() -> InlineKeyboardMarkup:
    """Return inline keyboard for language selection."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
            ],
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            ],
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            ],
        ]
    )
    return keyboard


def get_main_reply_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Return persistent reply keyboard for main student navigation.

    Includes only:
    - Send appeal
    - Change language
    """
    send_appeal_btn = BTN_SEND_APPEAL.get(lang, BTN_SEND_APPEAL["uz"])
    change_lang_btn = BTN_CHANGE_LANGUAGE.get(lang, BTN_CHANGE_LANGUAGE["uz"])

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=send_appeal_btn)],
            [KeyboardButton(text=change_lang_btn)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
    return keyboard


def get_cancel_reply_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Return reply keyboard with only Cancel button during appeal writing."""
    cancel_btn = BTN_CANCEL.get(lang, BTN_CANCEL["uz"])

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=cancel_btn)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard


def get_appeal_type_reply_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Return reply keyboard to choose appeal type (Anonymous vs Open) or Cancel."""
    anon_btn = BTN_ANONYMOUS.get(lang, BTN_ANONYMOUS["uz"])
    open_btn = BTN_OPEN.get(lang, BTN_OPEN["uz"])
    cancel_btn = BTN_CANCEL.get(lang, BTN_CANCEL["uz"])

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=anon_btn), KeyboardButton(text=open_btn)],
            [KeyboardButton(text=cancel_btn)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard
