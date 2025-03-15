import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import json

# Telegram Bot Token (замени на свой)
TOKEN = "your_token_here"

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
dp = Dispatcher()

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
    try:
        user_id = str(user_id)
        if user_id not in user_scores:
            user_scores[user_id] = {"points": 0, "level": "Seeker", "challenges": 0}
        user_scores[user_id]["points"] += points
        await check_level_up(user_id)
        save_data()
    except Exception as e:
        logging.error(f"Ошибка начисления баллов: {e}")

# Функция списания баллов
async def remove_points(user_id, points):
    try:
        user_id = str(user_id)
        if user_id in user_scores:
            user_scores[user_id]["points"] = max(0, user_scores[user_id]["points"] - points)
            save_data()
    except Exception as e:
        logging.error(f"Ошибка списания баллов: {e}")

# Функция проверки повышения уровня
async def check_level_up(user_id):
    try:
        points = user_scores[user_id]["points"]
        current_level = user_scores[user_id]["level"]
        for level, required_points in LEVELS.items():
            if points >= required_points and current_level != level:
                user_scores[user_id]["level"] = level
                await bot.send_message(user_id, f"🎉 Поздравляем! Вы достигли уровня **{level}**!")
                await add_to_group(user_id, level)
                break
    except Exception as e:
        logging.error(f"Ошибка проверки уровня: {e}")

# Функция сохранения данных
def save_data():
    try:
        with open("user_scores.json", "w") as file:
            json.dump(user_scores, file)
    except Exception as e:
        logging.error(f"Ошибка сохранения данных: {e}")

# Функция добавления в группы
async def add_to_group(user_id, level):
    try:
        if level == "Practitioner":
            chat_id = await get_chat_id(GROUPS['active'])
            await bot.add_chat_member(chat_id, user_id)
            await bot.send_message(user_id, f"Добро пожаловать в чат активных участников: {GROUPS['active']}")
        elif level == "Mentor":
            chat_id = await get_chat_id(GROUPS['mentors'])
            await bot.add_chat_member(chat_id, user_id)
            await bot.send_message(user_id, f"Добро пожаловать в чат наставников: {GROUPS['mentors']}")
        elif level == "Guardian":
            chat_id = await get_chat_id(GROUPS['vip'])
            await bot.add_chat_member(chat_id, user_id)
            await bot.send_message(user_id, f"Вы стали Хранителем! Доступ в VIP-клуб: {GROUPS['vip']}")
    except Exception as e:
        logging.error(f"Ошибка добавления в группу: {e}")

# Функция получения идентификатора чата по ссылке
async def get_chat_id(chat_link):
    try:
        chat_info = await bot.get_chat(chat_link)
        return chat_info.id
    except Exception as e:
        logging.error(f"Ошибка получения идентификатора чата: {e}")
        return None

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

# Команда для администраторов - добавить пользователя в группу
@dp.message_handler(commands=["add_to_group"], is_chat_admin=True)
async def admin_add_to_group(message: types.Message):
    if message.from_user.id in ADMINS:
        args = message.text.split()
        if len(args) == 3:
            user_id = args[1]
            group_name = args[2]
            if group_name in GROUPS:
                chat_id = await get_chat_id(GROUPS[group_name])
                if chat_id:
                    await bot.add_chat_member(chat_id, user_id)
                    await message.reply(f"Пользователь {user_id} добавлен в группу {group_name}.")
                else:
                    await message.reply(f"Не удалось получить идентификатор группы {group_name}.")
            else:
                await message.reply("Недопустимое имя группы.")
        else:
            await message.reply("Используйте формат: /add_to_group <user_id> <group_name>")

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

# Команда для просмотра списка групп
@dp.message_handler(commands=["groups"])
async def show_groups(message: types.Message):
    groups_list = "\n".join([f"{name}: {link}" for name, link in GROUPS.items()])
    await message.reply(f"Список групп:\n{groups_list}")

# Запуск бота
async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
