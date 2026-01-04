import asyncio
from aiogram import Dispatcher, filters, Bot ,F , html
from aiogram.types import Message,CallbackQuery ,ReplyKeyboardMarkup , KeyboardButton , InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
import os
from dotenv import load_dotenv

load_dotenv()

dp = Dispatcher()


@dp.message(filters.CommandStart())
async def start(message: Message):
    await message.answer(
        text=f"{html.bold('name:')} <code>{message.from_user.full_name}</code>\n<b>username:</b>{html.code(message.from_user.username)} \n{html.bold('id:')} {html.code(message.from_user.id)} \n {html.bold('premium:')} {'✅'if message.from_user.is_premium else '❌'}",
        parse_mode=ParseMode.HTML
        )


@dp.message(filters.Command("self", prefix="/"))
async def self_(message: Message):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[ 
            [InlineKeyboardButton(text="ELON",callback_data="MUSK")],
            [InlineKeyboardButton(text="danoush",callback_data="vahdat")],
            [InlineKeyboardButton(text="MARYAM", url="https://en.wikipedia.org/wiki/Maryam_Mirzakhani")],
        ]
    )
    await message.answer(text="چیه", reply_markup=markup)



@dp.message(F.text=="keyhan's butt")
async def handle_everything(message: Message):
    await message.reply(text=message.text)  

@dp.callback_query()
async def callback(call:CallbackQuery ):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text= "ادم خوبیه"
    )

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(token=token)
    await dp.start_polling(bot)


if __name__== "__main__" :
     asyncio.run(main())
     