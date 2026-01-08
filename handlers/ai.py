from aiogram import Router, filters
from aiogram.types import Message
from openai import APIStatusError
import logging

from services.ai import ai_service

router = Router()
logger = logging.getLogger(__name__)

@router.message(filters.Command("ai"))
async def ai_chat(message: Message):
    try:
        user_text = message.text.replace("/ai", "").strip()
        if not user_text:
            await message.reply("Please provide a prompt. Example: /ai Hello")
            return

        wait_msg = await message.reply("Thinking...")

        response_content = ai_service.get_chat_response(user_text)

        await wait_msg.edit_text(response_content)

    except APIStatusError as e:
        logger.error(f"AI API Error: {e}")

        if e.status_code == 402:
            await wait_msg.edit_text(
                "⚠️ Insufficient balance.\nPlease add credits at openrouter.ai"
            )
        elif e.status_code == 401:
            await wait_msg.edit_text(
                "⚠️ Invalid OpenRouter API Key. Check your .env file."
            )
        else:
            await wait_msg.edit_text(f"⚠️ API Error ({e.status_code})")

    except Exception as e:
        logger.exception("Unexpected AI error")
        await message.reply(f"Error: {e}")
