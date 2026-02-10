from aiogram import Router, filters
from aiogram.types import Message
from openai import APIStatusError
import logging, asyncio

from services.ai import ai_service
import mongo

router = Router()
logger = logging.getLogger(__name__)

# General-purpose chat `/ai` — does NOT save words
@router.message(filters.Command("ai"))
async def ai_chat(message: Message):
    wait_msg = None
    try:
        user_text = message.text.replace("/ai", "").strip()
        if not user_text:
            await message.reply("Please provide a prompt. Example: /ai Hello")
            return

        wait_msg = await message.reply("Thinking...")

        response_content = await asyncio.to_thread(ai_service.get_chat_response, user_text)

        await wait_msg.edit_text(response_content)
    except APIStatusError as e:
        logger.error(f"AI API Error: {e}")
        if wait_msg:
            if getattr(e, "status_code", None) == 402:
                await wait_msg.edit_text("⚠️ Insufficient balance. Add credits at your provider.")
            elif getattr(e, "status_code", None) == 401:
                await wait_msg.edit_text("⚠️ Invalid API Key.")
            else:
                await wait_msg.edit_text(f"⚠️ API Error ({getattr(e,'status_code', 'unknown')})")
    except Exception as e:
        logger.exception("Unexpected AI error")
        if wait_msg:
            await wait_msg.edit_text("⚠️ Something went wrong with the AI service.")
        else:
            await message.reply("⚠️ Something went wrong with the AI service.")


@router.message()
async def save_word_handler(message: Message):

    if message.text and message.text.startswith("/"):
        return

    user = await db.get_user_by_telegram(message.from_user.id)
    if not user:
        return await message.reply("Please use /start first and set your languages.")

    phrase = message.text.strip()

    if len(phrase) > 120:
        return await message.reply("Please send a single word or short phrase (max 120 characters).")

    wait_msg = await message.reply("Looking up translation and example…")

    try:
 
        ai_data = await asyncio.to_thread(ai_service.analyze_phrase, phrase, user["native_lang"], user["learning_lang"])

        saved_doc = await mongo.add_word_for_user(message.from_user.id, phrase, ai_data)

       
        text = (
            f"Saved: {phrase}\n\n"
            f"Translation: {ai_data.get('translation','—')}\n"
            f"Definition: {ai_data.get('definition','—')}\n"
            f"Example: {ai_data.get('example','—')}\n"
            f"{ai_data.get('example_translation','')}"
        )
        await wait_msg.edit_text(text)
    except APIStatusError as e:
        logger.error("AI APIStatusError", exc_info=e)
        await wait_msg.edit_text("AI provider returned an error.")
    except Exception as e:
        logger.exception("Error while saving word")
        await wait_msg.edit_text("Failed to analyze or save the word. Try again later.")
