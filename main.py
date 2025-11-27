import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import FSInputFile
from aiohttp import web
import aiohttp
from prompts import get_system_prompt

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
    # verify_ssl_certs=False нужно для Render
    ai_model = GigaChat(credentials=GIGA_KEY, verify_ssl_certs=False)
    logging.info("✅ GigaChat подключен!")
else:
    ai_model = None
    logging.warning("⚠️ GIGA_KEY не найден!")

# --- ТЕКСТЫ И КНОПКИ ---
BTN_BATTERY = "🔋 Батарейка на нуле"
BTN_FOG = "🌫 Я в тумане"
BTN_ANGER = "🔥 Меня всё бесит"
BTN_LOOK = "👀 Просто смотрю"
BTN_BACK = "🔙 В начало (Костёр)"
BTN_CONTACT = "✅ Да, давай попробуем"
BTN_READ = "🤔 Хочу сначала почитать"
BTN_FIGHT = "✅ Записаться на бой с тенью"

TXT_START = (
    "Тишина. Ты добрался.\n"
    "Здесь не нужно притворяться, что у тебя всё под контролем.\n\n"
    "Я — цифровой проводник Алексея. Моя задача — помочь тебе сделать выбор без давления.\n\n"
    "Что ты чувствуешь прямо сейчас?"
)

# --- ФУНКЦИИ МЕНЮ ---
async def show_main_menu(message: types.Message, with_photo=True):
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_BATTERY)
    builder.button(text=BTN_FOG)
    builder.button(text=BTN_ANGER)
    builder.button(text=BTN_LOOK)
    builder.adjust(2)
    
    try:
        if with_photo:
            photo = FSInputFile("bonfire.jpg")
            await message.answer_photo(photo, caption=TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))
        else:
            await message.answer(TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))
    except:
        await message.answer(TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))

# --- ОБРАБОТЧИКИ КНОПОК ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await show_main_menu(message, with_photo=True)

@dp.message(F.text == BTN_BACK) 
async def back_home(message: types.Message):
    await show_main_menu(message, with_photo=True) 

@dp.message(F.text.in_({BTN_BATTERY, BTN_FOG}))
async def flow_empathy(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_CONTACT)
    builder.button(text=BTN_READ)
    builder.button(text=BTN_BACK)
    builder.adjust(1)
    await message.answer("Знакомое чувство. Первая встреча — это не 'лечение', это выдох.\nМы можем найти 45 минут, чтобы поговорить бесплатно.", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == BTN_ANGER)
async def flow_anger(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_FIGHT)
    builder.button(text=BTN_BACK)
    builder.adjust(1)
    await message.answer("Злость — это топливо. Приноси её на встречу, она нам пригодится.", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text.in_({BTN_LOOK, BTN_READ}))
async def flow_skeptic(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Перейти в Канал", url=CHANNEL_LINK)
    kb_back = ReplyKeyboardBuilder()
    kb_back.button(text=BTN_BACK)
    await message.answer("Хорошая стратегия. Почитай канал Алексея без цензуры:", reply_markup=builder.as_markup())
    await message.answer("Как надумаешь — костёр горит здесь.", reply_markup=kb_back.as_markup(resize_keyboard=True))

@dp.message(F.text.in_({BTN_CONTACT, BTN_FIGHT}))
async def flow_contact_request(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Отправить мой контакт", request_contact=True)
    builder.button(text=BTN_BACK)
    builder.adjust(1)
    await message.answer("Принято. Нажми кнопку ниже, чтобы Алексей мог связаться.", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.contact)
async def flow_get_contact(message: types.Message):
    contact = message.contact
    kb = ReplyKeyboardBuilder()
    kb.button(text=BTN_BACK)
    await message.answer("Связь установлена. 📡\nАлексей напишет в течение 24 часов.", reply_markup=kb.as_markup(resize_keyboard=True))
    
    user_link = f"@{message.from_user.username}" if message.from_user.username else "Нет юзернейма"
    admin_text = (
        "🔥 <b>НОВАЯ ЗАЯВКА</b>\n"
        f"👤 {contact.first_name} {contact.last_name or ''}\n"
        f"📱 {contact.phone_number}\n"
        f"🔗 {user_link}\n"
        f"💬 ID: {message.from_user.id}"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
    except Exception as e:
        logging.error(e)

# --- 4. УМНЫЙ МОЗГ (GIGACHAT) ---
@dp.message(F.text)
async def ai_chat_handler(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text=BTN_BACK) 
    
    if not ai_model:
        await message.answer("Мозги отключены. Жми кнопку.", reply_markup=kb.as_markup(resize_keyboard=True))
        return

    await bot.send_chat_action(message.chat.id, "typing")

    try:
        # БЕРЕМ ПРОМПТ ИЗ ФАЙЛА
        system_text = get_system_prompt()
        
        # Склеиваем инструкцию и вопрос
        full_text = f"{system_text}\n\nПользователь пишет: {message.text}"
        
        # Отправляем
        response = await asyncio.to_thread(ai_model.chat, full_text)
        ai_answer = response.choices[0].message.content

        await message.answer(ai_answer, reply_markup=kb.as_markup(resize_keyboard=True))

    except Exception as e:
        logging.error(f"AI Error: {e}")
        await message.answer("Помехи в эфире... Вернись к костру.", reply_markup=kb.as_markup(resize_keyboard=True))
        
        # Получаем ответ
        ai_answer = response.choices[0].message.content

        await message.answer(ai_answer, reply_markup=kb.as_markup(resize_keyboard=True))

    except Exception as e:
        logging.error(f"AI Error: {e}")
        await message.answer("Помехи в эфире... Вернись к костру.", reply_markup=kb.as_markup(resize_keyboard=True))

# --- СЛУЖЕБНЫЕ ФУНКЦИИ (ВЕРНУЛИ ОБРАТНО!) ---

async def health_check(request):
    return web.Response(text="Bot is alive")

async def keep_alive():
    while True:
        await asyncio.sleep(600)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://127.0.0.1:8080') as resp:
                    pass
        except:
            pass

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

async def main():
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot),
        keep_alive()
    )

if __name__ == "__main__":
    asyncio.run(main())


