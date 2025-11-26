import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiohttp import web # <--- НУЖНА ЭТА БИБЛИОТЕКА

# Получаем токен (или берем из файла .env если он есть)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("TOKEN")

# Логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ВАШИ КНОПКИ И ЛОГИКА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="👋 Обо мне")],
        [types.KeyboardButton(text="💼 Мои услуги")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Привет! Я ваш HR-помощник.", reply_markup=keyboard)

@dp.message()
async def echo_handler(message: types.Message):
    if message.text == "👋 Обо мне":
        await message.answer("Я HR-консультант...")
    elif message.text == "💼 Мои услуги":
        await message.answer("Мои услуги...")
    else:
        await message.answer("Нажми на кнопку!")

# --- ОБМАНКА ДЛЯ RENDER (ФЕЙКОВЫЙ САЙТ) ---
async def health_check(request):
    return web.Response(text="Bot is alive")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check) # Главная страница сайта
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080) # Слушаем порт 8080
    await site.start()

# --- ЗАПУСК ВСЕГО ВМЕСТЕ ---
async def main():
    # Запускаем фейковый сайт и бота одновременно
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
