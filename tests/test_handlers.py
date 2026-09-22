"""Integration tests for aiogram handlers using mock objects."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Chat, Message, User, CallbackQuery, PhotoSize

from bot.config import Settings
from bot.database import Database
from bot.handlers.appeal import (
    handle_appeal_content,
    handle_cancel_appeal,
    handle_start_appeal,
    handle_unhandled_message,
    media_group_collector,
)
from bot.handlers.language import handle_language_callback, handle_change_language_button
from bot.handlers.start import handle_start_command
from bot.states import AppealStates


@pytest.fixture
def mock_config():
    """Fixture providing test configuration."""
    return Settings(
        BOT_TOKEN="123456:TEST_TOKEN",
        RECTOR_CHAT_ID=-100999888777,
        RECTOR_THREAD_ID=15,
        RATE_LIMIT_SECONDS=60,
        DB_PATH="test.db",
    )


@pytest.fixture
async def test_db(tmp_path):
    """Fixture providing initialized SQLite test database."""
    db_file = tmp_path / "test_handler.db"
    db = Database(str(db_file))
    await db.init()
    return db


@pytest.fixture
def memory_storage():
    return MemoryStorage()


def make_fsm_context(storage, bot_id=1, chat_id=12345, user_id=12345):
    key = StorageKey(bot_id=bot_id, chat_id=chat_id, user_id=user_id)
    return FSMContext(storage=storage, key=key)


def make_mock_message(
    text=None,
    user_id=12345,
    chat_id=12345,
    photo=None,
    caption=None,
    media_group_id=None,
    animation=None,
    chat_type="private",
):
    msg = AsyncMock(spec=Message)
    msg.message_id = 99
    msg.text = text
    msg.caption = caption
    msg.photo = photo
    msg.document = None
    msg.voice = None
    msg.video = None
    msg.audio = None
    msg.video_note = None
    msg.animation = animation
    msg.media_group_id = media_group_id

    user = User(id=user_id, is_bot=False, first_name="Student", username="student123")
    chat = Chat(id=chat_id, type=chat_type)
    msg.from_user = user
    msg.chat = chat
    msg.answer = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_start_command_flow(test_db, memory_storage):
    """Test /start command prompts for language."""
    fsm = make_fsm_context(memory_storage)
    msg = make_mock_message(text="/start")

    await handle_start_command(message=msg, state=fsm, db=test_db)

    # Initial state should be cleared and answer called
    assert await fsm.get_state() is None
    assert msg.answer.called
    args, kwargs = msg.answer.call_args
    assert "Tash Tech" in kwargs["text"]
    assert kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_language_callback_selection(test_db, memory_storage):
    """Test selecting language via inline keyboard callback."""
    fsm = make_fsm_context(memory_storage)
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "lang:ru"
    callback.from_user = User(id=12345, is_bot=False, first_name="Student")
    callback.message = make_mock_message()
    callback.answer = AsyncMock()

    await handle_language_callback(callback=callback, state=fsm, db=test_db)

    # Database should now have ru
    assert await test_db.get_user_language(12345) == "ru"
    assert callback.answer.called
    assert callback.message.answer.called


@pytest.mark.asyncio
async def test_appeal_start_and_cancel(test_db, memory_storage, mock_config):
    """Test initiating appeal flow and aborting it via cancel."""
    fsm = make_fsm_context(memory_storage)
    await test_db.set_user_language(12345, "uz")

    # Step 1: User presses Send Appeal
    msg_start = make_mock_message(text="✉️ Murojaat yuborish")
    await handle_start_appeal(message=msg_start, state=fsm, db=test_db, config=mock_config)

    # Should enter waiting_for_appeal state
    assert await fsm.get_state() == AppealStates.waiting_for_appeal.state
    assert "Murojaatingizni yozing" in msg_start.answer.call_args[1]["text"]

    # Step 2: User presses Cancel
    msg_cancel = make_mock_message(text="❌ Bekor qilish")
    await handle_cancel_appeal(message=msg_cancel, state=fsm, db=test_db)

    # State cleared
    assert await fsm.get_state() is None
    assert "bekor qilindi" in msg_cancel.answer.call_args[1]["text"]


@pytest.mark.asyncio
async def test_appeal_submission_text(test_db, memory_storage, mock_config):
    """Test submitting text appeal forwards anonymously to Rector with correct header."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "uz")

    mock_bot = AsyncMock()
    msg = make_mock_message(text="Hurmatli rektor, talabalar turar joyida isitish tizimi ishlamayapti.")

    await handle_appeal_content(
        message=msg,
        state=fsm,
        bot=mock_bot,
        db=test_db,
        config=mock_config,
    )

    # State should be cleared
    assert await fsm.get_state() is None

    # Rector message must be sent
    assert mock_bot.send_message.called
    rector_call_kwargs = mock_bot.send_message.call_args[1]
    assert rector_call_kwargs["chat_id"] == mock_config.rector_chat_id
    assert rector_call_kwargs["message_thread_id"] == mock_config.rector_thread_id
    rector_text = rector_call_kwargs["text"]

    # Header checks
    assert "#TT-0001" in rector_text
    assert "Tash Tech — Anonim Murojaat" in rector_text
    assert "(UTC+5)" in rector_text
    assert "O'zbekcha" in rector_text
    assert "isitish tizimi ishlamayapti" in rector_text

    # Student received screenshot confirmation
    student_reply = msg.answer.call_args[1]["text"]
    assert "✅ Rahmat! Murojaatingiz yuborildi." in student_reply
    assert "🔒 Anonim murojaat — javob va holat kuzatilmaydi." in student_reply


