from aiogram import Router, filters, F, html
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
import logging
import config

router = Router()
logger = logging.getLogger(__name__)

@router.message(filters.CommandStart())
async def start(message: Message):
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        text=f"{html.bold(config.WELCOME_MESSAGE)}\n"
             f"{html.bold('name:')} <code>{message.from_user.full_name}</code>\n"
             f"<b>username:</b>{html.code(message.from_user.username)} \n"
             f"{html.bold('id:')} {html.code(message.from_user.id)} \n"
             f"{html.bold('premium:')} {'✅' if message.from_user.is_premium else '❌'}",
        parse_mode=ParseMode.HTML
    )

@router.message(filters.Command("self", prefix="/"))
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

@router.message(filters.Command("help", prefix="/"))
async def help(message: Message):
    await message.answer(text="ازینجا ببعدش برای تو که دولوپش کنی  : ).")

@router.message(F.text == "keyhan's butt")
async def handle_everything(message: Message):
    await message.reply(text=message.text)

@router.callback_query()
async def callback(call: CallbackQuery):
    logger.info(f"Callback query from user {call.from_user.id}: {call.data}")
    if call.data == "help":
        await call.message.answer(text="چگونه می‌توانم به شما کمک کنم؟")
    else:
        await call.message.answer(text="ادم خوبیه")
