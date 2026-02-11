import asyncio
import logging
from aiogram import Bot, Dispatcher
import config
from handlers import common, ai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set in .env file")

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Include routers
    dp.include_router(common.router)
    dp.include_router(ai.router)

    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
