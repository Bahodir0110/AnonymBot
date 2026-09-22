"""Localization module for Tash Tech Rector Anonymous Bot.

Supported languages:
- uz: O'zbekcha (Latin)
- ru: Русский
- en: English
"""

from typing import Dict, Any

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "uz": "O'zbekcha",
    "ru": "Русский",
    "en": "English",
}

# Button labels
BTN_SEND_APPEAL = {
    "uz": "✉️ Murojaat yuborish",
    "ru": "✉️ Отправить обращение",
    "en": "✉️ Send appeal",
}

BTN_CHANGE_LANGUAGE = {
    "uz": "🌐 Tilni o'zgartirish",
    "ru": "🌐 Сменить язык",
    "en": "🌐 Change language",
}

BTN_CANCEL = {
    "uz": "❌ Bekor qilish",
    "ru": "❌ Отмена",
    "en": "❌ Cancel",
}

# Sets for quick matching across any language
ALL_SEND_APPEAL_BTNS = set(BTN_SEND_APPEAL.values())
ALL_CHANGE_LANGUAGE_BTNS = set(BTN_CHANGE_LANGUAGE.values())
ALL_CANCEL_BTNS = set(BTN_CANCEL.values())

TEXTS: Dict[str, Dict[str, str]] = {
    "start_welcome": {
        "uz": (
            "👋 Assalomu alaykum! <b>Tash Tech</b> rektoriga anonim murojaat qilish botiga xush kelibsiz.\n\n"
            "Bu yerda siz o'z taklif, shikoyat va murojaatlaringizni to'g'ridan-to'g'ri rektorga "
            "to'liq anonim tarzda yuborishingiz mumkin. Shaxsingiz hech qachon oshkor etilmaydi.\n\n"
            "🌐 Iltimos, tilni tanlang:"
        ),
        "ru": (
            "👋 Здравствуйте! Добро пожаловать в бот анонимных обращений к ректору <b>Tash Tech</b>.\n\n"
            "Здесь вы можете отправить свои предложения, жалобы и обращения напрямую ректору "
            "полностью анонимно. Ваша личность никогда не будет раскрыта.\n\n"
            "🌐 Пожалуйста, выберите язык:"
        ),
        "en": (
            "👋 Hello! Welcome to the <b>Tash Tech</b> Rector Anonymous Appeals Bot.\n\n"
            "Here you can submit your proposals, complaints, and feedback directly to the rector "
            "completely anonymously. Your identity will never be revealed.\n\n"
            "🌐 Please choose your language:"
        ),
    },
    "choose_language": {
        "uz": "🌐 Iltimos, kerakli tilni tanlang:",
        "ru": "🌐 Пожалуйста, выберите язык:",
        "en": "🌐 Please select your language:",
    },
    "language_changed": {
        "uz": "✅ Til muvaffaqiyatli tanlandi: <b>O'zbekcha</b>",
        "ru": "✅ Язык успешно выбран: <b>Русский</b>",
        "en": "✅ Language successfully selected: <b>English</b>",
    },
    "main_menu": {
        "uz": "Asosiy menyu. Murojaat yuborish uchun quyidagi tugmani bosing:",
        "ru": "Главное меню. Чтобы отправить обращение, нажмите кнопку ниже:",
        "en": "Main menu. To send an appeal, press the button below:",
    },
    "appeal_prompt": {
        "uz": "✍️ Murojaatingizni yozing:\n\n<i>(Matn, rasm, hujjat/PDF, audio yoki video yuborishingiz mumkin)</i>",
        "ru": "✍️ Напишите ваше обращение:\n\n<i>(Вы можете отправить текст, фото, документ/PDF, аудио или видео)</i>",
        "en": "✍️ Write your appeal:\n\n<i>(You can send text, photo, document/PDF, audio or video)</i>",
    },
    "appeal_submitted": {
        "uz": (
            "✅ Rahmat! Murojaatingiz yuborildi.\n\n"
            "🔒 Anonim murojaat — javob va holat kuzatilmaydi."
        ),
        "ru": (
            "✅ Спасибо! Ваше обращение отправлено.\n\n"
            "🔒 Анонимное обращение — ответ и статус не отслеживаются."
        ),
        "en": (
            "✅ Thank you! Your appeal has been sent.\n\n"
            "🔒 Anonymous appeal — replies and status are not tracked."
        ),
    },
    "appeal_cancelled": {
        "uz": "❌ Murojaat bekor qilindi.",
        "ru": "❌ Обращение отменено.",
        "en": "❌ Appeal cancelled.",
    },
    "rate_limit_warning": {
        "uz": "⏳ Iltimos, keyingi murojaatni yuborishdan oldin {remaining} soniya kuting.",
        "ru": "⏳ Пожалуйста, подождите {remaining} сек. перед отправкой следующего обращения.",
        "en": "⏳ Please wait {remaining} seconds before submitting another appeal.",
    },
    "unsupported_content": {
        "uz": "⚠️ Faqat matn, rasm, hujjat, ovozli xabar yoki video yuborishingiz mumkin.",
        "ru": "⚠️ Пожалуйста, отправляйте только текст, фото, документы, аудио или видео.",
        "en": "⚠️ Please send only text, photo, document, voice message, or video.",
    },
    "general_error": {
        "uz": "⚠️ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
        "ru": "⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.",
        "en": "⚠️ An error occurred. Please try again.",
    },
}


def get_text(key: str, lang: str = "uz", **kwargs: Any) -> str:
    """Retrieve localized string by key and format with kwargs."""
    translations = TEXTS.get(key, {})
    # Fallback to uz, then ru, then en, then raw key
    template = (
        translations.get(lang)
        or translations.get("uz")
        or translations.get("ru")
        or translations.get("en")
        or key
    )
    if kwargs:
        return template.format(**kwargs)
    return template


def get_button_text(button_type: str, lang: str = "uz") -> str:
    """Retrieve button label based on type and language."""
    button_map = {
        "send_appeal": BTN_SEND_APPEAL,
        "change_language": BTN_CHANGE_LANGUAGE,
        "cancel": BTN_CANCEL,
    }
    mapping = button_map.get(button_type, {})
    return mapping.get(lang, mapping.get("uz", ""))


def get_language_display_name(lang_code: str) -> str:
    """Return friendly display name of the language."""
    return SUPPORTED_LANGUAGES.get(lang_code, lang_code)
