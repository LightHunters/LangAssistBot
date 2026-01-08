import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

import config
from handlers.common import router as common_router
from handlers.ai import router as ai_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    dp = Dispatcher()
    dp.include_router(common_router)
    dp.include_router(ai_router)

    logger.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
