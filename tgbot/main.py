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

# 🔐 Загружаем токен
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


# 🏠 Главное меню
async def main_menu(message):
    keyboard = [
        [InlineKeyboardButton("🧪 Проверить Python-код", callback_data="check_code")],
        [InlineKeyboardButton("💡 Советы по коду", callback_data="recommend")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "🤖 <b>Добро пожаловать!</b>\n\n"
        "Я бот для проверки Python-кода 🐍\n"
        "Выберите действие ниже 👇",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


# 👋 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_for_code"] = False
    await main_menu(update.message)


# 🔘 Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 🧪 Проверка кода
    if query.data == "check_code":
        context.user_data["waiting_for_code"] = True

        keyboard = [
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
        ]

        await query.message.reply_text(
            "✏️ <b>Отправьте Python-код</b>\n\n"
            "Я выполню его и покажу результат.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )

    # 💡 Советы
    elif query.data == "recommend":
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
        ]

        await query.message.reply_text(
            "💡 <b>Полезные советы:</b>\n\n"
            "• Проверяйте отступы\n"
            "• Используйте print() для вывода\n"
            "• Не используйте опасные операции\n"
            "• Пишите чистый и читаемый код\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )

    # ℹ️ О боте
    elif query.data == "about":
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
        ]

        await query.message.reply_text(
            "ℹ️ <b>О боте</b>\n\n"
            "Этот бот выполняет Python-код и проверяет его на ошибки.\n"
            "Создан для обучения и тестирования 🐍",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )

    # 🔙 Назад
    elif query.data == "back":
        context.user_data["waiting_for_code"] = False
        await main_menu(query.message)


# 🧠 Проверка кода
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for_code"):
        return

    context.user_data["waiting_for_code"] = False
    user_code = update.message.text

    try:
        # Безопасная среда выполнения
        local_vars = {}
        exec(user_code, {"__builtins__": {}}, local_vars)

        await update.message.reply_text(
            "✅ <b>Код выполнен успешно!</b>\nОшибок не найдено.",
            parse_mode="HTML",
        )

    except Exception:
        error_message = traceback.format_exc()

        await update.message.reply_text(
            "❌ <b>Ошибка в коде:</b>\n\n"
            f"<code>{error_message}</code>",
            parse_mode="HTML",
        )


# 🚀 Запуск бота
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