from aiogram import Router, F, html
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import logging

import mongo

router = Router()
logger = logging.getLogger(__name__)

class Onboard(StatesGroup):
    native = State()
    learning = State()

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started the bot")
    username = message.from_user.username or "—"
    await message.answer(
        text=(
            f"Welcome to LangAssistBot!\n\n"
            f"{html.bold('name:')} <code>{message.from_user.full_name}</code>\n"
            f"{html.bold('username:')} {html.code(username)}\n"
            f"{html.bold('id:')} {html.code(message.from_user.id)}\n"
            f"{html.bold('premium:')} {'✅' if message.from_user.is_premium else '❌'}\n\n"
            "I'll help you store words you don't know and send short daily reviews.\n"
            "To get started, what is your native language? (e.g., German)"
        ),
        parse_mode=ParseMode.HTML,
    )
    await state.set_state(Onboard.native)

@router.message(Onboard.native)
async def get_native(message: Message, state: FSMContext):
    await state.update_data(native=message.text.strip())
    await message.answer("Great. What language are you learning? (e.g., Spanish)")
    await state.set_state(Onboard.learning)

@router.message(Onboard.learning)
async def get_learning(message: Message, state: FSMContext):
    data = await state.get_data()
    native = data.get("native")
    learning = message.text.strip()
   
    await db.upsert_user(message.from_user.id, native, learning)
    await message.answer(f"Saved languages: native={native}, learning={learning}\nNow send any word/phrase in {learning} and I'll save it for review.")
    await state.clear()

@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        text=(
            "To add a word: just send a single word or short phrase in the language you're learning.\n"
            "Example: `perro`\n\n"
            "Commands:\n"
            "/list — show your saved words\n"
            "/review — trigger an on-demand quick review\n"
            "/clear — remove all saved words (confirmation required)\n"
            "/ai <prompt> — general AI chat (not saved)"
        )
    )

@router.message(Command("list"))
async def list_cmd(message: Message):
    rows = await db.list_words_for_user(message.from_user.id, limit=200)
    if not rows:
        return await message.answer("You have no saved words yet.")
    lines = [f"{r['phrase']} — {r.get('translation','—')} (progress {r.get('progress',0)})" for r in rows]
 
    text = "\n".join(lines)
    if len(text) > 4000:
        text = "\n".join(lines[:80]) + "\n…"
    await message.answer(text)

@router.message(Command("clear"))
async def clear_cmd(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Confirm delete all", callback_data="confirm_clear"),
                InlineKeyboardButton(text="Cancel", callback_data="cancel_clear"),
            ]
        ]
    )
    await message.answer("Are you sure you want to delete all saved words?", reply_markup=keyboard)

@router.callback_query()
async def callback(call: CallbackQuery):
    logger.info(f"Callback query from user {call.from_user.id}: {call.data}")
    await call.answer()
    if call.data == "confirm_clear":
        await db.delete_words_for_user(call.from_user.id)
        await call.message.answer("All saved words deleted.")
    elif call.data == "cancel_clear":
        await call.message.answer("Cancelled.")
    else:
        await call.message.answer("Unknown action.")
