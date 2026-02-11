from aiogram import Router, filters
from aiogram.types import Message
from openai import APIStatusError
import logging
from services.ai import ai_service

router = Router()
logger = logging.getLogger(__name__)

@router.message(filters.Command("ai", prefix="/"))
async def ai_chat(message: Message):
    try:
        user_text = message.text.replace("/ai", "").strip()
        if not user_text:
            await message.reply("Please provide a prompt. Example: /ai Hello")
            return
            
        wait_msg = await message.reply("Thinking...")
        
        # Use the service to get the response
        response_content = ai_service.get_chat_response(user_text)
        
        await wait_msg.edit_text(response_content)
        
    except APIStatusError as e:
        logger.error(f"AI API Error: {e}")
        if e.status_code == 402:
            await wait_msg.edit_text(
                "⚠️ **Insufficient Balance**\n\n"
                "The bot cannot process your request because the OpenRouter account has run out of credits.\n"
                "Please add funds at [openrouter.ai](https://openrouter.ai)."
            )
        elif e.status_code == 401:
             await wait_msg.edit_text(
                "⚠️ **Authentication Error**\n\n"
                "Invalid or missing OpenRouter API Key. Please check your .env file."
            )
        else:
            await wait_msg.edit_text(f"⚠️ API Error ({e.status_code}): {e.message}")
            
    except Exception as e:
        logger.error(f"AI Unexpected Error: {e}")
        if 'wait_msg' in locals():
            await wait_msg.edit_text(f"An error occurred: {str(e)}")
        else:
            await message.reply(f"An error occurred: {str(e)}")
