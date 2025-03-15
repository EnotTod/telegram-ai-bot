import logging
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ChatMemberAdministrator

# Telegram Bot Token
TOKEN = "7555883585:AAFFzmAIxWCIQWkxn1qE-3NFp3sDIyW_hIQ"

# ID групп
GROUPS = {
    "main": "@hYIBrs0vnYw5MWI6",
    "active": "@7tYJXjHi4Cs0Mjli",
    "mentors": "@CsChNc61Ct9mNjdi",
    "vip": "@AV86AOkbLlRiMTAy"
}

# ID администраторов
ADMINS = [123456789, 987654321]

# Настройки логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Загрузка данных пользователей
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

async def add_points(user_id: int, points: int):
    user_id = str(user_id)
    if user_id not in user_scores:
        user_scores[user_id] = {"points": 0, "level": "Seeker"}
    user_scores[user_id]["points"] += points
    await check_level_up(user_id)
    save_data()

async def remove_points(user_id: int, points: int):
    user_id = str(user_id)
    if user_id in user_scores:
        user_scores[user_id]["points"] = max(0, user_scores[user_id]["points"] - points)
        save_data()

async def check_level_up(user_id: str):
    points = user_scores[user_id]["points"]
    current_level = user_scores[user_id]["level"]
    for level, required in LEVELS.items():
        if points >= required and current_level != level:
            user_scores[user_id]["level"] = level
            await bot.send_message(user_id, f"🎉 Новый уровень: {level}!")
            await add_to_group(int(user_id), level)
            break

def save_data():
    with open("user_scores.json", "w") as file:
        json.dump(user_scores, file, indent=4)

async def add_to_group(user_id: int, level: str):
    try:
        group = {
            "Practitioner": GROUPS['active'],
            "Mentor": GROUPS['mentors'],
            "Guardian": GROUPS['vip']
        }.get(level)
        
        if group:
            chat = await bot.get_chat(group)
            await bot.add_chat_member(chat.id, user_id)
            await bot.send_message(user_id, f"Добро пожаловать в {group}!")
    except Exception as e:
        logging.error(f"Ошибка добавления в группу: {e}")

# Кастомный фильтр для админов
from aiogram.filters import BaseFilter

class IsChatAdmin(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        if not message.chat.type in ["group", "supergroup"]:
            return False
            
        member = await message.bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )
        return isinstance(member, ChatMemberAdministrator) and member.can_restrict_members

# Обработчики команд
@dp.message(Command("add_points"), IsChatAdmin())
async def handle_add_points(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    try:
        _, user_id, points = message.text.split()
        await add_points(int(user_id), int(points))
        await message.reply(f"✅ Добавлено {points} баллов для {user_id}")
    except:
        await message.reply("❌ Формат: /add_points <user_id> <points>")

@dp.message(Command("remove_points"), IsChatAdmin())
async def handle_remove_points(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    try:
        _, user_id, points = message.text.split()
        await remove_points(int(user_id), int(points))
        await message.reply(f"✅ Снято {points} баллов с {user_id}")
    except:
        await message.reply("❌ Формат: /remove_points <user_id> <points>")

@dp.message(Command("status"))
async def handle_status(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in user_scores:
        data = user_scores[user_id]
        reply = f"🏅 Уровень: {data['level']}\n💎 Баллы: {data['points']}"
        await message.reply(reply)
    else:
        await message.reply("❌ Данные не найдены")

@dp.message(Command("groups"))
async def handle_groups(message: types.Message):
    groups = "\n".join([f"{k}: {v}" for k, v in GROUPS.items()])
    await message.reply(f"📚 Список групп:\n{groups}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
