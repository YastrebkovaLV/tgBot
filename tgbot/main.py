import os
import random
import sqlite3
import logging
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_PATH = os.getenv("DATABASE_PATH", "casino.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
conn.execute("PRAGMA temp_store=MEMORY;")
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 100,
        games INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0
    )
    """)
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "balance": row[2],
        "games": row[3],
        "wins": row[4],
        "losses": row[5],
    }

def create_user(user_id, username):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user_id, username),
    )
    conn.commit()

def update_user(user):
    cursor.execute("""
    UPDATE users SET
        username=?, balance=?, games=?, wins=?, losses=?
    WHERE user_id=?
    """, (
        user["username"],
        user["balance"],
        user["games"],
        user["wins"],
        user["losses"],
        user["user_id"],
    ))
    conn.commit()

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Игры", callback_data="games")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
    ])

def games_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 Слот", callback_data="slot")],
        [InlineKeyboardButton("🎲 Кубик", callback_data="dice")],
        [InlineKeyboardButton("🪙 Монетка", callback_data="coin")],
        [InlineKeyboardButton("⬅ Назад", callback_data="back")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    username = update.effective_user.username or "NoName"

    if not get_user(user_id):
        create_user(user_id, username)

    await update.message.reply_text(
        "🚀 Казино запущено!",
        reply_markup=main_keyboard()
    )

processing = set()

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id in processing:
        return

    processing.add(user_id)

    try:

        user = get_user(user_id)
        if not user:
            await query.message.edit_text("Нажмите /start")
            return

        if query.data == "games":
            await query.message.edit_text(
                "Выберите игру:",
                reply_markup=games_keyboard()
            )

        elif query.data == "back":
            await query.message.edit_text(
                "Главное меню",
                reply_markup=main_keyboard()
            )

        elif query.data == "profile":

            text = (
                f"👤 {user['username']}\n\n"
                f"💰 Баланс: {user['balance']}\n"
                f"🎮 Игр: {user['games']}\n"
                f"🏆 Побед: {user['wins']}\n"
                f"❌ Поражений: {user['losses']}"
            )

            await query.message.edit_text(text, reply_markup=main_keyboard())

        elif query.data == "slot":

            bet = 20
            if user["balance"] < bet:
                await query.message.edit_text("❌ Нет средств", reply_markup=main_keyboard())
                return

            user["games"] += 1
            user["balance"] -= bet

            symbols = ["🍒","🍋","🍉","⭐","🔔","💎"]
            result = [random.choice(symbols) for _ in range(3)]

            if result[0] == result[1] == result[2]:
                win = bet * 5
                user["balance"] += win
                user["wins"] += 1
                text = f"🎰 {' | '.join(result)}\n🏆 +{win}"
            else:
                user["losses"] += 1
                text = f"🎰 {' | '.join(result)}\n❌ -{bet}"

            await query.message.edit_text(text, reply_markup=main_keyboard())

        elif query.data == "dice":

            bet = 10
            if user["balance"] < bet:
                await query.message.edit_text("❌ Нет средств", reply_markup=main_keyboard())
                return

            user["games"] += 1
            user["balance"] -= bet

            value = random.randint(1, 6)

            if value >= 4:
                win = bet * 2
                user["balance"] += win
                user["wins"] += 1
                text = f"🎲 {value}\n🏆 +{win}"
            else:
                user["losses"] += 1
                text = f"🎲 {value}\n❌ -{bet}"

            await query.message.edit_text(text, reply_markup=main_keyboard())

        elif query.data == "coin":

            bet = 5
            if user["balance"] < bet:
                await query.message.edit_text("❌ Нет средств", reply_markup=main_keyboard())
                return

            user["games"] += 1
            user["balance"] -= bet

            result = random.choice(["Орёл", "Решка"])

            if result == "Орёл":
                win = bet * 2
                user["balance"] += win
                user["wins"] += 1
                text = f"🪙 {result}\n🏆 +{win}"
            else:
                user["losses"] += 1
                text = f"🪙 {result}\n❌ -{bet}"

            await query.message.edit_text(text, reply_markup=main_keyboard())

        update_user(user)

    except Exception:
        logger.exception("Ошибка")

    finally:
        processing.discard(user_id)
def main():

    if not TOKEN:
        logger.error("BOT_TOKEN не найден")
        return

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Бот максимально оптимизирован и запущен")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()