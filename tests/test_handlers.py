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
    handle_choose_appeal_type,
    handle_contact_input,
    handle_name_input,
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
    contact=None,
    chat_type="private",
    username="student123",
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
    msg.contact = contact
    msg.media_group_id = media_group_id

    user = User(id=user_id, is_bot=False, first_name="Student", username=username)
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

    # Should enter waiting_for_type state
    assert await fsm.get_state() == AppealStates.waiting_for_type.state
    assert "Murojaat turini tanlang" in msg_start.answer.call_args[1]["text"]

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
    await fsm.update_data(is_anonymous=True)
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
    assert "📬 <b>Yangi anonim murojaat</b>" in rector_text
    assert "🔒 <b>Turi:</b> Anonim" in rector_text
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

    # Student received exactly ONE confirmation across the media album
    answered_msg = msg1 if msg1.answer.called else msg2
    unanswered_msg = msg2 if msg1.answer.called else msg1
    assert answered_msg.answer.called
    assert "✅ Rahmat! Murojaatingiz yuborildi." in answered_msg.answer.call_args[1]["text"]
    assert not unanswered_msg.answer.called


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


@pytest.mark.asyncio
async def test_anonymous_flow_complete(test_db, memory_storage, mock_config):
    """Test full flow: start -> choose anonymous -> write appeal -> anonymous delivery to rector."""
    fsm = make_fsm_context(memory_storage)
    user_id = 7771
    await test_db.set_user_language(user_id, "uz")

    # Step 1: Start appeal
    msg_start = make_mock_message(text="✉️ Murojaat yuborish", user_id=user_id)
    await handle_start_appeal(msg_start, fsm, test_db, mock_config)
    assert await fsm.get_state() == AppealStates.waiting_for_type.state
    assert "🔐 Murojaat turini tanlang:" in msg_start.answer.call_args[1]["text"]

    # Step 2: Choose Anonymous
    msg_type = make_mock_message(text="🔒 Anonim", user_id=user_id)
    await handle_choose_appeal_type(msg_type, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_appeal.state
    assert "✍️ Murojaatingizni yozing:" in msg_type.answer.call_args[1]["text"]

    # Step 3: Submit appeal content
    mock_bot = AsyncMock()
    msg_content = make_mock_message(text="Anonim taklif matni.", user_id=user_id)
    await handle_appeal_content(msg_content, fsm, mock_bot, test_db, mock_config)

    assert await fsm.get_state() is None
    assert mock_bot.send_message.called
    rector_text = mock_bot.send_message.call_args[1]["text"]
    assert "📬 <b>Yangi anonim murojaat</b>" in rector_text
    assert "🔒 <b>Turi:</b> Anonim" in rector_text
    assert "Anonim taklif matni." in rector_text
    assert "Talaba / F.I.Sh." not in rector_text

    # Student confirmation
    student_confirm = msg_content.answer.call_args[1]["text"]
    assert "✅ Rahmat! Murojaatingiz yuborildi." in student_confirm
    assert "🔒 Anonim murojaat — javob va holat kuzatilmaydi." in student_confirm

    # DB verify
    appeal = await test_db.get_appeal(1)
    assert appeal["is_anonymous"] == 1
    assert appeal["full_name"] is None
    assert appeal["contact_info"] is None


@pytest.mark.asyncio
async def test_open_flow_complete_uz(test_db, memory_storage, mock_config):
    """Test full flow for open appeal in Uzbek: start -> choose open -> name -> contact -> write appeal."""
    fsm = make_fsm_context(memory_storage)
    user_id = 7772
    await test_db.set_user_language(user_id, "uz")

    # Step 1: Start appeal
    msg_start = make_mock_message(text="✉️ Murojaat yuborish", user_id=user_id)
    await handle_start_appeal(msg_start, fsm, test_db, mock_config)
    assert await fsm.get_state() == AppealStates.waiting_for_type.state

    # Step 2: Choose Open
    msg_type = make_mock_message(text="🔓 Ochiq", user_id=user_id)
    await handle_choose_appeal_type(msg_type, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_name.state
    assert "👤 Ism-familiyangizni kiriting:" in msg_type.answer.call_args[1]["text"]

    # Step 3: Enter Full Name
    msg_name = make_mock_message(text="Anvar Qodirov", user_id=user_id)
    await handle_name_input(msg_name, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_contact.state
    assert "📞 Bog'lanish uchun kontakt" in msg_name.answer.call_args[1]["text"]

    # Step 4: Enter Contact Info
    msg_contact = make_mock_message(text="+998901112233", user_id=user_id)
    await handle_contact_input(msg_contact, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_appeal.state
    assert "✍️ Murojaatingizni yozing:" in msg_contact.answer.call_args[1]["text"]

    # Step 5: Submit Appeal Content
    mock_bot = AsyncMock()
    msg_content = make_mock_message(text="Kutubxonada yangi kitoblar kerak.", user_id=user_id)
    await handle_appeal_content(msg_content, fsm, mock_bot, test_db, mock_config)

    assert await fsm.get_state() is None
    assert mock_bot.send_message.called
    rector_text = mock_bot.send_message.call_args[1]["text"]
    assert "📬 <b>Yangi ochiq murojaat</b>" in rector_text
    assert "🔓 <b>Turi:</b> Ochiq (Oshkora)" in rector_text
    assert "👤 <b>Talaba / F.I.Sh.:</b> Anvar Qodirov" in rector_text
    assert "📞 <b>Aloqa:</b> +998901112233" in rector_text
    assert "✈️ <b>Telegram:</b> @student123" in rector_text
    assert "Kutubxonada yangi kitoblar kerak." in rector_text

    # Student confirmation
    student_confirm = msg_content.answer.call_args[1]["text"]
    assert "✅ Rahmat! Murojaatingiz yuborildi." in student_confirm
    assert "🔓 Ochiq murojaat — ma'lumotlaringiz ijrochi direktorga yetkazildi." in student_confirm

    # DB record
    appeal = await test_db.get_appeal(1)
    assert appeal["is_anonymous"] == 0
    assert appeal["full_name"] == "Anvar Qodirov"
    assert appeal["contact_info"] == "+998901112233"
    assert appeal["telegram_username"] == "student123"


@pytest.mark.asyncio
async def test_open_flow_complete_ru(test_db, memory_storage, mock_config):
    """Test full flow for open appeal in Russian."""
    fsm = make_fsm_context(memory_storage)
    user_id = 7773
    await test_db.set_user_language(user_id, "ru")

    # Step 1: Start appeal
    msg_start = make_mock_message(text="✉️ Отправить обращение", user_id=user_id)
    await handle_start_appeal(msg_start, fsm, test_db, mock_config)
    assert await fsm.get_state() == AppealStates.waiting_for_type.state
    assert "🔐 Выберите тип обращения:" in msg_start.answer.call_args[1]["text"]

    # Step 2: Choose Open
    msg_type = make_mock_message(text="🔓 Открыто", user_id=user_id)
    await handle_choose_appeal_type(msg_type, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_name.state
    assert "👤 Как вас зовут?" in msg_type.answer.call_args[1]["text"]

    # Step 3: Enter Name
    msg_name = make_mock_message(text="Алексей Смирнов", user_id=user_id)
    await handle_name_input(msg_name, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_contact.state
    assert "📞 Укажите контакт для связи" in msg_name.answer.call_args[1]["text"]

    # Step 4: Enter Contact
    msg_contact = make_mock_message(text="alex@example.com", user_id=user_id)
    await handle_contact_input(msg_contact, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_appeal.state
    assert "✍️ Опишите ваше обращение:" in msg_contact.answer.call_args[1]["text"]

    # Step 5: Submit Appeal
    mock_bot = AsyncMock()
    msg_content = make_mock_message(text="Вопрос по общежитию.", user_id=user_id, username=None)
    await handle_appeal_content(msg_content, fsm, mock_bot, test_db, mock_config)

    assert await fsm.get_state() is None
    assert mock_bot.send_message.called
    rector_text = mock_bot.send_message.call_args[1]["text"]
    assert "📬 <b>Новое открытое обращение</b>" in rector_text
    assert "🔓 <b>Turi:</b> Ochiq (Oshkora)" in rector_text
    assert "👤 <b>Talaba / F.I.Sh.:</b> Алексей Смирнов" in rector_text
    assert "📞 <b>Aloqa:</b> alex@example.com" in rector_text
    assert "✈️ <b>Telegram:</b> <i>Не указан</i>" in rector_text

    student_confirm = msg_content.answer.call_args[1]["text"]
    assert "✅ Спасибо! Ваше обращение отправлено." in student_confirm
    assert "🔓 Открытое обращение — ваши данные переданы исполнительному директору." in student_confirm


@pytest.mark.asyncio
async def test_open_flow_complete_en(test_db, memory_storage, mock_config):
    """Test full flow for open appeal in English."""
    fsm = make_fsm_context(memory_storage)
    user_id = 7774
    await test_db.set_user_language(user_id, "en")

    # Step 1: Start appeal
    msg_start = make_mock_message(text="✉️ Send appeal", user_id=user_id)
    await handle_start_appeal(msg_start, fsm, test_db, mock_config)
    assert await fsm.get_state() == AppealStates.waiting_for_type.state
    assert "🔐 Choose appeal type:" in msg_start.answer.call_args[1]["text"]

    # Step 2: Choose Open
    msg_type = make_mock_message(text="🔓 Open", user_id=user_id)
    await handle_choose_appeal_type(msg_type, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_name.state
    assert "👤 What is your full name?" in msg_type.answer.call_args[1]["text"]

    # Step 3: Enter Name
    msg_name = make_mock_message(text="Alice Smith", user_id=user_id)
    await handle_name_input(msg_name, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_contact.state
    assert "📞 Enter contact info" in msg_name.answer.call_args[1]["text"]

    # Step 4: Enter Contact
    msg_contact = make_mock_message(text="+1234567890", user_id=user_id)
    await handle_contact_input(msg_contact, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_appeal.state
    assert "✍️ Write your appeal:" in msg_contact.answer.call_args[1]["text"]

    # Step 5: Submit Appeal
    mock_bot = AsyncMock()
    msg_content = make_mock_message(text="Request for cafeteria improvements.", user_id=user_id, username="alicesmith")
    await handle_appeal_content(msg_content, fsm, mock_bot, test_db, mock_config)

    assert await fsm.get_state() is None
    assert mock_bot.send_message.called
    rector_text = mock_bot.send_message.call_args[1]["text"]
    assert "📬 <b>New Open Appeal</b>" in rector_text
    assert "Alice Smith" in rector_text
    assert "+1234567890" in rector_text
    assert "✈️ <b>Telegram:</b> @alicesmith" in rector_text

    student_confirm = msg_content.answer.call_args[1]["text"]
    assert "✅ Thank you! Your appeal has been sent." in student_confirm
    assert "🔓 Open appeal — your contact details were delivered to the CEO." in student_confirm


@pytest.mark.asyncio
async def test_open_appeal_with_photo(test_db, memory_storage, mock_config):
    """Test submitting open appeal with photo attachment includes student identity and username in caption."""
    fsm = make_fsm_context(memory_storage)
    user_id = 7775
    await test_db.set_user_language(user_id, "uz")
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await fsm.update_data(is_anonymous=False, full_name="Sardor Aliyev", contact_info="+998991234567")

    mock_bot = AsyncMock()
    photo_mock = [PhotoSize(file_id="photo999", file_unique_id="u999", width=800, height=600)]
    msg = make_mock_message(photo=photo_mock, caption="Bino fotosi", user_id=user_id, username="sardor_ali")

    await handle_appeal_content(msg, fsm, mock_bot, test_db, mock_config)

    assert await fsm.get_state() is None
    assert mock_bot.copy_message.called
    caption = mock_bot.copy_message.call_args[1]["caption"]
    assert "📬 <b>Yangi ochiq murojaat</b>" in caption
    assert "Sardor Aliyev" in caption
    assert "+998991234567" in caption
    assert "✈️ <b>Telegram:</b> @sardor_ali" in caption
    assert "Bino fotosi" in caption

    student_reply = msg.answer.call_args[1]["text"]
    assert "🔓 Ochiq murojaat — ma'lumotlaringiz ijrochi direktorga yetkazildi." in student_reply


@pytest.mark.asyncio
async def test_cancel_at_each_state(test_db, memory_storage):
    """Verify cancel button clears state from waiting_for_type, waiting_for_name, and waiting_for_contact."""
    states_to_test = [
        AppealStates.waiting_for_type,
        AppealStates.waiting_for_name,
        AppealStates.waiting_for_contact,
        AppealStates.waiting_for_appeal,
    ]
    for st in states_to_test:
        fsm = make_fsm_context(memory_storage)
        await fsm.set_state(st)
        msg_cancel = make_mock_message(text="❌ Bekor qilish")
        await handle_cancel_appeal(msg_cancel, fsm, test_db)
        assert await fsm.get_state() is None
        assert "bekor qilindi" in msg_cancel.answer.call_args[1]["text"]


@pytest.mark.asyncio
async def test_invalid_inputs_in_open_flow(test_db, memory_storage):
    """Verify validation when user submits invalid name or contact info."""
    fsm = make_fsm_context(memory_storage)
    user_id = 8888
    await test_db.set_user_language(user_id, "uz")

    # Invalid name (empty or whitespace)
    await fsm.set_state(AppealStates.waiting_for_name)
    msg_empty_name = make_mock_message(text="   ", user_id=user_id)
    await handle_name_input(msg_empty_name, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_name.state
    assert "ism-familiyangizni matn ko'rinishida kiriting" in msg_empty_name.answer.call_args[1]["text"]

    # Invalid contact (empty)
    await fsm.set_state(AppealStates.waiting_for_contact)
    msg_empty_contact = make_mock_message(text="   ", user_id=user_id)
    await handle_contact_input(msg_empty_contact, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_contact.state
    assert "bog'lanish kontaktini matn ko'rinishida kiriting" in msg_empty_contact.answer.call_args[1]["text"]

    # Invalid appeal type selection
    await fsm.set_state(AppealStates.waiting_for_type)
    msg_invalid_type = make_mock_message(text="Tasodifiy javob", user_id=user_id)
    await handle_choose_appeal_type(msg_invalid_type, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_type.state
    assert "🔐 Murojaat turini tanlang:" in msg_invalid_type.answer.call_args[1]["text"]


@pytest.mark.asyncio
async def test_cross_appeal_type_rate_limiting(test_db, memory_storage, mock_config):
    """Verify cooldown applies across appeal types: submitting open blocks anonymous and vice versa."""
    fsm = make_fsm_context(memory_storage)
    user_id = 9911
    await test_db.set_user_language(user_id, "uz")

    # Flow 1: Submit Open appeal
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await fsm.update_data(is_anonymous=False, full_name="Vali Aliyev", contact_info="+998901234567")
    mock_bot = AsyncMock()
    msg1 = make_mock_message(text="Ochiq murojaat", user_id=user_id)
    await handle_appeal_content(msg1, fsm, mock_bot, test_db, mock_config)

    # State cleared
    assert await fsm.get_state() is None

    # Immediate attempt to start Anonymous appeal must be blocked by rate limit
    msg2 = make_mock_message(text="✉️ Murojaat yuborish", user_id=user_id)
    await handle_start_appeal(msg2, fsm, test_db, mock_config)
    assert await fsm.get_state() is None
    assert "⏳ Iltimos, keyingi murojaatni yuborishdan oldin" in msg2.answer.call_args[1]["text"]


@pytest.mark.asyncio
async def test_telegram_contact_share_input(test_db, memory_storage):
    """Verify student can provide contact info via Telegram contact card."""
    fsm = make_fsm_context(memory_storage)
    user_id = 9922
    await test_db.set_user_language(user_id, "uz")
    await fsm.set_state(AppealStates.waiting_for_contact)

    mock_contact = MagicMock()
    mock_contact.phone_number = "+998939998877"
    msg = make_mock_message(text=None, contact=mock_contact, user_id=user_id)

    await handle_contact_input(msg, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_appeal.state
    data = await fsm.get_data()
    assert data["contact_info"] == "+998939998877"


@pytest.mark.asyncio
async def test_change_language_shortcuts_in_all_states(test_db, memory_storage):
    """Verify pressing change language from any appeal state clears state and prompts language selection."""
    for st in [AppealStates.waiting_for_type, AppealStates.waiting_for_name, AppealStates.waiting_for_contact]:
        fsm = make_fsm_context(memory_storage)
        await fsm.set_state(st)
        user_id = 9933
        await test_db.set_user_language(user_id, "uz")

        msg_lang = make_mock_message(text="🌐 Tilni o'zgartirish", user_id=user_id)
        if st == AppealStates.waiting_for_type:
            await handle_choose_appeal_type(msg_lang, fsm, test_db)
        elif st == AppealStates.waiting_for_name:
            await handle_name_input(msg_lang, fsm, test_db)
        elif st == AppealStates.waiting_for_contact:
            await handle_contact_input(msg_lang, fsm, test_db)

        assert await fsm.get_state() is None
        assert "kerakli tilni tanlang" in msg_lang.answer.call_args[1]["text"]


@pytest.mark.asyncio
async def test_open_appeal_media_group_album(test_db, memory_storage, mock_config):
    """Verify album of photos in open appeal includes student identity in rector delivery."""
    media_group_collector.delay_seconds = 0.05

    fsm = make_fsm_context(memory_storage)
    user_id = 9944
    await test_db.set_user_language(user_id, "uz")
    await fsm.set_state(AppealStates.waiting_for_appeal)
    await fsm.update_data(is_anonymous=False, full_name="Zafar Ergashev", contact_info="+998971112233")

    mock_bot = AsyncMock()
    # Leader and follower messages
    msg1 = make_mock_message(
        photo=[PhotoSize(file_id="p1", file_unique_id="u1", width=100, height=100)],
        caption="Laboratoriya rasmlari",
        media_group_id="group_open_1",
        user_id=user_id,
    )
    msg1.message_id = 301
    msg2 = make_mock_message(
        photo=[PhotoSize(file_id="p2", file_unique_id="u2", width=100, height=100)],
        media_group_id="group_open_1",
        user_id=user_id,
    )
    msg2.message_id = 302

    # Concurrently receive both messages belonging to the media album
    import asyncio
    await asyncio.gather(
        handle_appeal_content(msg1, fsm, mock_bot, test_db, mock_config),
        handle_appeal_content(msg2, fsm, mock_bot, test_db, mock_config),
    )

    assert await fsm.get_state() is None
    # Rector header sent
    assert mock_bot.send_message.called
    rector_header = mock_bot.send_message.call_args[1]["text"]
    assert "📬 <b>Yangi ochiq murojaat</b>" in rector_header
    assert "Zafar Ergashev" in rector_header
    assert "+998971112233" in rector_header
    assert "✈️ <b>Telegram:</b> @student123" in rector_header
    assert "Laboratoriya rasmlari" in rector_header

    # Student confirmation sent to whichever message was processed as leader
    answered_msg = msg1 if msg1.answer.called else msg2
    assert answered_msg.answer.called
    assert "🔓 Ochiq murojaat — ma'lumotlaringiz ijrochi direktorga yetkazildi." in answered_msg.answer.call_args[1]["text"]


@pytest.mark.asyncio
async def test_long_name_and_contact_truncation(test_db, memory_storage, mock_config):
    """Verify name and contact inputs > 150 chars are bounded to prevent header overflow / DoS."""
    fsm = make_fsm_context(memory_storage)
    user_id = 9955
    await test_db.set_user_language(user_id, "uz")

    # Name input > 200 chars
    await fsm.set_state(AppealStates.waiting_for_name)
    super_long_name = "Abdurahmon " * 30  # ~330 chars
    msg_name = make_mock_message(text=super_long_name, user_id=user_id)
    await handle_name_input(msg_name, fsm, test_db)
    data = await fsm.get_data()
    assert len(data["full_name"]) == 150

    # Contact input > 200 chars
    await fsm.set_state(AppealStates.waiting_for_contact)
    super_long_contact = "+998901234567 " * 20  # ~300 chars
    msg_contact = make_mock_message(text=super_long_contact, user_id=user_id)
    await handle_contact_input(msg_contact, fsm, test_db)
    data = await fsm.get_data()
    assert len(data["contact_info"]) == 150

    # Submit content and ensure header delivers safely
    mock_bot = AsyncMock()
    msg_content = make_mock_message(text="Qisqa matn", user_id=user_id)
    await handle_appeal_content(msg_content, fsm, mock_bot, test_db, mock_config)
    assert mock_bot.send_message.called
    sent_text = mock_bot.send_message.call_args[1]["text"]
    assert "Qisqa matn" in sent_text
    assert len(sent_text) < 4096


@pytest.mark.asyncio
async def test_contact_card_shared_at_name_step(test_db, memory_storage):
    """Verify sharing Telegram contact card at the name step extracts full name."""
    fsm = make_fsm_context(memory_storage)
    user_id = 9966
    await test_db.set_user_language(user_id, "uz")
    await fsm.set_state(AppealStates.waiting_for_name)

    mock_contact = MagicMock()
    mock_contact.first_name = "Dilshod"
    mock_contact.last_name = "Karimov"
    mock_contact.phone_number = "+998909876543"
    msg = make_mock_message(text=None, contact=mock_contact, user_id=user_id)

    await handle_name_input(msg, fsm, test_db)
    assert await fsm.get_state() == AppealStates.waiting_for_contact.state
    data = await fsm.get_data()
    assert data["full_name"] == "Dilshod Karimov"


@pytest.mark.asyncio
async def test_switch_to_anonymous_from_open_steps(test_db, memory_storage, mock_config):
    """Verify student tapping Anonymous button while at name or contact prompt switches to anonymous flow."""
    fsm = make_fsm_context(memory_storage)
    user_id = 9977
    await test_db.set_user_language(user_id, "uz")

    # Step 1: In waiting_for_name, taps Anonymous
    await fsm.set_state(AppealStates.waiting_for_name)
    await fsm.update_data(is_anonymous=False, full_name="Halfway User")
    msg_switch = make_mock_message(text="🔒 Anonim", user_id=user_id)
    await handle_name_input(msg_switch, fsm, test_db)

    # Must transition to waiting_for_appeal with anonymous state
    assert await fsm.get_state() == AppealStates.waiting_for_appeal.state
    data = await fsm.get_data()
    assert data["is_anonymous"] is True
    assert data["full_name"] is None

    # Submit appeal anonymously
    mock_bot = AsyncMock()
    msg_content = make_mock_message(text="Fikr matni", user_id=user_id)
    await handle_appeal_content(msg_content, fsm, mock_bot, test_db, mock_config)
    assert mock_bot.send_message.called
    rector_header = mock_bot.send_message.call_args[1]["text"]
    assert "📬 <b>Yangi anonim murojaat</b>" in rector_header
    assert "Halfway User" not in rector_header


@pytest.mark.asyncio
async def test_cancel_button_direct_handling_in_all_flow_handlers(test_db, memory_storage):
    """Verify direct calls to flow handlers with cancel button cleanly abort."""
    for handler_fn, st in [
        (handle_choose_appeal_type, AppealStates.waiting_for_type),
        (handle_name_input, AppealStates.waiting_for_name),
        (handle_contact_input, AppealStates.waiting_for_contact),
    ]:
        fsm = make_fsm_context(memory_storage)
        await fsm.set_state(st)
        user_id = 9988
        await test_db.set_user_language(user_id, "ru")

        msg_cancel = make_mock_message(text="❌ Отмена", user_id=user_id)
        await handler_fn(msg_cancel, fsm, test_db)
        assert await fsm.get_state() is None
        assert "отменено" in msg_cancel.answer.call_args[1]["text"]


@pytest.mark.asyncio
async def test_auto_language_detection_from_appeal_button(test_db, memory_storage, mock_config):
    """Verify user without saved language clicking Russian send appeal gets Russian type prompt."""
    fsm = make_fsm_context(memory_storage)
    user_id = 9999

    # User has no language in db initially
    assert await test_db.get_user_language(user_id) is None

    msg = make_mock_message(text="✉️ Отправить обращение", user_id=user_id)
    await handle_start_appeal(msg, fsm, test_db, mock_config)

    # State is waiting_for_type and prompt is in Russian
    assert await fsm.get_state() == AppealStates.waiting_for_type.state
    prompt_text = msg.answer.call_args[1]["text"]
    assert "🔐 Выберите тип обращения:" in prompt_text

    # Database language was automatically recorded as Russian
    assert await test_db.get_user_language(user_id) == "ru"



