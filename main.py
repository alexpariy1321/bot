import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

# ВСТАВЬТЕ СЮДА ВАШ ТОКЕН ВНУТРИ КАВЫЧЕК
TOKEN = os.getenv("TOKEN")

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=TOKEN)
# Диспетчер (это мозг, который распределяет сообщения)
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="👋 Кто я")],
        [types.KeyboardButton(text="💼 Услуги")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Привет! Я ваш личный психолог. Чем могу помочь?", reply_markup=keyboard)

# Хэндлер на нажатие кнопок
@dp.message()
async def echo_handler(message: types.Message):
    if message.text == "👋 Обо мне":
        await message.answer("Я HR-консультант с опытом...")
    elif message.text == "💼 Мои услуги":
        await message.answer("1. Консультация\n2. Разбор резюме")
    else:
        await message.answer("Я пока понимаю только кнопки!")

# Запуск процесса
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



