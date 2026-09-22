"""Unit tests for bot keyboards."""

from bot.keyboards import (
    get_appeal_type_reply_keyboard,
    get_cancel_reply_keyboard,
    get_language_inline_keyboard,
    get_main_reply_keyboard,
)


def test_language_inline_keyboard():
    """Verify inline keyboard has 3 language buttons with valid callback data."""
    kb = get_language_inline_keyboard()
    assert len(kb.inline_keyboard) == 3

    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    texts = [btn.text for row in kb.inline_keyboard for btn in row]

    assert "lang:uz" in callbacks
    assert "lang:ru" in callbacks
    assert "lang:en" in callbacks

    assert any("O'zbekcha" in t for t in texts)
    assert any("Русский" in t for t in texts)
    assert any("English" in t for t in texts)


def test_main_reply_keyboard():
    """Verify main reply keyboard contains only Send Appeal and Change Language buttons."""
    for lang in ["uz", "ru", "en"]:
        kb = get_main_reply_keyboard(lang=lang)
        buttons = [btn.text for row in kb.keyboard for btn in row]

        # Must have exactly 2 buttons
        assert len(buttons) == 2

        # Check no "Mening murojaatlarim" / "My appeals" button
        for b in buttons:
            assert "Mening murojaatlarim" not in b
            assert "Мои обращения" not in b
            assert "My appeals" not in b

        assert kb.resize_keyboard is True
        assert kb.is_persistent is True


def test_cancel_reply_keyboard():
    """Verify cancel keyboard has only the cancel button."""
    for lang, expected_word in [("uz", "Bekor qilish"), ("ru", "Отмена"), ("en", "Cancel")]:
        kb = get_cancel_reply_keyboard(lang=lang)
        buttons = [btn.text for row in kb.keyboard for btn in row]
        assert len(buttons) == 1
        assert expected_word in buttons[0]
        assert kb.resize_keyboard is True


def test_appeal_type_reply_keyboard():
    """Verify appeal type reply keyboard has Anonymous, Open, and Cancel buttons."""
    # UZ
    kb_uz = get_appeal_type_reply_keyboard(lang="uz")
    assert len(kb_uz.keyboard) == 2
    assert [btn.text for btn in kb_uz.keyboard[0]] == ["🔒 Anonim", "🔓 Ochiq"]
    assert [btn.text for btn in kb_uz.keyboard[1]] == ["❌ Bekor qilish"]

    # RU
    kb_ru = get_appeal_type_reply_keyboard(lang="ru")
    assert len(kb_ru.keyboard) == 2
    assert [btn.text for btn in kb_ru.keyboard[0]] == ["🔒 Анонимно", "🔓 Открыто"]
    assert [btn.text for btn in kb_ru.keyboard[1]] == ["❌ Отмена"]

    # EN
    kb_en = get_appeal_type_reply_keyboard(lang="en")
    assert len(kb_en.keyboard) == 2
    assert [btn.text for btn in kb_en.keyboard[0]] == ["🔒 Anonymous", "🔓 Open"]
    assert [btn.text for btn in kb_en.keyboard[1]] == ["❌ Cancel"]
