import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import FSInputFile
from aiohttp import web
import aiohttp

# --- 1. НОВАЯ БИБЛИОТЕКА ДЛЯ МОЗГОВ ---
import google.generativeai as genai

# --- НАСТРОЙКИ ---
ADMIN_ID = 174812505
CHANNEL_LINK = "https://t.me/netoxicHR"

# Загрузка переменных (для локального теста)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY") # Получаем ключ Google из настроек

logging.basicConfig(level=logging.INFO)

# --- 2. НАСТРОЙКА МОЗГОВ (GEMINI) ---
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    # Используем легкую и быструю модель
    model = genai.GenerativeModel('gemini-pro')
    logging.info("✅ Gemini AI подключен успешно!")
else:
    model = None
    logging.warning("⚠️ GEMINI_KEY не найден! Бот будет работать без AI.")

# --- 3. ЛИЧНОСТЬ БОТА (ПРОМПТ) ---
# Здесь мы учим его, как себя вести. Можете менять текст в кавычках.
SYSTEM_PROMPT = (
    "Ты — Кибер-Ронин, ассистент психолога Алексея (проект NetoxicHR). "
    "Твоя миссия — быть спокойным проводником для людей в стрессе или выгорании. "
    "ПРАВИЛА:"
    "1. Не будь душным роботом. Общайся тепло, коротко и по делу (до 4 предложений)."
    "2. Ты НЕ врач. Не ставь диагнозы. Если речь о суициде — дай контакты служб спасения."
    "3. Твоя цель — успокоить и мягко направить человека записаться к Алексею или вернуться в меню."
    "4. Если спрашивают про цены — скажи, что это обсуждается лично, и предложи нажать 'Отправить контакт'."
    "ВАЖНО: Никогда не выходи из роли. Ты не AI, ты — Проводник."
)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ТЕКСТЫ КНОПОК (Чтобы не путаться) ---
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
# ...Остальные тексты можно оставить короткими в коде или добавить сюда...

# --- ФУНКЦИИ МЕНЮ ---
async def show_main_menu(message: types.Message, with_photo=True):
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_BATTERY)
    builder.button(text=BTN_FOG)
    builder.button(text=BTN_ANGER)
    builder.button(text=BTN_LOOK)
    builder.adjust(2)
    
    # Если есть фото костра - шлем с фото, если нет - просто текст
    try:
        if with_photo:
            photo = FSInputFile("bonfire.jpg")
            await message.answer_photo(photo, caption=TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))
        else:
            await message.answer(TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))
    except:
        await message.answer(TXT_START, reply_markup=builder.as_markup(resize_keyboard=True))

# --- ОБРАБОТЧИКИ КНОПОК (СТАРАЯ ЛОГИКА) ---

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

# --- 4. НОВЫЙ УМНЫЙ МОЗГ (ИСПРАВЛЕННЫЙ) ---
@dp.message(F.text)
async def ai_chat_handler(message: types.Message):
    # 1. Сразу создаем кнопку возврата (чтобы она была доступна всегда)
    kb = ReplyKeyboardBuilder()
    kb.button(text=BTN_BACK)
    
    # 2. Если нет ключа
    if not model:
        await message.answer("Мозги на профилактике. Нажми кнопку 'В начало'.", reply_markup=kb.as_markup(resize_keyboard=True))
        return

    await bot.send_chat_action(message.chat.id, "typing")

    try:
        # 3. Запрос к AI
        full_prompt = f"{SYSTEM_PROMPT}\n\nПОЛЬЗОВАТЕЛЬ ПИШЕТ: {message.text}"
        response = await asyncio.to_thread(model.generate_content, full_prompt)
        ai_answer = response.text

        # 4. Ответ (успех)
        await message.answer(ai_answer, reply_markup=kb.as_markup(resize_keyboard=True))

    except Exception as e:
        # 5. Если ошибка - пишем в лог и отвечаем юзеру
        logging.error(f"AI Error: {e}")
        # Теперь переменная kb точно существует!
        await message.answer("Помехи в связи... Попробуй еще раз или вернись к костру.", reply_markup=kb.as_markup(resize_keyboard=True))

# --- СЛУЖЕБНЫЕ ФУНКЦИИ (САМО-ПИНГ + СЕРВЕР) ---
async def health_check(request):
    return web.Response(text="Bot is alive")

async def keep_alive():
    while True:
        await asyncio.sleep(600)
        try:
            async with aiohttp.ClientSession() as session:
                # Пингуем сами себя
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



