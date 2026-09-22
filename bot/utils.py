"""Utility functions for time, formatting, and reference IDs."""

import html
from datetime import datetime, timezone, timedelta
from typing import List, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore


def get_tashkent_now(tz_name: str = "Asia/Tashkent") -> datetime:
    """Return current datetime in Tashkent (UTC+5).

    Falls back to a fixed UTC+5 offset if ZoneInfo is unavailable or tzdata is missing.
    """
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo(tz_name))
        except Exception:
            pass
    # Tashkent is UTC+5 year-round
    tashkent_tz = timezone(timedelta(hours=5))
    return datetime.now(tashkent_tz)


def format_tashkent_time(dt: datetime = None, tz_name: str = "Asia/Tashkent") -> str:
    """Format current or given time as YYYY-MM-DD HH:MM:SS (UTC+5)."""
    if dt is None:
        dt = get_tashkent_now(tz_name)
    return dt.strftime("%Y-%m-%d %H:%M:%S (UTC+5)")


def format_reference_id(sequence_num: int) -> str:
    """Format sequential number into #TT-XXXX reference ID."""
    return f"#TT-{sequence_num:04d}"


def escape_html(text: str) -> str:
    """Escape special HTML characters (&, <, >) for Telegram HTML parse mode while keeping quotes."""
    if not text:
        return ""
    # quote=False preserves single and double quotes so Uzbek latin names like O'zbekcha aren't mangled to O&#x27;zbekcha
    return html.escape(text, quote=False)


def build_rector_header(
    reference_id: str,
    timestamp_str: str,
    language_name: str,
    is_anonymous: bool = True,
    full_name: Optional[str] = None,
    contact_info: Optional[str] = None,
    language_code: str = "uz",
) -> str:
    """Construct standard notification header for Rector delivery."""
    if is_anonymous:
        title_map = {
            "uz": "📬 <b>Yangi anonim murojaat</b>",
            "ru": "📬 <b>Новое анонимное обращение</b>",
            "en": "📬 <b>New Anonymous Appeal</b>",
        }
        title = title_map.get(language_code, title_map["uz"])
        return (
            f"{title}\n"
            f"🆔 <b>Murojaat ID:</b> <code>{escape_html(reference_id)}</code>\n"
            "🔒 <b>Turi:</b> Anonim\n"
            f"📅 <b>Sana:</b> {escape_html(timestamp_str)}\n"
            f"🌐 <b>Til:</b> {escape_html(language_name)}"
        )
    else:
        title_map = {
            "uz": "📬 <b>Yangi ochiq murojaat</b>",
            "ru": "📬 <b>Новое открытое обращение</b>",
            "en": "📬 <b>New Open Appeal</b>",
        }
        title = title_map.get(language_code, title_map["uz"])
        return (
            f"{title}\n"
            f"🆔 <b>Murojaat ID:</b> <code>{escape_html(reference_id)}</code>\n"
            "🔓 <b>Turi:</b> Ochiq (Oshkora)\n"
            f"👤 <b>Talaba / F.I.Sh.:</b> {escape_html(full_name or '')}\n"
            f"📞 <b>Aloqa:</b> {escape_html(contact_info or '')}\n"
            f"📅 <b>Sana:</b> {escape_html(timestamp_str)}\n"
            f"🌐 <b>Til:</b> {escape_html(language_name)}"
        )


def split_text_chunks(text: str, max_chunk_size: int = 4000) -> List[str]:
    """Split long text into chunks that fit within Telegram's limits without breaking HTML entities."""
    if len(text) <= max_chunk_size:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_chunk_size:
            chunks.append(text)
            break
        # Look for last newline within max_chunk_size
        split_idx = text.rfind("\n", 0, max_chunk_size)
        if split_idx == -1 or split_idx < max_chunk_size // 2:
            # Look for last space
            split_idx = text.rfind(" ", 0, max_chunk_size)
        if split_idx == -1 or split_idx < max_chunk_size // 2:
            split_idx = max_chunk_size

        # Guard against splitting in the middle of an HTML entity like &amp;, &#x27;, &lt;, &gt;
        amp_idx = text.rfind("&", max(0, split_idx - 10), split_idx)
        if amp_idx != -1:
            semicolon_idx = text.find(";", amp_idx, split_idx + 10)
            if semicolon_idx != -1 and semicolon_idx >= split_idx:
                split_idx = amp_idx

        chunk = text[:split_idx].strip()
        if not chunk:
            chunk = text[:max_chunk_size]
            split_idx = max_chunk_size

        chunks.append(chunk)
        text = text[split_idx:].lstrip()
    return chunks
