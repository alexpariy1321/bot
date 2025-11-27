import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import FSInputFile
from aiohttp import web
import aiohttp # Нужно для пинга (если оставили его)

# --- НАСТРОЙКИ ---
ADMIN_ID = 174812505  # Ваш ID
CHANNEL_LINK = "https://t.me/netoxicalex" 

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("TOKEN")
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ТЕКСТЫ ---
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
TXT_UNKNOW = (
    "Я слышу тебя, но пока понимаю только язык кнопок.\n\n"
    "Если ты не нашел нужного варианта — просто нажми 'В начало' и попробуй выбрать то, что ближе всего.\n"
    "Или перейди в канал, там можно писать в комментариях живым языком."
)

# --- ЛОГИКА ---

# Стартовое меню (вынесли в функцию, чтобы вызывать отовсюду)
async def show_main_menu(message: types.Message, with_photo=True):
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔋 Батарейка на нуле")
    builder.button(text="🌫 Я в тумане")
    builder.button(text="🔥 Меня всё бесит")
    builder.button(text="👀 Просто смотрю")
    builder.adjust(2)
    
    if with_photo:
        try:
            photo = FSInputFile("bonfire.jpg")
            await message.answer_photo(photo, caption=TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))
        except:
            await message.answer(TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))
    else:
        await message.answer(TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await show_main_menu(message, with_photo=True)

# Кнопка "В начало" (Возврат)
@dp.message(F.text.contains("В начало")) 
async def back_home(message: types.Message):
    # Без фото, чтобы не спамить картинкой каждый раз, или можно с фото
    await show_main_menu(message, with_photo=True) 

# Ветка А: Эмпатия
@dp.message(F.text.in_({"🔋 Батарейка на нуле", "🌫 Я в тумане"}))
async def flow_empathy(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="✅ Да, давай попробуем")
    builder.button(text="🤔 Хочу сначала почитать")
    builder.button(text="🔙 В начало (Костёр)") # Добавили возврат
    builder.adjust(1)
    await message.answer(TXT_BATTERY, reply_markup=builder.as_markup(resize_keyboard=True))

# Ветка Б: Агрессия
@dp.message(F.text == "🔥 Меня всё бесит")
async def flow_anger(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="✅ Записаться на бой с тенью")
    builder.button(text="🔙 В начало (Костёр)") # Добавили возврат
    builder.adjust(1)
    await message.answer(TXT_ANGER, reply_markup=builder.as_markup(resize_keyboard=True))

# Ветка В: Скептик
@dp.message(F.text.in_({"👀 Просто смотрю", "🤔 Хочу сначала почитать"}))
async def flow_skeptic(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Перейти в Канал", url=CHANNEL_LINK)
    
    await message.answer(TXT_WATCH, reply_markup=builder.as_markup())
    
    # Снизу дублируем навигацию, чтобы меню не пропало
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔙 В начало (Костёр)")
    await message.answer("Как надумаешь — костёр горит здесь.", reply_markup=kb.as_markup(resize_keyboard=True))

# Запрос контакта
@dp.message(F.text.in_({"✅ Да, давай попробуем", "✅ Записаться на бой с тенью"}))
async def flow_contact_request(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Отправить мой контакт", request_contact=True)
    builder.button(text="🔙 В начало (Костёр)") # Даже отсюда можно сбежать
    builder.adjust(1)
    await message.answer("Чтобы Алексей мог связаться...", reply_markup=builder.as_markup(resize_keyboard=True))

# Получение контакта
@dp.message(F.contact)
async def flow_get_contact(message: types.Message):
    contact = message.contact
    # Кнопка возврата после отправки, чтобы не висело пустое поле
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔙 В начало (Костёр)")
    
    await message.answer("Связь установлена. 📡\nАлексей напишет в течение 24 часов.", reply_markup=kb.as_markup(resize_keyboard=True))
    
    user_link = f"@{message.from_user.username}" if message.from_user.username else "Нет юзернейма"
    admin_text = (
        "🔥 <b>НОВАЯ ЗАЯВКА</b>\n"
        f"👤 {contact.first_name} {contact.last_name or ''}\n"
        f"📱 {contact.phone_number}\n"
        f"🔗 {user_link}"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
    except Exception as e:
        logging.error(e)

# --- МАГИЯ: Ловим всё остальное (Если человек пишет текст руками) ---
@dp.message()
async def unknown_message(message: types.Message):
    # Предлагаем вернуться к костру
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔙 В начало (Костёр)")
    await message.answer(TXT_UNKNOW, reply_markup=kb.as_markup(resize_keyboard=True))

# --- WEB SERVER (Оставляем как было) ---
async def health_check(request):
    return web.Response(text="Bot is alive")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

async def main():
    await asyncio.gather(start_web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
