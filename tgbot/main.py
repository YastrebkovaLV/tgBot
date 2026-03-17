import os
import traceback
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# 🔐 Загружаем переменные из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Состояние ожидания кода
WAITING_FOR_CODE = False


# 👋 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧪 Проверить код", callback_data="check_code")],
        [InlineKeyboardButton("💡 Рекомендации", callback_data="recommend")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я бот для проверки реального Python-кода.\n"
        "Выберите действие:",
        reply_markup=reply_markup,
    )


# 🔘 Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global WAITING_FOR_CODE

    query = update.callback_query
    await query.answer()

    if query.data == "check_code":
        WAITING_FOR_CODE = True
        await query.message.reply_text(
            "✏️ Отправьте Python-код.\n"
            "Я выполню его и проверю на ошибки."
        )

    elif query.data == "recommend":
        await query.message.reply_text(
            "💡 Рекомендации:\n"
            "- Проверяйте отступы\n"
            "- Не используйте опасные операции\n"
            "- Код должен быть корректным Python\n"
            "- Используйте print() для вывода результата"
        )


# 🧠 Проверка реального Python-кода
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global WAITING_FOR_CODE

    if not WAITING_FOR_CODE:
        return

    WAITING_FOR_CODE = False
    user_code = update.message.text

    try:
        # Создаем безопасное пространство выполнения
        local_vars = {}

        # Выполняем код
        exec(user_code, {"__builtins__": {}}, local_vars)

        await update.message.reply_text("✅ Код выполнен успешно! Ошибок нет.")

    except Exception:
        error_message = traceback.format_exc()

        await update.message.reply_text(
            "❌ В коде есть ошибка:\n\n"
            f"{error_message}"
        )


def main():
    if not TOKEN:
        print("❌ Токен не найден в .env файле")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))

    print("🤖 Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()