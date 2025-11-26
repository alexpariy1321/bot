import os
import logging
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import FSInputFile
from aiohttp import web

# --- НАСТРОЙКИ ---
# ID Алексея (куда пересылать контакты). Вставьте свой ID цифрами!
ADMIN_ID = 174812505  

# Ссылка на ваш канал
CHANNEL_LINK = "https://t.me/AlexeyPariy" 

# --- Инициализация ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("TOKEN")
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ТЕКСТЫ (Чтобы не мусорить в логике) ---
TXT_START = (
    "Тишина. Ты добрался.\n"
    "Здесь не нужно притворяться, что у тебя всё под контролем.\n\n"
    "Я — цифровой проводник Алексея. Моя задача — помочь тебе сделать выбор без давления.\n\n"
    "Что ты чувствуешь прямо сейчас?"
)

TXT_BATTERY = (
    "Знакомое чувство. Будто ты бежишь марафон, но финиш постоянно отодвигают.\n\n"
    "Алексей тоже там был. Поэтому первая встреча — это не 'лечение'. Это выдох.\n"
    "Мы можем найти 45 минут на этой неделе, чтобы просто поговорить. Это бесплатно.\n\n"
    "Готов попробовать?"
)

TXT_ANGER = (
    "И это нормально. Злость — это топливо, которое горит не в том двигателе.\n"
    "Не нужно быть 'позитивным'. Приноси свою злость на встречу, она нам пригодится.\n\n"
    "Встреча конфиденциальна. Никто не узнает."
)

TXT_WATCH = (
    "Хорошая стратегия. В мире шума опасно доверять первому встречному.\n\n"
    "Вот что я могу предложить без обязательств:\n"
    "1. Почитать канал Алексея (там мысли без цензуры)\n"
    "2. Вернуться сюда, когда прижмет."
)

TXT_CONTACT_REQ = (
    "Принято.\n"
    "Чтобы Алексей мог связаться с тобой и предложить время, нажми кнопку ниже.\n"
    "Мы не будем спамить. Это закон."
)

TXT_FINAL = (
    "Связь установлена. 📡\n\n"
    "Алексей напишет тебе в личку в течение 24 часов.\n"
    "А пока... просто выдохни. Ты уже сделал самое сложное — признал, что тебе нужно поговорить."
)

# --- ЛОГИКА БОТА ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем кнопки (Reply)
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔋 Батарейка на нуле")
    builder.button(text="🌫 Я в тумане")
    builder.button(text="🔥 Меня всё бесит")
    builder.button(text="👀 Просто смотрю")
    builder.adjust(2) # По 2 кнопки в ряд

    # Отправляем фото костра (если есть файл bonfire.jpg)
    # Если файла нет - код не упадет, просто отправит текст
    try:
        photo = FSInputFile("bonfire.jpg")
        await message.answer_photo(photo, caption=TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))
    except:
        await message.answer(TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))

# Ветка А: Эмпатия (Батарейка / Туман)
@dp.message(F.text.in_({"🔋 Батарейка на нуле", "🌫 Я в тумане"}))
async def flow_empathy(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="✅ Да, давай попробуем")
    builder.button(text="🤔 Хочу сначала почитать")
    builder.adjust(1)
    await message.answer(TXT_BATTERY, reply_markup=builder.as_markup(resize_keyboard=True))

# Ветка Б: Агрессия
@dp.message(F.text == "🔥 Меня всё бесит")
async def flow_anger(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="✅ Записаться на бой с тенью")
    builder.button(text="🔙 Вернуться")
    builder.adjust(1)
    await message.answer(TXT_ANGER, reply_markup=builder.as_markup(resize_keyboard=True))

# Ветка В: Скептик
@dp.message(F.text.in_({"👀 Просто смотрю", "🤔 Хочу сначала почитать", "🔙 Вернуться"}))
async def flow_skeptic(message: types.Message):
    # Инлайн кнопки (ссылки)
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Перейти в Канал", url=CHANNEL_LINK)
    # Можно добавить ссылку на PDF гайд, если он есть
    
    await message.answer(TXT_WATCH, reply_markup=builder.as_markup())
    # Возвращаем главное меню клавиатурой, чтобы не потерялся
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔙 Вернуться в начало")
    await message.answer("...", reply_markup=kb.as_markup(resize_keyboard=True))

# Обработка желания записаться (Запрос контакта)
@dp.message(F.text.in_({"✅ Да, давай попробуем", "✅ Записаться на бой с тенью"}))
async def flow_contact_request(message: types.Message):
    builder = ReplyKeyboardBuilder()
    # СПЕЦИАЛЬНАЯ КНОПКА, которая сама отправляет номер телефона
    builder.button(text="📱 Отправить мой контакт", request_contact=True)
    builder.adjust(1)
    await message.answer(TXT_CONTACT_REQ, reply_markup=builder.as_markup(resize_keyboard=True))

# Финиш: Получение контакта и пересылка Админу
@dp.message(F.contact)
async def flow_get_contact(message: types.Message):
    contact = message.contact
    
    # 1. Отвечаем пользователю
    await message.answer(TXT_FINAL, reply_markup=types.ReplyKeyboardRemove())
    
    # 2. Пересылаем Алексею (Админу)
    user_link = f"@{message.from_user.username}" if message.from_user.username else "Нет юзернейма"
    admin_text = (
        "🔥 <b>НОВАЯ ЗАЯВКА (БОТ)</b>\n\n"
        f"👤 Имя: {contact.first_name} {contact.last_name or ''}\n"
        f"📱 Тел: {contact.phone_number}\n"
        f"🔗 Линк: {user_link}\n"
        f"💬 ID: {message.from_user.id}"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Не удалось отправить админу: {e}")

# Возврат в начало
@dp.message(F.text == "🔙 Вернуться в начало")
async def back_home(message: types.Message):
    await cmd_start(message)

# --- ФИНАЛЬНАЯ ВЕРСИЯ C САМО-ПИНГОМ ---

async def health_check(request):
    return web.Response(text="Bot is alive")

async def keep_alive():
    """Функция, которая сама себя пингует каждые 10 минут"""
    while True:
        await asyncio.sleep(600)  # Ждем 10 минут (600 секунд)
        try:
            # ВМЕСТО 'https://ваш-проект.onrender.com'
            # RENDER сам знает свой адрес внутри системы, можно стучаться локально
            # Но для надежности лучше указать полный внешний адрес.
            # Если вы не знаете точный адрес, используйте локальный хост:
            async with aiohttp.ClientSession() as session:
                # Стучимся сами к себе на локальный порт
                async with session.get('http://127.0.0.1:8080') as resp:
                    logging.info(f"Self-Ping status: {resp.status}")
        except Exception as e:
            logging.error(f"Self-Ping error: {e}")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

async def main():
    # Запускаем: Веб-сервер + Бота + Само-Пинг
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot),
        keep_alive()  # <--- Добавили вот это
    )

if __name__ == "__main__":
    # ВАЖНО: Нужно импортировать aiohttp внутри кода или в начале файла
    # Убедитесь, что в самом верху файла есть: import aiohttp
    asyncio.run(main())
