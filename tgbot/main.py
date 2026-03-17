import os
import random
import asyncio
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

users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 100,
            "level": 1,
            "xp": 0,
            "games": 0,
            "wins": 0,
            "losses": 0,
        }
    return users[user_id]

def update_level(user):
    if user["xp"] >= 100:
        user["level"] += 1
        user["xp"] = 0

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 Слот", callback_data="slot")],
        [InlineKeyboardButton("🎲 Кубик", callback_data="dice")],
        [InlineKeyboardButton("🪙 Монетка", callback_data="coin")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🔄 Перезапуск", callback_data="restart")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Перезапуск", callback_data="restart")]
    ])

async def show_menu(message, user):
    text = "🎰 <b>CASINO ULTRA</b>\n\nВыберите игру 👇"
    await message.edit_text(
        text,
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )

async def win_animation(message, final_text):
    for _ in range(3):
        await message.edit_text("✨")
        await asyncio.sleep(0.15)
        await message.edit_text("🎉")
        await asyncio.sleep(0.15)
    await message.edit_text(final_text, reply_markup=back_keyboard())

async def smooth_slot(message):
    symbols = ["🍒", "🍋", "🍉", "⭐", "🔔", "💎"]
    reels = ["❓", "❓", "❓"]

    for i in range(12):
        reels[0] = random.choice(symbols)
        if i > 3:
            reels[1] = random.choice(symbols)
        if i > 7:
            reels[2] = random.choice(symbols)

        await message.edit_text(f"🎰 {' | '.join(reels)}")
        await asyncio.sleep(0.12)

    return [random.choice(symbols) for _ in range(3)]

async def dice_animation(message):
    dice_msg = await message.reply_dice(emoji="🎲")
    await asyncio.sleep(3)
    value = dice_msg.dice.value
    try:
        await dice_msg.delete()
    except:
        pass
    return value

async def coin_animation(message):
    frames = ["🪙 Орёл или решка...", "🪙 Крутим...", "🪙 Почти готово..."]
    for frame in frames:
        await message.edit_text(frame)
        await asyncio.sleep(0.4)

    result = random.choice(["Орёл", "Решка"])
    return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    message = await update.message.reply_text("🎰 Загрузка...")
    await show_menu(message, user)

async def restart_to_menu(query):
    user = get_user(query.from_user.id)
    await show_menu(query.message, user)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)

    if query.data == "restart":
        await restart_to_menu(query)
        return

    if query.data == "stats":
        games = user["games"]
        wins = user["wins"]
        losses = user["losses"]
        winrate = round((wins / games) * 100, 1) if games > 0 else 0

        text = (
            "📊 <b>СТАТИСТИКА</b>\n\n"
            f"🎮 Игр: <b>{games}</b>\n"
            f"🏆 Побед: <b>{wins}</b>\n"
            f"❌ Поражений: <b>{losses}</b>\n"
            f"📈 Winrate: <b>{winrate}%</b>"
        )

        await query.message.edit_text(text, reply_markup=main_keyboard(), parse_mode="HTML")
        return

    if query.data == "slot":
        bet = 20
        if user["balance"] < bet:
            await query.message.edit_text("❌ Недостаточно монет!", reply_markup=back_keyboard())
            return

        user["games"] += 1
        result = await smooth_slot(query.message)

        if result[0] == result[1] == result[2]:
            win = bet * 5
            user["balance"] += win
            user["xp"] += 30
            user["wins"] += 1
            update_level(user)

            await win_animation(
                query.message,
                f"🎰 {' | '.join(result)}\n\n🏆 ДЖЕКПОТ +{win}"
            )
        else:
            user["balance"] -= bet
            user["losses"] += 1

            await query.message.edit_text(
                f"🎰 {' | '.join(result)}\n\n😢 -{bet}",
                reply_markup=back_keyboard()
            )

    elif query.data == "dice":
        bet = 10
        if user["balance"] < bet:
            await query.message.edit_text("❌ Недостаточно монет!", reply_markup=back_keyboard())
            return

        user["games"] += 1
        value = await dice_animation(query.message)

        if value >= 4:
            user["balance"] += bet
            user["xp"] += 20
            user["wins"] += 1
            update_level(user)

            await win_animation(
                query.message,
                f"🎲 Выпало {value}\n🎉 Победа +{bet}"
            )
        else:
            user["balance"] -= bet
            user["losses"] += 1

            await query.message.edit_text(
                f"🎲 Выпало {value}\n😢 Проигрыш -{bet}",
                reply_markup=back_keyboard()
            )

    elif query.data == "coin":
        bet = 5
        if user["balance"] < bet:
            await query.message.edit_text("❌ Недостаточно монет!", reply_markup=back_keyboard())
            return

        user["games"] += 1
        result = await coin_animation(query.message)

        if result == "Орёл":
            user["balance"] += bet
            user["xp"] += 10
            user["wins"] += 1
            update_level(user)

            await win_animation(query.message, "🪙 ОРЁЛ!\n🎉 Победа!")
        else:
            user["balance"] -= bet
            user["losses"] += 1

            await query.message.edit_text(
                "🪙 РЕШКА!\n😢 Поражение",
                reply_markup=back_keyboard()
            )

def main():
    if not TOKEN:
        print("❌ BOT_TOKEN не найден")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🎰 Казино запущено...")
    app.run_polling()

if __name__ == "__main__":
    main()