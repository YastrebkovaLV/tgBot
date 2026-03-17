import os
import asyncio
import subprocess
import tempfile
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.error import Conflict

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден. Проверь файл .env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Отправь Python код так:\n\n"
        "#python\n"
        "print('Hello')"
    )


def extract_code(text: str):
    if text.startswith("#python"):
        return text.replace("#python", "", 1).strip()
    return None


async def check_code(update: Update, code: str):
    msg = await update.message.reply_text("⏳ Проверяю код...")

    temp_file = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(code)
            temp_file = f.name

        result = subprocess.run(
            ["pylint", temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            text = "✅ Ошибок не найдено"
        else:
            output = result.stdout or result.stderr
            text = f"❌ Ошибки:\n<code>{output[:3500]}</code>"

    except Exception as e:
        text = f"⚠️ Ошибка: {str(e)}"

    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

    await msg.edit_text(text, parse_mode="HTML")


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    code = extract_code(update.message.text)

    if not code:
        await update.message.reply_text("❌ Напиши код с #python в начале")
        return

    await check_code(update, code)


async def error_handler(update, context):
    if isinstance(context.error, Conflict):
        logging.warning("⚠️ Conflict — сбрасываю webhook...")
        try:
            await context.bot.delete_webhook(drop_pending_updates=True)
        except Exception as e:
            logging.error(f"Webhook error: {e}")
    else:
        logging.error("Ошибка:", exc_info=context.error)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_error_handler(error_handler)

    print("🚀 Бот запущен")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":

    main()