@pytest.mark.asyncio
async def test_appeal_submission_media_photo(test_db, memory_storage, mock_config):
    """Test submitting photo appeal copies anonymously to Rector."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "ru")

    mock_bot = AsyncMock()
    photo_mock = [PhotoSize(file_id="photo123", file_unique_id="u123", width=800, height=600)]
    msg = make_mock_message(photo=photo_mock, caption="Фото расписания")

    await handle_appeal_content(
        message=msg,
        state=fsm,
        bot=mock_bot,
        db=test_db,
        config=mock_config,
    )

    # State cleared
    assert await fsm.get_state() is None

    # Bot should have called copy_message to Rector chat anonymously
    assert mock_bot.copy_message.called
    copy_kwargs = mock_bot.copy_message.call_args[1]
    assert copy_kwargs["chat_id"] == mock_config.rector_chat_id
    assert copy_kwargs["message_thread_id"] == mock_config.rector_thread_id
    assert copy_kwargs["from_chat_id"] == msg.chat.id
    assert copy_kwargs["message_id"] == msg.message_id
    assert "#TT-0001" in copy_kwargs["caption"]
    assert "Русский" in copy_kwargs["caption"]

    # Student received confirmation
    student_reply = msg.answer.call_args[1]["text"]
    assert "✅ Спасибо! Ваше обращение отправлено." in student_reply


@pytest.mark.asyncio
async def test_rate_limit_blocking(test_db, memory_storage, mock_config):
    """Test that cooldown prevents spamming multiple appeals immediately."""
    fsm = make_fsm_context(memory_storage)
    user_id = 99999
    await test_db.set_user_language(user_id, "uz")
    # Simulate recent appeal
    await test_db.update_last_appeal_time(user_id)

    msg = make_mock_message(text="✉️ Murojaat yuborish", user_id=user_id)
    await handle_start_appeal(message=msg, state=fsm, db=test_db, config=mock_config)

    # Must NOT enter state
    assert await fsm.get_state() is None
    # Must give friendly warning
    reply_text = msg.answer.call_args[1]["text"]
    assert "⏳ Iltimos, keyingi murojaatni yuborishdan oldin" in reply_text
    assert "soniya kuting" in reply_text


@pytest.mark.asyncio
async def test_appeal_submission_document(test_db, memory_storage, mock_config):
    """Test submitting document appeal (e.g. PDF)."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "en")

    mock_bot = AsyncMock()
    msg = make_mock_message()
    msg.document = MagicMock()
    msg.caption = "Attached petition PDF"

    await handle_appeal_content(
        message=msg,
        state=fsm,
        bot=mock_bot,
        db=test_db,
        config=mock_config,
    )

    assert await fsm.get_state() is None
    assert mock_bot.copy_message.called
    assert "#TT-0001" in mock_bot.copy_message.call_args[1]["caption"]
    assert "English" in mock_bot.copy_message.call_args[1]["caption"]
    assert "Thank you! Your appeal has been sent." in msg.answer.call_args[1]["text"]


