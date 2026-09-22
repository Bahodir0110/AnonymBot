"""Unit tests for locales and translations."""

from bot.locales import (
    ALL_CANCEL_BTNS,
    ALL_CHANGE_LANGUAGE_BTNS,
    ALL_SEND_APPEAL_BTNS,
    BTN_CANCEL,
    BTN_CHANGE_LANGUAGE,
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

    assert "✉️ Murojaat yuborish" in ALL_SEND_APPEAL_BTNS
    assert "✉️ Отправить обращение" in ALL_SEND_APPEAL_BTNS
    assert "✉️ Send appeal" in ALL_SEND_APPEAL_BTNS

    assert "🌐 Tilni o'zgartirish" in ALL_CHANGE_LANGUAGE_BTNS
    assert "🌐 Сменить язык" in ALL_CHANGE_LANGUAGE_BTNS
    assert "🌐 Change language" in ALL_CHANGE_LANGUAGE_BTNS

    assert "❌ Bekor qilish" in ALL_CANCEL_BTNS
    assert "❌ Отмена" in ALL_CANCEL_BTNS
    assert "❌ Cancel" in ALL_CANCEL_BTNS


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
