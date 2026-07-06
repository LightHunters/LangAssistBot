import os
import re
from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import db
from ai import build_learning_card


def normalize_text(text: str):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u0600-\u06FF]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def answer_is_close(user_answer: str, expected_answer: str):
    user_answer = normalize_text(user_answer)
    expected_answer = normalize_text(expected_answer)

    if not user_answer or not expected_answer:
        return False

    if user_answer == expected_answer:
        return True

    if user_answer in expected_answer:
        return True

    if expected_answer in user_answer:
        return True

    return False


async def send_help(update: Update):
    await update.message.reply_text(
        "LangAssistBot commands:\n\n"
        "/start - start or continue setup\n"
        "/settings - show your languages\n"
        "/change_languages - change native and target languages\n"
        "/list - show saved words\n"
        "/progress - show learning stats\n"
        "/review - start a 5-word review\n"
        "/clear - delete all saved words with confirmation\n"
        "/cancel - cancel current action\n\n"
        "To save a word, just send it as a normal message."
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = db.get_or_create_user(telegram_id)

    if user["state"] == "ready":
        await update.message.reply_text(
            f"Welcome back.\n\n"
            f"Native language: {user['native_lang']}\n"
            f"Learning: {user['target_lang']}\n\n"
            f"Send me a word or phrase, or use /review."
        )
        return

    await update.message.reply_text(
        "Hi! I’m LangAssistBot.\n\n"
        "First, what is your native language?\n"
        "Example: Persian, German, English"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_help(update)


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = db.get_or_create_user(telegram_id)

    native_lang = user["native_lang"] or "not set"
    target_lang = user["target_lang"] or "not set"

    await update.message.reply_text(
        f"Your settings:\n\n"
        f"Native language: {native_lang}\n"
        f"Learning language: {target_lang}\n\n"
        f"Use /change_languages to set them again."
    )


async def change_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    db.get_or_create_user(telegram_id)
    db.reset_languages(telegram_id)

    context.user_data.clear()

    await update.message.reply_text(
        "Okay, let’s set your languages again.\n\n"
        "What is your native language?"
    )


async def list_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cards = db.list_cards(telegram_id)

    if not cards:
        await update.message.reply_text("You have no saved words yet. Send me a word or phrase.")
        return

    lines = ["Your saved words:\n"]

    for card in cards:
        lines.append(
            f"• {card['phrase']} → {card['translation']}\n"
            f"  Level: {card['difficulty']} | Reviewed: {card['times_reviewed']} | Correct: {card['correct_count']} | Wrong: {card['wrong_count']}"
        )

    await update.message.reply_text("\n".join(lines))


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    stats = db.get_progress_stats(telegram_id)

    if stats["total"] == 0:
        await update.message.reply_text("No progress yet. Send me your first word or phrase.")
        return

    accuracy = 0

    if stats["total_reviews"] > 0:
        accuracy = round((stats["total_correct"] / stats["total_reviews"]) * 100)

    await update.message.reply_text(
        f"Progress:\n\n"
        f"Saved cards: {stats['total']}\n"
        f"Reviewed cards: {stats['reviewed']}\n"
        f"Probably mastered: {stats['mastered']}\n"
        f"Total reviews: {stats['total_reviews']}\n"
        f"Accuracy: {accuracy}%\n\n"
        f"Use /review for a quick session."
    )


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = db.get_or_create_user(telegram_id)

    if user["state"] != "ready":
        await update.message.reply_text("Use /start first so I know your languages.")
        return

    cards = db.get_review_cards(telegram_id, limit=5)

    if not cards:
        await update.message.reply_text("No saved words yet. Send me a word or phrase first.")
        return

    context.user_data["review_session"] = {
        "cards": cards,
        "index": 0,
        "correct": 0,
        "total": len(cards),
    }

    await ask_next_review_question(update, context)


async def ask_next_review_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = context.user_data.get("review_session")

    if not session:
        await update.message.reply_text("No active review session. Use /review to start.")
        return

    index = session["index"]
    cards = session["cards"]

    if index >= len(cards):
        correct = session["correct"]
        total = session["total"]

        context.user_data.pop("review_session", None)
        context.user_data.pop("active_quiz", None)

        await update.message.reply_text(
            f"Review finished.\n\n"
            f"Score: {correct}/{total}\n\n"
            f"Good work. This is exactly how vocabulary sticks."
        )
        return

    card = cards[index]

    context.user_data["active_quiz"] = {
        "card_id": card["id"],
        "phrase": card["phrase"],
        "translation": card["translation"],
        "example_target": card.get("example_target") or "",
        "example_native": card.get("example_native") or "",
    }

    await update.message.reply_text(
        f"Question {index + 1}/{len(cards)}\n\n"
        f"What does “{card['phrase']}” mean?"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    total = db.count_cards(telegram_id)

    if total == 0:
        await update.message.reply_text("Your saved list is already empty.")
        return

    context.user_data.clear()
    context.user_data["pending_clear"] = True

    await update.message.reply_text(
        f"This will delete {total} saved words.\n\n"
        f"Type YES CLEAR to confirm.\n"
        f"Type anything else to cancel."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text("Cancelled.")


async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    active_quiz = context.user_data.get("active_quiz")

    expected = active_quiz["translation"]
    correct = answer_is_close(text, expected)

    db.mark_review(active_quiz["card_id"], correct)

    session = context.user_data.get("review_session")

    if correct:
        if session:
            session["correct"] += 1

        reply = "Correct."
    else:
        reply = (
            f"Not quite.\n\n"
            f"“{active_quiz['phrase']}” means:\n"
            f"{active_quiz['translation']}"
        )

    example_target = active_quiz.get("example_target", "")
    example_native = active_quiz.get("example_native", "")

    if example_target or example_native:
        reply += f"\n\nExample:\n{example_target}\n{example_native}"

    await update.message.reply_text(reply)

    context.user_data.pop("active_quiz", None)

    if session:
        session["index"] += 1
        await ask_next_review_question(update, context)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    if not text:
        return

    if context.user_data.get("pending_clear"):
        if text == "YES CLEAR":
            db.clear_cards(telegram_id)
            context.user_data.clear()
            await update.message.reply_text("Your saved words have been cleared.")
        else:
            context.user_data.clear()
            await update.message.reply_text("Clear cancelled.")
        return

    if context.user_data.get("active_quiz"):
        await handle_quiz_answer(update, context, text)
        return

    user = db.get_or_create_user(telegram_id)

    if user["state"] == "await_native":
        db.set_native_language(telegram_id, text)
        await update.message.reply_text(
            f"Great. Your native language is {text}.\n\n"
            f"What language are you learning?"
        )
        return

    if user["state"] == "await_target":
        db.set_target_language(telegram_id, text)
        await update.message.reply_text(
            f"Perfect. You are learning {text}.\n\n"
            f"Now send me any word or phrase you find while reading."
        )
        return

    if user["state"] != "ready":
        await update.message.reply_text("Use /start first.")
        return

    if len(text) > 200:
        await update.message.reply_text("Send a shorter word or phrase. Keep it under 200 characters.")
        return

    await update.message.reply_text("Making a learning card...")

    try:
        card = build_learning_card(
            phrase=text,
            native_lang=user["native_lang"],
            target_lang=user["target_lang"],
        )
    except Exception as error:
        await update.message.reply_text(
            f"I could not create the card.\n\n"
            f"Error: {error}"
        )
        return

    db.save_card(telegram_id, card)

    reply = (
        f"📌 {card['phrase']}\n\n"
        f"Translation: {card['translation']}\n"
        f"Definition: {card['definition']}\n"
        f"Pronunciation: {card['pronunciation']}\n"
        f"Part of speech: {card['part_of_speech']}\n"
        f"Difficulty: {card['difficulty']}\n\n"
        f"Example:\n"
        f"{card['example_target']}\n"
        f"{card['example_native']}\n\n"
        f"Saved. Use /review for a quick session."
    )

    await update.message.reply_text(reply)


def main():
    db.init_db()

    token = os.getenv("BOT_TOKEN", "").strip()

    if not token:
        raise RuntimeError("Missing BOT_TOKEN in .env")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("change_languages", change_languages))
    app.add_handler(CommandHandler("list", list_words))
    app.add_handler(CommandHandler("progress", progress))
    app.add_handler(CommandHandler("review", review))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("LangAssistBot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()