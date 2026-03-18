import os
import random
import asyncio
import sqlite3
import io
import logging
import matplotlib.pyplot as plt
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================== LOAD ENV ==================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_PATH = os.getenv("DATABASE_PATH", "casino.db")

# ================== LOGGING ==================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ================== DATABASE ==================

conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 100,
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        games INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    logger.info("База данных инициализирована")

def user_exists(user_id):
    cursor.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None

def create_user(user_id, username):
    cursor.execute("""
    INSERT OR IGNORE INTO users (user_id, username)
    VALUES (?, ?)
    """, (user_id, username))
    conn.commit()
    logger.info(f"Создан пользователь {username} ({user_id})")

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "balance": row[2],
        "level": row[3],
        "xp": row[4],
        "games": row[5],
        "wins": row[6],
        "losses": row[7],
    }

def update_user(user):
    cursor.execute("""
    UPDATE users SET
        username=?, balance=?, level=?, xp=?,
        games=?, wins=?, losses=?
    WHERE user_id=?
    """, (
        user["username"],
        user["balance"],
        user["level"],
        user["xp"],
        user["games"],
        user["wins"],
        user["losses"],
        user["user_id"]
    ))
    conn.commit()

# ================== KEYBOARDS ==================

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Игры", callback_data="games")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("📊 График", callback_data="graph")],
    ])

def games_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 Слот", callback_data="slot")],
        [InlineKeyboardButton("🎲 Кубик", callback_data="dice")],
        [InlineKeyboardButton("🪙 Монетка", callback_data="coin")],
        [InlineKeyboardButton("⬅ Назад", callback_data="back")]
    ])

# ================== GRAPH ==================

def create_graph(wins, losses):

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(6,4))

    bars = ax.bar(
        ["Победы", "Поражения"],
        [wins, losses],
        color=["#00ff88", "#ff4d4d"]
    )

    ax.set_title("Статистика игрока")
    ax.set_ylabel("Количество")

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2,
                height,
                str(height),
                ha='center',
                va='bottom')

    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plt.close()

    return buffer

# ================== START ==================

registering_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    username = update.effective_user.username or "NoName"

    logger.info(f"/start от {user_id}")

    if not user_exists(user_id):
        registering_users.add(user_id)
        await update.message.reply_text("👋 Введите ник для регистрации:")
        return

    await update.message.reply_text(
        "🎰 Добро пожаловать!",
        reply_markup=main_keyboard()
    )

# ================== REGISTRATION ==================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in registering_users:
        return

    username = update.message.text.strip()

    if len(username) < 3:
        await update.message.reply_text("❌ Ник минимум 3 символа")
        return

    create_user(user_id, username)
    registering_users.remove(user_id)

    await update.message.reply_text("✅ Регистрация завершена!")
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=main_keyboard()
    )

# ================== BUTTONS ==================

processing_users = set()

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if not user_exists(user_id):
        await query.message.edit_text("❌ Сначала /start")
        return

    if user_id in processing_users:
        return

    processing_users.add(user_id)

    try:

        user = get_user(user_id)

        if query.data == "back":
            await query.message.edit_text(
                "🎰 Главное меню",
                reply_markup=main_keyboard()
            )

        elif query.data == "games":
            await query.message.edit_text(
                "🎮 Выберите игру:",
                reply_markup=games_keyboard()
            )

        elif query.data == "profile":

            winrate = round((user["wins"]/user["games"])*100,1) if user["games"] else 0

            text = f"""
👤 ПРОФИЛЬ

🎮 Ник: {user['username']}
💰 Баланс: {user['balance']}
⭐ Уровень: {user['level']}

🎰 Игр: {user['games']}
🏆 Побед: {user['wins']}
❌ Поражений: {user['losses']}
📊 Winrate: {winrate}%
"""

            await query.message.edit_text(
                text,
                reply_markup=main_keyboard()
            )

        elif query.data == "graph":

            buffer = create_graph(user["wins"], user["losses"])

            await query.message.reply_photo(
                photo=buffer,
                caption="📊 Статистика",
                reply_markup=main_keyboard()
            )

        # ===== SLOT =====
        elif query.data == "slot":

            bet = 20

            if user["balance"] < bet:
                await query.message.edit_text("❌ Недостаточно средств", reply_markup=main_keyboard())
                return

            user["games"] += 1
            user["balance"] -= bet

            symbols = ["🍒","🍋","🍉","⭐","🔔","💎"]
            result = [random.choice(symbols) for _ in range(3)]

            await asyncio.sleep(0.5)

            if result[0] == result[1] == result[2]:
                win = bet * 5
                user["balance"] += win
                user["wins"] += 1
                text = f"🎰 {' | '.join(result)}\n🏆 +{win}"
            else:
                user["losses"] += 1
                text = f"🎰 {' | '.join(result)}\n❌ -{bet}"

            await query.message.edit_text(text, reply_markup=main_keyboard())

        update_user(user)

    except Exception as e:
        logger.exception("Ошибка в обработке кнопки")

    finally:
        processing_users.discard(user_id)

# ================== RUN ==================

def main():

    if not TOKEN:
        logger.error("BOT_TOKEN не найден в .env")
        return

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Бот запущен")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()