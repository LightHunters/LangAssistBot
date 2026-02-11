import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

import config
import mongo
from handlers.common import router as common_router
from handlers.ai import router as ai_router
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set in environment")


    await mongo.init_db()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(common_router)
    dp.include_router(ai_router)

   
    start_scheduler(bot)

    logger.info("Bot started")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
