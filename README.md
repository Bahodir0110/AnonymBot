# 🏛 Tash Tech CEO Appeals Telegram Bot

[![CI](https://github.com/tashtech/rector-anonymous-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/tashtech/rector-anonymous-bot/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.x-brightgreen.svg)](https://docs.aiogram.dev/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An official appeals bot for **Tash Tech University** students in Tashkent to send proposals, feedback, and complaints directly to the CEO.

---

## 🇺🇸 English Documentation

### 🌟 Key Features

1. **Zero-Knowledge Anonymity**:
   - Messages and attachments are delivered via Telegram's `copy_message` API, eliminating sender forward headers, profile links, and phone numbers.
   - Database schema strictly separates rate-limiting user IDs from appeals (`appeals` table contains **zero** student identifiers).
2. **Trilingual Support**:
   - Uzbek Latin (`uz`), Russian (`ru`), and English (`en`).
   - Interactive inline language selector on `/start` and persistent change language button (`🌐 Tilni o'zgartirish`).
3. **Strict One-Way Rector Delivery**:
   - Delivered to a configurable personal, group, or channel ID (`RECTOR_CHAT_ID`).
   - Supports supergroup forum topics via `RECTOR_THREAD_ID`.
   - Strictly one-way: no replies can be routed back to students.
4. **Rich Content Support**:
   - Plain text, photos, documents/PDFs, voice notes, audio, and videos.
5. **Anti-Spam & Cooldown**:
   - Configurable cooldown per student (`RATE_LIMIT_SECONDS=60`).
   - Displays friendly countdown messages when cooldown is active.
6. **Rector Notification Header**:
   - Header with sequential reference ID (`#TT-0001`), UTC+5 Tashkent timestamp, and student's chosen language.
7. **Clean Student Interface**:
   - Reply keyboard with only `✉️ Murojaat yuborish` and `🌐 Tilni o'zgartirish`.
   - `❌ Bekor qilish` cancel button during active appeal draft.
   - Submission confirmation:
     ```
     ✅ Rahmat! Murojaatingiz yuborildi.

     🔒 Anonim murojaat — javob va holat kuzatilmaydi.
     ```

---

### 🚀 Quick Start & Installation

#### 1. Clone & Prepare Environment
```bash
git clone https://github.com/tashtech/rector-anonymous-bot.git
cd rector-anonymous-bot
cp .env.example .env
```

#### 2. Configure Environment Variables (`.env`)
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
RECTOR_CHAT_ID=-1001234567890
RECTOR_THREAD_ID=
RATE_LIMIT_SECONDS=60
DB_PATH=data/bot.db
TIMEZONE=Asia/Tashkent
LOG_LEVEL=INFO
```

> **How to obtain `RECTOR_CHAT_ID`?**
> - For a personal chat: Message [@userinfobot](https://t.me/userinfobot) to find the Rector's Telegram ID.
> - For a private group/channel: Add your bot to the group/channel as an admin and send a message, then inspect updates or use [@raw_data_bot](https://t.me/raw_data_bot). Group IDs usually begin with `-100...`.

#### 3. Run with Docker Compose (Recommended)
```bash
docker-compose up -d --build
```
To view real-time logs:
```bash
docker-compose logs -f bot
```

#### 4. Run Locally without Docker
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### 5. Run Automated Tests
```bash
pytest -v
```

---

## 🇺🇿 O'zbekcha Qo'llanma

### 🌟 Asosiy Imkoniyatlar

1. **100% Kafolatlangan Anonimlik**:
   - Xabarlar va media fayllar Telegram `copy_message` orqali yuboriladi. Anonim rejimda talabaning ismi, username'i, profili yoki telefon raqami ijrochi direktorga ko'rsatilmaydi.
   - Ma'lumotlar bazasida anonim murojaatlar talaba shaxsi bilan bog'lanmagan (Zero-Knowledge arxitekturasi).
2. **3 ta Tilni Qo'llab-quvvatlash**:
   - O'zbekcha (Lotin), Ruscha va Inglizcha.
   - `/start` bosilganda inline tugmalar orqali til tanlanadi va xohlagan paytda `🌐 Tilni o'zgartirish` orqali almashtiriladi.
3. **Ijrochi direktorga Yetkazish**:
   - `.env` orqali ijrochi direktorning shaxsiy Telegram ID'si yoki maxsus yopiq guruh/kanal ID'si (`RECTOR_CHAT_ID`) sozlanadi.
   - Forum guruhlar uchun mavzu (topic) ID'si (`RECTOR_THREAD_ID`) qo'llab-quvvatlanadi.
   - Talabaga javob qaytarilmaydi (bir tomonlama aloqa).
4. **Har Qanday Media Turlari**:
   - Matn, rasm, PDF va boshqa hujjatlar, ovozli xabar (audio/voice) hamda video.
5. **Anti-Spam Himoyasi**:
   - Har bir talaba uchun murojaatlar oralig'ida kutish vaqti (`RATE_LIMIT_SECONDS=60`).
   - Qayta yuborishdan oldin necha soniya qolganini ko'rsatuvchi ogohlantirish.
6. **Bildirishnoma Formati**:
   - Har bir murojaat tartib raqami (`#TT-0001`), Toshkent vaqti (UTC+5) va talabaning tanlagan tili bilan birga yetkaziladi.

---

### 🚀 O'rnatish va Ishga Tushirish

#### 1. Loyihani yuklab olish va sozlash
```bash
git clone https://github.com/tashtech/rector-anonymous-bot.git
cd rector-anonymous-bot
cp .env.example .env
```

#### 2. `.env` faylini to'ldirish
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
RECTOR_CHAT_ID=-1001234567890
RECTOR_THREAD_ID=
RATE_LIMIT_SECONDS=60
DB_PATH=data/bot.db
TIMEZONE=Asia/Tashkent
LOG_LEVEL=INFO
```

#### 3. Docker orqali ishga tushirish (Tavsiya etiladi)
```bash
docker-compose up -d --build
```
Loglarni kuzatish:
```bash
docker-compose logs -f bot
```

#### 4. Mahalliy (Local) kompyuterda ishga tushirish
```bash
python -m venv .venv
# Windows tizimida:
.venv\Scripts\activate
# Linux / macOS tizimida:
# source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

#### 5. Testlarni ishga tushirish
```bash
pytest -v
```

---

## 🗄 Ma'lumotlar Bazasi Tuzilishi (Database Architecture)

```
SQLite (data/bot.db)
├── users (Talabalar tili va anti-spam vaqti)
│   ├── user_id (INTEGER PRIMARY KEY)
│   ├── language_code (TEXT)
│   ├── last_appeal_at (REAL)
│   └── timestamps
│
└── appeals (Anonim murojaatlar - Talaba ID saqlanmaydi!)
    ├── id (INTEGER PRIMARY KEY AUTOINCREMENT)
    ├── reference_code (TEXT UNIQUE) - Masalan: #TT-0001
    ├── language_code (TEXT)
    ├── content_type (TEXT) - text / photo / document / voice / video
    └── created_at (TIMESTAMP)
```

---

## 🛡 Xavfsizlik va Maxfiylik (Security & Privacy)

- **Hech qanday user_id saqlanmaydi**: `appeals` jadvalida talabaning `user_id` ustuni umuman mavjud emas. Bazaga to'g'ridan-to'g'ri kirish huquqiga ega shaxs ham murojaat qaysi talabaga tegishli ekanini aniqlay olmaydi.
- **HTML injection himoyasi**: Talaba yuborgan xabardagi barcha HTML belgilar (`<`, `>`, `&`) avtomatik tozalanadi va xavfsiz holatda yetkaziladi.
- **Docker Volume**: Ma'lumotlar bazasi `./data` papkasi orqali konteyner tashqarisida saqlanadi va yangilanishlarda yo'qolib ketmaydi.
