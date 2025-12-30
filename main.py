import asyncio
import logging
import random
import os
import json  # <--- 1. Добавили библиотеку
from dotenv import load_dotenv
from datetime import datetime
import pytz

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale

# --- ЗАГРУЗКА НАСТРОЕК ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")

# 2. Функция для чтения файла пользователей
def load_users_config():
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("Файл users.json не найден! Создайте его.")
        return {}
    except json.JSONDecodeError:
        logging.error("Ошибка в формате файла users.json (проверьте запятые и кавычки).")
        return {}

# 3. Загружаем конфиг в переменную
USERS_CONFIG = load_users_config()

DEFAULT_TZ = "UTC"

# Шутки
YOGA_JOKES = [
    "Готовьте коврики! Шавасана сама себя не сделает 🧘‍♀️",
    "Самое сложное в йоге — это расстелить коврик 😉",
    "Спина скажет спасибо! 🙏",
    "Не будь как бревно, будь как бамбук! 🌱",
    "Вдох — выдох. Главное не уснуть! 😴"
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class YogaState(StatesGroup):
    waiting_for_time = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_tz_name(username: str):
    """Получить таймзону по юзернейму или вернуть дефолтную"""
    return USERS_CONFIG.get(username.lower(), DEFAULT_TZ)

def calculate_all_times(base_dt: datetime, base_tz_name: str):
    """
    Принимает время автора.
    Возвращает список строк с временем для КАЖДОГО участника из USERS_CONFIG.
    """
    base_tz = pytz.timezone(base_tz_name)
    # Делаем время автора "осознанным" (с часовым поясом)
    dt_base_localized = base_tz.localize(base_dt)
    
    results = []
    
    # Проходим по всем участникам в конфиге
    for user_login, user_tz_str in USERS_CONFIG.items():
        target_tz = pytz.timezone(user_tz_str)
        # Конвертируем время
        dt_target = dt_base_localized.astimezone(target_tz)
        
        # Красивый формат: 19:00 (25.10)
        time_str = dt_target.strftime("%H:%M (%d.%m)")
        
        # Добавляем значок, если это время автора
        icon = "👤" if user_tz_str == base_tz_name else "📍"
        
        # Формируем строку: 📍 login (City): 19:00...
        # Берем город из таймзоны для краткости (напр. Helsinki)
        city = user_tz_str.split('/')[-1].replace('_', ' ')
        
        results.append(f"{icon} **{user_login}** ({city}): `{time_str}`")
        
    return "\n".join(results)

# --- ЛОГИКА БОТА ---

@dp.message(Command("yoga"))
async def cmd_yoga(message: types.Message):
    if not message.from_user.username:
        await message.answer("Ошибка: У вас нет Username. Установите его в настройках Telegram.")
        return

    user_tz = get_tz_name(message.from_user.username)
    
    calendar = SimpleCalendar(locale=await get_user_locale(message.from_user))
    await message.answer(
        f"📅 **Планируем занятие**\nВаша зона: `{user_tz}`\n\nВыберите дату:",
        reply_markup=await calendar.start_calendar(),
        parse_mode="Markdown"
    )

@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected_date = callback_data.date
    await state.update_data(chosen_date=selected_date)
    await state.set_state(YogaState.waiting_for_time)
    
    # --- ГЕНЕРАЦИЯ ПОДСКАЗКИ О РАЗНИЦЕ ВО ВРЕМЕНИ ---
    sender_username = callback.from_user.username.lower()
    sender_tz_name = get_tz_name(sender_username)
    sender_tz = pytz.timezone(sender_tz_name)
    
    hint_lines = []
    noon = selected_date.replace(hour=12)
    dt_sender = sender_tz.localize(noon)
    
    # Считаем разницу для всех остальных
    for u_login, u_tz_str in USERS_CONFIG.items():
        if u_login == sender_username: continue # Пропускаем автора
        
        target_tz = pytz.timezone(u_tz_str)
        dt_target = dt_sender.astimezone(target_tz)
        
        diff = (dt_target.utcoffset() - dt_sender.utcoffset()).total_seconds() / 3600
        sign = "+" if diff > 0 else ""
        if diff != 0:
            hint_lines.append(f"{u_login}: {sign}{int(diff)}ч")
            
    hint_text = f"\nℹ️ Разница: {', '.join(hint_lines)}" if hint_lines else ""

    date_str = selected_date.strftime("%d.%m.%Y")
    await callback.message.edit_text(
        f"🗓 Дата: **{date_str}**\nВведите время (в вашем поясе). Пример: `19:00`\n{hint_text}",
        parse_mode="Markdown"
    )

@dp.message(YogaState.waiting_for_time)
async def process_time_input(message: types.Message, state: FSMContext):
    user_time_str = message.text.strip()
    try:
        hour, minute = map(int, user_time_str.replace('.', ':').split(':'))
    except ValueError:
        await message.answer("Формат: ЧЧ:ММ (напр. 19:00)")
        return

    data = await state.get_data()
    chosen_date = data['chosen_date']
    
    # Базовое время (наивное)
    dt_naive = chosen_date.replace(hour=hour, minute=minute)
    
    # Кто отправляет
    sender_username = message.from_user.username.lower()
    sender_tz_name = get_tz_name(sender_username)
    
    # Генерируем список времен для всех
    times_list_str = calculate_all_times(dt_naive, sender_tz_name)
    
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтверждаю", callback_data="approve")
    builder.button(text="❌ Не подходит", callback_data="reject")
    builder.adjust(2)
    
    await message.answer(
        f"🧘 **Предложение занятия**\n\n"
        f"{times_list_str}\n\n"
        f"Согласуем?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "approve")
async def send_approve(callback: types.CallbackQuery):
    text_with_times = callback.message.text.split("Согласуем?")[0].strip()
    joke = random.choice(YOGA_JOKES)
    user_approver = callback.from_user.first_name

    final_text = (
        f"{text_with_times}\n\n"
        f"✅ **ЗАНЯТИЕ СОСТОИТСЯ!**\n"
        f"(Подтвердил: {user_approver})\n"
        f"✨ _{joke}_"
    )
    
    await callback.message.edit_text(final_text, parse_mode="Markdown")
    try: await callback.message.pin()
    except: pass

@dp.callback_query(F.data == "reject")
async def send_reject(callback: types.CallbackQuery):
    user = callback.from_user.first_name
    await callback.message.edit_text(f"❌ **ОТМЕНА** ({user})\nПредложите другое время.", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())