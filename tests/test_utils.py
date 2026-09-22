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
    """Verify rector notification header format."""
    header = build_rector_header(
        reference_id="#TT-0001",
        timestamp_str="2026-09-22 14:15:00 (UTC+5)",
        language_name="O'zbekcha",
    )
    assert "Tash Tech — Anonim Murojaat" in header
    assert "#TT-0001" in header
    assert "2026-09-22 14:15:00 (UTC+5)" in header
    assert "O'zbekcha" in header


def test_split_text_chunks():
    """Verify long text is safely split into chunks."""
    short_text = "Short message"
    assert split_text_chunks(short_text, max_chunk_size=50) == [short_text]

    long_text = "Line 1\n" + ("a" * 60) + "\nLine 3\n" + ("b" * 60)
    chunks = split_text_chunks(long_text, max_chunk_size=50)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 70