@pytest.mark.asyncio
async def test_appeal_submission_voice_message(test_db, memory_storage, mock_config):
    """Test submitting voice message appeal."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "uz")

    mock_bot = AsyncMock()
    msg = make_mock_message()
    msg.voice = MagicMock()

    await handle_appeal_content(
        message=msg,
        state=fsm,
        bot=mock_bot,
        db=test_db,
        config=mock_config,
    )

    assert await fsm.get_state() is None
    assert mock_bot.copy_message.called
    assert "#TT-0001" in mock_bot.copy_message.call_args[1]["caption"]


@pytest.mark.asyncio
async def test_appeal_submission_long_text(test_db, memory_storage, mock_config):
    """Test text appeal exceeding 4096 characters is sent in multiple chunks."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "uz")

    mock_bot = AsyncMock()
    very_long_text = "Tash Tech talabalari nomidan taklif:\n" + ("A" * 5000)
    msg = make_mock_message(text=very_long_text)

    await handle_appeal_content(
        message=msg,
        state=fsm,
        bot=mock_bot,
        db=test_db,
        config=mock_config,
    )

    assert await fsm.get_state() is None
    # bot.send_message should be called more than once (header + chunks)
    assert mock_bot.send_message.call_count >= 2


@pytest.mark.asyncio
async def test_appeal_submission_long_caption(test_db, memory_storage, mock_config):
    """Test photo appeal with caption > 1024 characters sends header first then copies message."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "uz")

    mock_bot = AsyncMock()
    photo_mock = [PhotoSize(file_id="p1", file_unique_id="u1", width=100, height=100)]
    long_caption = "B" * 1050
    msg = make_mock_message(photo=photo_mock, caption=long_caption)

    await handle_appeal_content(
        message=msg,
        state=fsm,
        bot=mock_bot,
        db=test_db,
        config=mock_config,
    )

    assert await fsm.get_state() is None
    # Should send header separately
    assert mock_bot.send_message.called
    assert "#TT-0001" in mock_bot.send_message.call_args[1]["text"]
    # And copy message without custom caption
    assert mock_bot.copy_message.called


@pytest.mark.asyncio
async def test_appeal_unsupported_content_type(test_db, memory_storage, mock_config):
    """Test sending sticker or unsupported content keeps state and shows warning."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "uz")

    mock_bot = AsyncMock()
    msg = make_mock_message()  # text and all media are None

    await handle_appeal_content(
        message=msg,
        state=fsm,
        bot=mock_bot,
        db=test_db,
        config=mock_config,
    )

    # State should remain waiting_for_appeal so student can retry
    assert await fsm.get_state() == AppealStates.waiting_for_appeal.state
    # Bot did not forward to rector
    assert not mock_bot.send_message.called
    assert not mock_bot.copy_message.called
    # Sent warning
    assert "Faqat matn, rasm, hujjat" in msg.answer.call_args[1]["text"]


@pytest.mark.asyncio
async def test_change_language_button_during_appeal(test_db, memory_storage, mock_config):
    """Test pressing Change Language button while writing appeal resets state and prompts language."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "uz")

    mock_bot = AsyncMock()
    msg = make_mock_message(text="🌐 Tilni o'zgartirish")

    await handle_appeal_content(
        message=msg,
        state=fsm,
        bot=mock_bot,
        db=test_db,
        config=mock_config,
    )

    # State cleared
    assert await fsm.get_state() is None
    assert "tilni tanlang" in msg.answer.call_args[1]["text"]


@pytest.mark.asyncio
async def test_html_injection_prevention(test_db, memory_storage, mock_config):
    """Test that malicious HTML tags in student message are escaped and do not break Telegram HTML."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "uz")

    mock_bot = AsyncMock()
    malicious_text = "<script>alert('hack')</script> & <invalid_tag>bold</invalid_tag>"
    msg = make_mock_message(text=malicious_text)

    await handle_appeal_content(
        message=msg,
        state=fsm,
        bot=mock_bot,
        db=test_db,
        config=mock_config,
    )

    rector_text = mock_bot.send_message.call_args[1]["text"]
    assert "<script>" not in rector_text
    assert "&lt;script&gt;" in rector_text
    assert "&lt;invalid_tag&gt;" in rector_text


