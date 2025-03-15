import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram import Dispatcher
import asyncio
import json
import random

# Telegram Bot Token (замени на свой)
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# ID групп
GROUPS = {
    "main": "@hYIBrs0vnYw5MWI6",
    "active": "@7tYJXjHi4Cs0Mjli",
    "mentors": "@CsChNc61Ct9mNjdi",
    "vip": "@AV86AOkbLlRiMTAy"
}

# ID администраторов
ADMINS = [123456789, 987654321]  # Замените на реальные ID администраторов

# Настройки логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Баллы пользователей (загружаем из файла или создаем пустую базу)
try:
    with open("user_scores.json", "r") as file:
        user_scores = json.load(file)
except FileNotFoundError:
    user_scores = {}

# Порог баллов для уровней
LEVELS = {
    "Practitioner": 200,
    "Guide": 500,
    "Mentor": 1000,
    "Guardian": 2000
}

# Функция начисления баллов
async def add_points(user_id, points):
    user_id = str(user_id)
    if user_id not in user_scores:
        user_scores[user_id] = {"points": 0, "level": "Seeker", "challenges": 0}
    user_scores[user_id]["points"] += points
    await check_level_up(user_id)
    save_data()

# Функция списания баллов
async def remove_points(user_id, points):
    user_id = str(user_id)
    if user_id in user_scores:
        user_scores[user_id]["points"] = max(0, user_scores[user_id]["points"] - points)
        save_data()

# Функция проверки повышения уровня
async def check_level_up(user_id):
    points = user_scores[user_id]["points"]
    current_level = user_scores[user_id]["level"]
    for level, required_points in LEVELS.items():
        if points >= required_points and current_level != level:
            user_scores[user_id]["level"] = level
            await bot.send_message(user_id, f"🎉 Поздравляем! Вы достигли уровня **{level}**!")
            await add_to_group(user_id, level)
            break

# Функция сохранения данных
def save_data():
    with open("user_scores.json", "w") as file:
        json.dump(user_scores, file)

# Функция добавления в группы
async def add_to_group(user_id, level):
    if level == "Practitioner":
        await bot.send_message(user_id, f"Добро пожаловать в чат активных участников: {GROUPS['active']}")
    elif level == "Mentor":
        await bot.send_message(user_id, f"Добро пожаловать в чат наставников: {GROUPS['mentors']}")
    elif level == "Guardian":
        await bot.send_message(user_id, f"Вы стали Хранителем! Доступ в VIP-клуб: {GROUPS['vip']}")

# Команда для администраторов - начисление баллов
@dp.message_handler(commands=["add_points"], is_chat_admin=True)
async def admin_add_points(message: types.Message):
    if message.from_user.id in ADMINS:
        args = message.text.split()
        if len(args) == 3 and args[1].isdigit() and args[2].isdigit():
            user_id = args[1]
            points = int(args[2])
            await add_points(user_id, points)
            await message.reply(f"✅ Начислено {points} баллов пользователю {user_id}.")
        else:
            await message.reply("❌ Используйте формат: /add_points <user_id> <баллы>")

# Команда для администраторов - снятие баллов
@dp.message_handler(commands=["remove_points"], is_chat_admin=True)
async def admin_remove_points(message: types.Message):
    if message.from_user.id in ADMINS:
        args = message.text.split()
        if len(args) == 3 and args[1].isdigit() and args[2].isdigit():
            user_id = args[1]
            points = int(args[2])
            await remove_points(user_id, points)
            await message.reply(f"❌ Снято {points} баллов у пользователя {user_id}.")
        else:
            await message.reply("❌ Используйте формат: /remove_points <user_id> <баллы>")

# Команда для пользователя - узнать текущий статус и прогресс
@dp.message_handler(commands=["status"])
async def user_status(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in user_scores:
        points = user_scores[user_id]["points"]
        current_level = user_scores[user_id]["level"]
        next_level = None
        points_needed = None
        for level, required_points in LEVELS.items():
            if required_points > points:
                next_level = level
                points_needed = required_points - points
                break
        if next_level:
            await message.reply(f"🏆 Ваш уровень: {current_level} ({points} баллов)\nСледующий уровень: {next_level} через {points_needed} баллов.")
        else:
            await message.reply(f"🏆 Ваш уровень: {current_level} ({points} баллов). Вы достигли максимального уровня!")
    else:
        await message.reply("❌ У вас пока нет баллов. Начните участвовать в активности!")

# Запуск бота
async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
