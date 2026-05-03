import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
from datetime import datetime

TOKEN = os.getenv("TOKEN")

conn = sqlite3.connect("aghor.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    target_minutes INTEGER,
    points INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    user_id INTEGER,
    date TEXT,
    todo INTEGER DEFAULT 0,
    complete INTEGER DEFAULT 0,
    ypt_minutes INTEGER DEFAULT 0
)
""")
conn.commit()

def parse_time_to_minutes(time_str):
    try:
        h, m = map(int, time_str.split(":"))
        return h*60 + m
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to AGHOR 🔥\n\n"
        "Send your previous week avg study time\n"
        "Format: HH:MM (example: 05:30)\n"
        "OR type 'new'"
    )

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    name = update.message.from_user.first_name
    text = update.message.text

    if text.lower() == "new":
        target = 0
    else:
        target = parse_time_to_minutes(text)
        if target is None:
            await update.message.reply_text("Invalid format. Use HH:MM or 'new'")
            return

    cursor.execute("INSERT OR REPLACE INTO users (user_id, name, target_minutes) VALUES (?, ?, ?)",
                   (user_id, name, target))
    conn.commit()

    await update.message.reply_text("Registered ✅")

async def todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    date = str(datetime.now().date())

    cursor.execute("INSERT OR IGNORE INTO logs (user_id, date) VALUES (?, ?)", (user_id, date))
    cursor.execute("UPDATE logs SET todo=1 WHERE user_id=? AND date=?", (user_id, date))
    cursor.execute("UPDATE users SET points = points + 2 WHERE user_id=?", (user_id,))
    conn.commit()

    await update.message.reply_text("Todo +2 points ✅")

async def complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    date = str(datetime.now().date())

    cursor.execute("UPDATE logs SET complete=1 WHERE user_id=? AND date=?", (user_id, date))
    cursor.execute("UPDATE users SET points = points + 2 WHERE user_id=?", (user_id,))
    conn.commit()

    await update.message.reply_text("Completed +2 🔥")

async def ypt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not context.args:
        await update.message.reply_text("Use: /YPT 05:30")
        return

    minutes = parse_time_to_minutes(context.args[0])
    if minutes is None:
        await update.message.reply_text("Invalid format")
        return

    cursor.execute("SELECT target_minutes FROM users WHERE user_id=?", (user_id,))
    target = cursor.fetchone()
    target = target[0] if target else 0

    points = 2 if minutes > target else -1

    date = str(datetime.now().date())

    cursor.execute("UPDATE logs SET ypt_minutes=? WHERE user_id=? AND date=?", (minutes, user_id, date))
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (points, user_id))
    conn.commit()

    await update.message.reply_text(f"YPT {context.args[0]} | Points: {points}")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT 10")
    rows = cursor.fetchall()

    text = "🏆 Leaderboard\n\n"
    for i, (name, pts) in enumerate(rows, 1):
        text += f"{i}. {name} - {pts}\n"

    await update.message.reply_text(text)

print("TOKEN:", TOKEN)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("todo", todo))
app.add_handler(CommandHandler("complete", complete))
app.add_handler(CommandHandler("YPT", ypt))
app.add_handler(CommandHandler("leaderboard", leaderboard))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration))

print("Bot running...")
app.run_polling()
