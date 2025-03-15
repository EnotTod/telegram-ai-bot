import logging
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, BaseFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramConflictError, TelegramRetryAfter
from aiogram.utils.backoff import BackoffConfig

# Telegram Bot Token (замени на свой)
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

async def add_points(user_id, points):
    try:
        user_id = str(user_id)
        if user_id not in user_scores:
            user_scores[user_id] = {"points": 0, "level": "Seeker"}
        user_scores[user_id]["points"] += points
        await check_level_up(user_id)
        save_data()
    except Exception as e:
        logging.error(f"Ошибка начисления баллов: {e}")

async def remove_points(user_id, points):
    try:
        user_id = str(user_id)
        if user_id in user_scores:
            user_scores[user_id]["points"] = max(0, user_scores[user_id]["points"] - points)
            save_data()
    except Exception as e:
        logging.error(f"Ошибка списания баллов: {e}")

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

def save_data():
    try:
        with open("user_scores.json", "w") as file:
            json.dump(user_scores, file)
    except Exception as e:
        logging.error(f"Ошибка сохранения данных: {e}")

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

async def get_chat_id(chat_link):
    try:
        chat_info = await bot.get_chat(chat_link)
        return chat_info.id
    except Exception as e:
        logging.error(f"Ошибка получения идентификатора чата: {e}")
        return None

# Кастомный фильтр для админов
class IsChatAdmin(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        if not message.chat.type in ["group", "supergroup"]:
            return False
            
        member = await message.bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )
        return isinstance(member, types.ChatMemberAdministrator) and member.can_restrict_members

# Обработчики команд
@dp.message(Command("add_points"), IsChatAdmin())
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
    else:
        await message.reply("❌ Вы не являетесь администратором.")

# Обработчики команд
@dp.message(Command("remove_points"), IsChatAdmin())
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
    else:
        await message.reply("❌ Вы не являетесь администратором.")

# Команда для пользователя - узнать текущий статус и прогресс
@dp.message(Command("status"))
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
@dp.message(Command("groups"))
async def show_groups(message: types.Message):
    groups_list = "\n".join([f"{name}: {link}" for name, link in GROUPS.items()])
    await message.reply(f"Список групп:\n{groups_list}")

# Обработка ошибок
@dp.errors()
async def error_handler(update, exception):
    if isinstance(exception, TelegramConflictError):
        logging.critical("Conflict detected. Stopping bot.")
        await dp.stop_polling()
        await bot.session.close()
        exit(1)
    elif isinstance(exception, TelegramRetryAfter):
        logging.warning(f"Flood control. Retry after {exception.retry_after} seconds")
        await asyncio.sleep(exception.retry_after)
    else:
        logging.error(f"Error occurred: {exception}")

async def main():
    backoff_config = BackoffConfig(
        min_delay=1.0,
        max_delay=5.0,
        factor=1.3,
        jitter=0.1
    )
    
    try:
        await dp.start_polling(
            bot,
            polling_timeout=30,
            handle_as_tasks=True,
            backoff_config=backoff_config,
            allowed_updates=None,
            handle_signals=True,
            close_bot_session=True
        )
    except Exception as e:
        logging.critical(f"Failed to start polling: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
