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

BTN_ANONYMOUS = {
    "uz": "🔒 Anonim",
    "ru": "🔒 Анонимно",
    "en": "🔒 Anonymous",
}

BTN_OPEN = {
    "uz": "🔓 Ochiq",
    "ru": "🔓 Открыто",
    "en": "🔓 Open",
}

# Sets for quick matching across any language
ALL_SEND_APPEAL_BTNS = set(BTN_SEND_APPEAL.values())
ALL_CHANGE_LANGUAGE_BTNS = set(BTN_CHANGE_LANGUAGE.values())
ALL_CANCEL_BTNS = set(BTN_CANCEL.values())
ALL_ANONYMOUS_BTNS = set(BTN_ANONYMOUS.values())
ALL_OPEN_BTNS = set(BTN_OPEN.values())
ALL_APPEAL_TYPE_BTNS = ALL_ANONYMOUS_BTNS | ALL_OPEN_BTNS

TEXTS: Dict[str, Dict[str, str]] = {
    "start_welcome": {
        "uz": (
            "👋 Assalomu alaykum! <b>Tash Tech</b> ijrochi direktoriga anonim murojaat qilish botiga xush kelibsiz.\n\n"
            "Bu yerda siz o'z taklif, shikoyat va murojaatlaringizni to'g'ridan-to'g'ri ijrochi direktorga "
            "to'liq anonim tarzda yuborishingiz mumkin. Shaxsingiz hech qachon oshkor etilmaydi.\n\n"
            "🌐 Iltimos, tilni tanlang:"
        ),
        "ru": (
            "👋 Здравствуйте! Добро пожаловать в бот анонимных обращений к исполнительному директору <b>Tash Tech</b>.\n\n"
            "Здесь вы можете отправить свои предложения, жалобы и обращения напрямую исполнительному директору "
            "полностью анонимно. Ваша личность никогда не будет раскрыта.\n\n"
            "🌐 Пожалуйста, выберите язык:"
        ),
        "en": (
            "👋 Hello! Welcome to the <b>Tash Tech</b> CEO Anonymous Appeals Bot.\n\n"
            "Here you can submit your proposals, complaints, and feedback directly to the CEO "
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
    "choose_appeal_type": {
        "uz": "🔐 Murojaat turini tanlang:",
        "ru": "🔐 Выберите тип обращения:",
        "en": "🔐 Choose appeal type:",
    },
    "name_prompt": {
        "uz": "👤 Ism-familiyangizni kiriting:",
        "ru": "👤 Как вас зовут?",
        "en": "👤 What is your full name?",
    },
    "contact_prompt": {
        "uz": "📞 Bog'lanish uchun kontakt (telefon yoki email):",
        "ru": "📞 Укажите контакт для связи (телефон или email):",
        "en": "📞 Enter contact info (phone or email):",
    },
    "invalid_name": {
        "uz": "👤 Iltimos, ism-familiyangizni matn ko'rinishida kiriting:",
        "ru": "👤 Пожалуйста, укажите ваше имя и фамилию текстом:",
        "en": "👤 Please enter your full name as text:",
    },
    "invalid_contact": {
        "uz": "📞 Iltimos, bog'lanish kontaktini matn ko'rinishida kiriting:",
        "ru": "📞 Пожалуйста, укажите контакт для связи текстом:",
        "en": "📞 Please enter your contact info as text:",
    },
    "appeal_prompt": {
        "uz": "✍️ Murojaatingizni yozing:",
        "ru": "✍️ Опишите ваше обращение:",
        "en": "✍️ Write your appeal:",
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
    "appeal_submitted_anonymous": {
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
    "appeal_submitted_open": {
        "uz": (
            "✅ Rahmat! Murojaatingiz yuborildi.\n\n"
            "🔓 Ochiq murojaat — ma'lumotlaringiz ijrochi direktorga yetkazildi."
        ),
        "ru": (
            "✅ Спасибо! Ваше обращение отправлено.\n\n"
            "🔓 Открытое обращение — ваши данные переданы исполнительному директору."
        ),
        "en": (
            "✅ Thank you! Your appeal has been sent.\n\n"
            "🔓 Open appeal — your contact details were delivered to the CEO."
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
        "anonymous": BTN_ANONYMOUS,
        "open": BTN_OPEN,
    }
    mapping = button_map.get(button_type, {})
    return mapping.get(lang, mapping.get("uz", ""))


def get_language_display_name(lang_code: str) -> str:
    """Return friendly display name of the language."""
    return SUPPORTED_LANGUAGES.get(lang_code, lang_code)