@pytest.mark.asyncio
async def test_media_group_album_submission(test_db, memory_storage, mock_config):
    """Test submitting a media album (group of multiple photos) results in a single appeal."""
    import asyncio
    media_group_collector.delay_seconds = 0.05

    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "uz")

    mock_bot = AsyncMock()
    photo1 = [PhotoSize(file_id="p1", file_unique_id="u1", width=100, height=100)]
    photo2 = [PhotoSize(file_id="p2", file_unique_id="u2", width=100, height=100)]

    msg1 = make_mock_message(photo=photo1, caption="Album caption", media_group_id="group_test_99")
    msg1.message_id = 201
    msg2 = make_mock_message(photo=photo2, media_group_id="group_test_99")
    msg2.message_id = 202

    # Run both message arrivals concurrently
    await asyncio.gather(
        handle_appeal_content(msg1, fsm, mock_bot, test_db, mock_config),
        handle_appeal_content(msg2, fsm, mock_bot, test_db, mock_config),
    )

    # State cleared
    assert await fsm.get_state() is None

    # Database must have exactly ONE appeal
    assert await test_db.get_appeal_count() == 1

    # Header sent with caption
    assert mock_bot.send_message.called
    assert "Album caption" in mock_bot.send_message.call_args[1]["text"]

    # Media messages copied together
    assert mock_bot.copy_messages.called
    copy_call_kwargs = mock_bot.copy_messages.call_args[1]
    assert 201 in copy_call_kwargs["message_ids"]
    assert 202 in copy_call_kwargs["message_ids"]

    # Student received exactly ONE confirmation (on leader message)
    assert msg1.answer.called
    assert "✅ Rahmat! Murojaatingiz yuborildi." in msg1.answer.call_args[1]["text"]
    assert not msg2.answer.called


@pytest.mark.asyncio
async def test_animation_gif_submission(test_db, memory_storage, mock_config):
    """Test submitting GIF/animation is supported and forwarded to Rector."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "en")

    mock_bot = AsyncMock()
    msg = make_mock_message(animation=MagicMock(), caption="GIF demonstration")

    await handle_appeal_content(msg, fsm, mock_bot, test_db, mock_config)

    assert await fsm.get_state() is None
    assert mock_bot.copy_message.called
    assert "#TT-0001" in mock_bot.copy_message.call_args[1]["caption"]
    assert "GIF demonstration" in mock_bot.copy_message.call_args[1]["caption"]


@pytest.mark.asyncio
async def test_unhandled_message_outside_appeal(test_db):
    """Test message received outside of appeal state replies with main menu."""
    await test_db.set_user_language(12345, "uz")
    msg = make_mock_message(text="Tasodifiy xabar")

    await handle_unhandled_message(message=msg, db=test_db)

    assert msg.answer.called
    answer_text = msg.answer.call_args[1]["text"]
    assert "Asosiy menyu" in answer_text
    assert msg.answer.call_args[1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_photo_with_extreme_long_caption(test_db, memory_storage, mock_config):
    """Test photo with caption > 1024 chars delivers full text in message and copies media cleanly."""
    fsm = make_fsm_context(memory_storage)
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await test_db.set_user_language(12345, "uz")

    mock_bot = AsyncMock()
    photo_mock = [PhotoSize(file_id="p1", file_unique_id="u1", width=100, height=100)]
    long_caption = "Long explanation " * 70  # ~1190 chars
    msg = make_mock_message(photo=photo_mock, caption=long_caption)

    await handle_appeal_content(msg, fsm, mock_bot, test_db, mock_config)

    assert await fsm.get_state() is None
    # Header and full caption must be sent via send_message
    assert mock_bot.send_message.called
    assert "Long explanation" in mock_bot.send_message.call_args[1]["text"]
    # Media must be copied with empty caption
    assert mock_bot.copy_message.called
    assert mock_bot.copy_message.call_args[1]["caption"] == ""


