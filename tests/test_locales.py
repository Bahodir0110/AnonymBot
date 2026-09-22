"""Unit tests for locales and translations."""

from bot.locales import (
    ALL_ANONYMOUS_BTNS,
    ALL_APPEAL_TYPE_BTNS,
    ALL_CANCEL_BTNS,
    ALL_CHANGE_LANGUAGE_BTNS,
    ALL_OPEN_BTNS,
    ALL_SEND_APPEAL_BTNS,
    BTN_ANONYMOUS,
    BTN_CANCEL,
    BTN_CHANGE_LANGUAGE,
    BTN_OPEN,
    BTN_SEND_APPEAL,
    SUPPORTED_LANGUAGES,
    get_button_text,
    get_language_display_name,
    get_text,
)


def test_supported_languages():
    """Verify that uz, ru, and en are supported."""
    assert "uz" in SUPPORTED_LANGUAGES
    assert "ru" in SUPPORTED_LANGUAGES
    assert "en" in SUPPORTED_LANGUAGES
    assert SUPPORTED_LANGUAGES["uz"] == "O'zbekcha"
    assert SUPPORTED_LANGUAGES["ru"] == "Русский"
    assert SUPPORTED_LANGUAGES["en"] == "English"


def test_screenshot_confirmation_message_uz():
    """Verify the exact confirmation message matching screenshot in Uzbek."""
    expected_uz = (
        "✅ Rahmat! Murojaatingiz yuborildi.\n\n"
        "🔒 Anonim murojaat — javob va holat kuzatilmaydi."
    )
    assert get_text("appeal_submitted", lang="uz") == expected_uz


def test_screenshot_confirmation_message_ru_and_en():
    """Verify localized confirmations exist for Russian and English."""
    ru_text = get_text("appeal_submitted", lang="ru")
    assert "✅ Спасибо!" in ru_text
    assert "🔒 Анонимное обращение" in ru_text

    en_text = get_text("appeal_submitted", lang="en")
    assert "✅ Thank you!" in en_text
    assert "🔒 Anonymous appeal" in en_text


def test_rate_limit_formatting():
    """Verify rate limit warning formats the remaining seconds correctly."""
    uz_warning = get_text("rate_limit_warning", lang="uz", remaining=45)
    assert "45 soniya" in uz_warning

    ru_warning = get_text("rate_limit_warning", lang="ru", remaining=30)
    assert "30 сек" in ru_warning

    en_warning = get_text("rate_limit_warning", lang="en", remaining=15)
    assert "15 seconds" in en_warning


def test_button_mappings():
    """Verify button text retrieval and all-buttons sets."""
    assert BTN_SEND_APPEAL["uz"] == "✉️ Murojaat yuborish"
    assert BTN_CHANGE_LANGUAGE["uz"] == "🌐 Tilni o'zgartirish"
    assert BTN_CANCEL["uz"] == "❌ Bekor qilish"
    assert BTN_ANONYMOUS["uz"] == "🔒 Anonim"
    assert BTN_OPEN["uz"] == "🔓 Ochiq"

    assert "✉️ Murojaat yuborish" in ALL_SEND_APPEAL_BTNS
    assert "✉️ Отправить обращение" in ALL_SEND_APPEAL_BTNS
    assert "✉️ Send appeal" in ALL_SEND_APPEAL_BTNS

    assert "🌐 Tilni o'zgartirish" in ALL_CHANGE_LANGUAGE_BTNS
    assert "🌐 Сменить язык" in ALL_CHANGE_LANGUAGE_BTNS
    assert "🌐 Change language" in ALL_CHANGE_LANGUAGE_BTNS

    assert "❌ Bekor qilish" in ALL_CANCEL_BTNS
    assert "❌ Отмена" in ALL_CANCEL_BTNS
    assert "❌ Cancel" in ALL_CANCEL_BTNS

    assert "🔒 Anonim" in ALL_ANONYMOUS_BTNS
    assert "🔒 Анонимно" in ALL_ANONYMOUS_BTNS
    assert "🔒 Anonymous" in ALL_ANONYMOUS_BTNS

    assert "🔓 Ochiq" in ALL_OPEN_BTNS
    assert "🔓 Открыто" in ALL_OPEN_BTNS
    assert "🔓 Open" in ALL_OPEN_BTNS

    assert len(ALL_APPEAL_TYPE_BTNS) == 6
    assert get_button_text("anonymous", lang="ru") == "🔒 Анонимно"
    assert get_button_text("open", lang="en") == "🔓 Open"


def test_appeal_types_and_open_flow_texts():
    """Verify localization keys for appeal type selection, open flow prompts, and open confirmation."""
    # Choose appeal type
    assert get_text("choose_appeal_type", lang="uz") == "🔐 Murojaat turini tanlang:"
    assert get_text("choose_appeal_type", lang="ru") == "🔐 Выберите тип обращения:"
    assert get_text("choose_appeal_type", lang="en") == "🔐 Choose appeal type:"

    # Name prompt
    assert get_text("name_prompt", lang="uz") == "👤 Ism-familiyangizni kiriting:"
    assert get_text("name_prompt", lang="ru") == "👤 Как вас зовут?"
    assert get_text("name_prompt", lang="en") == "👤 What is your full name?"

    # Contact prompt
    assert get_text("contact_prompt", lang="uz") == "📞 Bog'lanish uchun kontakt (telefon yoki email):"
    assert get_text("contact_prompt", lang="ru") == "📞 Укажите контакт для связи (телефон или email):"
    assert get_text("contact_prompt", lang="en") == "📞 Enter contact info (phone or email):"

    # Appeal prompt
    assert get_text("appeal_prompt", lang="uz") == "✍️ Murojaatingizni yozing:"
    assert get_text("appeal_prompt", lang="ru") == "✍️ Опишите ваше обращение:"
    assert get_text("appeal_prompt", lang="en") == "✍️ Write your appeal:"

    # Open appeal submitted confirmation
    assert "🔓 Ochiq murojaat" in get_text("appeal_submitted_open", lang="uz")
    assert "🔓 Открытое обращение" in get_text("appeal_submitted_open", lang="ru")
    assert "🔓 Open appeal" in get_text("appeal_submitted_open", lang="en")


def test_fallback_behavior():
    """Verify get_text falls back gracefully for missing languages or keys."""
    # Unknown lang falls back to uz
    assert "Tash Tech" in get_text("start_welcome", lang="de")
    # Non-existent key returns key itself
    assert get_text("non_existent_key_xyz", lang="uz") == "non_existent_key_xyz"


def test_language_display_names():
    """Verify language display name lookup."""
    assert get_language_display_name("uz") == "O'zbekcha"
    assert get_language_display_name("ru") == "Русский"
    assert get_language_display_name("en") == "English"
    assert get_language_display_name("unknown") == "unknown"
