import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage import MemoryStorage
from aiogram.exceptions import TelegramConflictError

async def main():
    bot = Bot(token="7555883585:AAFFzmAIxWCIQWkxn1qE-3NFp3sDIyW_hIQ", parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            relax=2.0,  # Увеличить интервал между запросами
            timeout=30   # Таймаут для long-polling
        )
    except TelegramConflictError as e:
        logging.critical(f"Conflict detected: {e}")
        await bot.session.close()
        exit(1)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
