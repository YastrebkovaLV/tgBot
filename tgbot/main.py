import os
import random
import asyncio
import sqlite3
import io
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

# ================== CONFIG ==================

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# ================== DATABASE ==================

conn = sqlite3.connect("casino.db", check_same_thread=False)
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

def user_exists(user_id):
    cursor.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None

def create_user(user_id, username):
    cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)",
                   (user_id, username))
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

# ================== KEYBOARD ==================

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Игры", callback_data="games")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("📊 График", callback_data="graph")],
        [InlineKeyboardButton("🔄 Перезапуск", callback_data="restart")],
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

    ax.set_title("📊 Статистика игрока")
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

        # ===== MENU =====
        if query.data == "games":
            await query.message.edit_text(
                "🎮 Выберите игру:",
                reply_markup=games_keyboard()
            )

        elif query.data == "back":
            await query.message.edit_text(
                "🎰 Главное меню",
                reply_markup=main_keyboard()
            )

        elif query.data == "profile":

            winrate = round((user["wins"]/user["games"])*100,1) if user["games"] else 0

            text = f"""
👤 <b>ПРОФИЛЬ</b>

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
                parse_mode="HTML",
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
                text = f"🎰 {' | '.join(result)}\n\n🏆 ВЫИГРЫШ +{win}"
            else:
                user["losses"] += 1
                text = f"🎰 {' | '.join(result)}\n\n❌ ПРОИГРАЛ -{bet}"

            await query.message.edit_text(text, reply_markup=main_keyboard())

        # ===== DICE =====
        elif query.data == "dice":

            bet = 10

            if user["balance"] < bet:
                await query.message.edit_text("❌ Недостаточно средств", reply_markup=main_keyboard())
                return

            user["games"] += 1
            user["balance"] -= bet

            value = random.randint(1,6)

            await asyncio.sleep(0.5)

            if value >= 4:
                win = bet * 2
                user["balance"] += win
                user["wins"] += 1
                text = f"🎲 {value}\n\n🏆 ВЫИГРЫШ +{win}"
            else:
                user["losses"] += 1
                text = f"🎲 {value}\n\n❌ ПРОИГРАЛ -{bet}"

            await query.message.edit_text(text, reply_markup=main_keyboard())

        # ===== COIN =====
        elif query.data == "coin":

            bet = 5

            if user["balance"] < bet:
                await query.message.edit_text("❌ Недостаточно средств", reply_markup=main_keyboard())
                return

            user["games"] += 1
            user["balance"] -= bet

            result = random.choice(["Орёл","Решка"])

            await asyncio.sleep(0.5)

            if result == "Орёл":
                win = bet * 2
                user["balance"] += win
                user["wins"] += 1
                text = f"🪙 {result}\n\n🏆 ВЫИГРЫШ +{win}"
            else:
                user["losses"] += 1
                text = f"🪙 {result}\n\n❌ ПРОИГРАЛ -{bet}"

            await query.message.edit_text(text, reply_markup=main_keyboard())

        update_user(user)

    finally:
        processing_users.discard(user_id)

# ================== RUN ==================

def main():

    if not TOKEN:
        print("❌ BOT_TOKEN не найден")
        return

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Казино полностью работает")
    app.run_polling()

if __name__ == "__main__":
    main()