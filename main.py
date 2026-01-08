import asyncio
import logging
from aiogram import Dispatcher, filters, Bot, F, html
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


welcome_message= "سلام خوشگلهه 🥰. خوش اومدی به دستیار تیچر. من بت کمک میکنم تو یادگیری زبان جدیدت خیلی اسون تر و سریع تر باشی . استفاده ازمم خیلی راحته . میخوای بدونی چطوری ؟پس کلیک کن رو این دستور 👈 /help"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

llm = ChatOpenAI(model="gpt-4.1")
response = llm.invoke("who is the CEO of Apple?")

dp = Dispatcher()

@dp.message(filters.CommandStart())
async def start(message: Message):
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        text=f"{html.bold(welcome_message)}\n{html.bold('name:')} <code>{message.from_user.full_name}</code>\n<b>username:</b>{html.code(message.from_user.username)} \n{html.bold('id:')} {html.code(message.from_user.id)} \n {html.bold('premium:')} {'✅' if message.from_user.is_premium else '❌'}",
        parse_mode=ParseMode.HTML
    )

@dp.message(filters.Command("self", prefix="/"))
async def self_(message: Message):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ELON", callback_data="MUSK")],
            [InlineKeyboardButton(text="danoush", callback_data="vahdat")],
            [InlineKeyboardButton(text="MARYAM", url="https://en.wikipedia.org/wiki/Maryam_Mirzakhani")],
            [InlineKeyboardButton(text="Help", callback_data="help")],
        ]
    )
    await message.answer(text="چیه", reply_markup=markup)

@dp.message(F.text == "keyhan's butt")
async def handle_everything(message: Message):
    await message.reply(text=message.text)

@dp.message(filters.Command("help", prefix="/"))
async def help(message: Message):
    await message.answer(text="ازینجا ببعدش برای تو که دولوپش کنی  : ).")

@dp.callback_query()
async def callback(call: CallbackQuery):
    logger.info(f"Callback query from user {call.from_user.id}: {call.data}")
    if call.data == "help":
        await call.message.answer(text="چگونه می‌توانم به شما کمک کنم؟")
    else:
        await call.message.answer(text="ادم خوبیه")

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(token=token)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
