import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import FSInputFile
from aiohttp import web
import aiohttp

# --- 1. БИБЛИОТЕКА GIGACHAT ---
from gigachat import GigaChat

# --- НАСТРОЙКИ ---
ADMIN_ID = 174812505
CHANNEL_LINK = "https://t.me/netoxicHR"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("TOKEN")
GIGA_KEY = os.getenv("GIGA_KEY") # Ключ Сбера

logging.basicConfig(level=logging.INFO)

# --- 2. НАСТРОЙКА GIGACHAT ---
if GIGA_KEY:
    # verify_ssl_certs=False нужно для Render, чтобы не ругался на сертификаты МинЦифры
    ai_model = GigaChat(credentials=GIGA_KEY, verify_ssl_certs=False)
    logging.info("✅ GigaChat подключен!")
else:
    ai_model = None
    logging.warning("⚠️ GIGA_KEY не найден!")

# --- 3. ЛИЧНОСТЬ БОТА ---
SYSTEM_PROMPT = (
    "Ты — Кибер-Ронин, ассистент психолога Алексея. "
    "Твоя миссия — быть спокойным проводником. "
    "Отвечай кратко, тепло, не ставь диагнозы. Предлагай помощь."
)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ... (ВСЕ ТЕКСТЫ И КНОПКИ ОСТАВЛЯЕМ ТЕ ЖЕ САМЫЕ, Я ИХ СОКРАТИЛ ДЛЯ ЧИТАЕМОСТИ) ...
# ... (СКОПИРУЙТЕ ИХ ИЗ СТАРОГО ФАЙЛА ИЛИ ПРОСТО ОСТАВЬТЕ КАК ЕСТЬ) ...

# ФУНКЦИИ МЕНЮ И КНОПОК ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ (show_main_menu, cmd_start и т.д.)
# ...

# --- 4. УМНЫЙ МОЗГ (GIGACHAT VERSION) ---
@dp.message(F.text)
async def ai_chat_handler(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔙 В начало (Костёр)") # Кнопка возврата
    
    if not ai_model:
        await message.answer("Мозги отключены. Жми кнопку.", reply_markup=kb.as_markup(resize_keyboard=True))
        return

    await bot.send_chat_action(message.chat.id, "typing")

    try:
        # Формируем диалог
        payload = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message.text}
        ]
        
        # Запрос к Сберу
        # Используем run в потоке, так как библиотека синхронная
        response = await asyncio.to_thread(ai_model.chat, payload)
        ai_answer = response.choices[0].message.content

        await message.answer(ai_answer, reply_markup=kb.as_markup(resize_keyboard=True))

    except Exception as e:
        logging.error(f"AI Error: {e}")
        await message.answer("Помехи в эфире... Вернись к костру.", reply_markup=kb.as_markup(resize_keyboard=True))

# ... (СЛУЖЕБНЫЕ ФУНКЦИИ keep_alive И main ОСТАЮТСЯ ТЕМИ ЖЕ) ...
