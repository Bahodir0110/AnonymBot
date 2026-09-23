"""Unit tests for utility functions."""

from datetime import datetime, timezone, timedelta
from bot.utils import (
    build_rector_header,
    escape_html,
    format_reference_id,
    format_tashkent_time,
    get_tashkent_now,
    split_text_chunks,
)


def test_format_reference_id():
    """Verify sequential reference IDs format to #TT-XXXX format."""
    assert format_reference_id(1) == "#TT-0001"
    assert format_reference_id(42) == "#TT-0042"
    assert format_reference_id(999) == "#TT-0999"
    assert format_reference_id(1234) == "#TT-1234"
    assert format_reference_id(10000) == "#TT-10000"


def test_escape_html():
    """Verify HTML escaping for special characters."""
    raw = 'Hello <world> & "students" \''
    escaped = escape_html(raw)
    assert "<" not in escaped or "&lt;" in escaped
    assert ">" not in escaped or "&gt;" in escaped
    assert "&amp;" in escaped
    assert escape_html("") == ""


def test_format_tashkent_time():
    """Verify Tashkent time format string contains UTC+5 and valid datetime format."""
    dt = datetime(2026, 9, 22, 14, 15, 30, tzinfo=timezone(timedelta(hours=5)))
    result = format_tashkent_time(dt)
    assert result == "2026-09-22 14:15:30 (UTC+5)"

    now_result = format_tashkent_time()
    assert "(UTC+5)" in now_result


def test_get_tashkent_now():
    """Verify get_tashkent_now returns valid datetime."""
    now = get_tashkent_now()
    assert isinstance(now, datetime)


def test_build_rector_header():
    """Verify rector notification header format for anonymous appeals."""
    header_uz = build_rector_header(
        reference_id="#TT-0001",
        timestamp_str="2026-09-22 14:15:00 (UTC+5)",
        language_name="O'zbekcha",
        is_anonymous=True,
        language_code="uz",
    )
    assert "📬 <b>Yangi anonim murojaat</b>" in header_uz
    assert "🆔 <b>Murojaat ID:</b> <code>#TT-0001</code>" in header_uz
    assert "🔒 <b>Turi:</b> Anonim" in header_uz
    assert "📅 <b>Sana:</b> 2026-09-22 14:15:00 (UTC+5)" in header_uz
    assert "🌐 <b>Til:</b> O'zbekcha" in header_uz

    header_ru = build_rector_header(
        reference_id="#TT-0002",
        timestamp_str="2026-09-22 14:15:00 (UTC+5)",
        language_name="Русский",
        is_anonymous=True,
        language_code="ru",
    )
    assert "📬 <b>Новое анонимное обращение</b>" in header_ru

    header_en = build_rector_header(
        reference_id="#TT-0003",
        timestamp_str="2026-09-22 14:15:00 (UTC+5)",
        language_name="English",
        is_anonymous=True,
        language_code="en",
    )
    assert "📬 <b>New Anonymous Appeal</b>" in header_en


def test_build_rector_header_open():
    """Verify rector notification header format for open appeals."""
    header_uz = build_rector_header(
        reference_id="#TT-0005",
        timestamp_str="2026-09-22 14:15:00 (UTC+5)",
        language_name="O'zbekcha",
        is_anonymous=False,
        full_name="Alisher Navoiy",
        contact_info="+998901234567",
        language_code="uz",
        telegram_username="alisher_navoiy",
    )
    assert "📬 <b>Yangi ochiq murojaat</b>" in header_uz
    assert "🆔 <b>Murojaat ID:</b> <code>#TT-0005</code>" in header_uz
    assert "🔓 <b>Turi:</b> Ochiq (Oshkora)" in header_uz
    assert "👤 <b>Talaba / F.I.Sh.:</b> Alisher Navoiy" in header_uz
    assert "📞 <b>Aloqa:</b> +998901234567" in header_uz
    assert "✈️ <b>Telegram:</b> @alisher_navoiy" in header_uz
    assert "📅 <b>Sana:</b> 2026-09-22 14:15:00 (UTC+5)" in header_uz
    assert "🌐 <b>Til:</b> O'zbekcha" in header_uz

    header_ru = build_rector_header(
        reference_id="#TT-0006",
        timestamp_str="2026-09-22 14:15:00 (UTC+5)",
        language_name="Русский",
        is_anonymous=False,
        full_name="Иван Иванов",
        contact_info="ivan@example.com",
        language_code="ru",
        telegram_username=None,
    )
    assert "📬 <b>Новое открытое обращение</b>" in header_ru
    assert "Иван Иванов" in header_ru
    assert "ivan@example.com" in header_ru
    assert "✈️ <b>Telegram:</b> <i>Не указан</i>" in header_ru

    header_en = build_rector_header(
        reference_id="#TT-0007",
        timestamp_str="2026-09-22 14:15:00 (UTC+5)",
        language_name="English",
        is_anonymous=False,
        full_name="John Doe",
        contact_info="+1234567890",
        language_code="en",
        telegram_username="@johndoe",
    )
    assert "📬 <b>New Open Appeal</b>" in header_en
    assert "✈️ <b>Telegram:</b> @johndoe" in header_en


def test_split_text_chunks():
    """Verify long text is safely split into chunks."""
    short_text = "Short message"
    assert split_text_chunks(short_text, max_chunk_size=50) == [short_text]

    long_text = "Line 1\n" + ("a" * 60) + "\nLine 3\n" + ("b" * 60)
    chunks = split_text_chunks(long_text, max_chunk_size=50)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 70


def test_split_text_chunks_preserves_html_entities():
    """Verify split_text_chunks does not cut an HTML entity like &amp; in half."""
    text = ("A" * 3998) + "&amp;" + ("B" * 50)
    chunks = split_text_chunks(text, max_chunk_size=4000)
    assert len(chunks) == 2
    # Chunk 0 must not end with an incomplete entity like &a
    assert not chunks[0].endswith("&a")
    assert not chunks[0].endswith("&")
    # Chunk 1 must start with the complete entity &amp;
    assert chunks[1].startswith("&amp;")

