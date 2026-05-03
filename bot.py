import asyncio
import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== DATABASE =====
conn = sqlite3.connect("aghor.db")
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

def parse_time_to_minutes(t):
    try:
        h, m = map(int, t.split(":"))
        return h*60 + m
    except:
        return None

# ===== COMMANDS =====
@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer(
        "🔥 AGHOR 🔥\n\n"
        "Send your avg study time (HH:MM) or type 'new'"
    )

@dp.message()
async def register(msg: types.Message):
    user_id = msg.from_user.id
    name = msg.from_user.first_name
    text = msg.text

    if text.startswith("/"):
        return

    if text.lower() == "new":
        target = 0
    else:
        target = parse_time_to_minutes(text)
        if target is None:
            await msg.answer("Invalid format")
            return

    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, COALESCE((SELECT points FROM users WHERE user_id=?),0))",
                   (user_id, name, target, user_id))
    conn.commit()

    await msg.answer("✅ Registered")

@dp.message(Command("todo"))
async def todo(msg: types.Message):
    user_id = msg.from_user.id
    date = str(datetime.now().date())

    cursor.execute("INSERT OR IGNORE INTO logs VALUES (?, ?, 0, 0, 0)", (user_id, date))
    cursor.execute("UPDATE logs SET todo=1 WHERE user_id=? AND date=?", (user_id, date))
    cursor.execute("UPDATE users SET points = points + 2 WHERE user_id=?", (user_id,))
    conn.commit()

    await msg.answer("📌 Todo +2")

@dp.message(Command("complete"))
async def complete(msg: types.Message):
    user_id = msg.from_user.id
    date = str(datetime.now().date())

    cursor.execute("UPDATE logs SET complete=1 WHERE user_id=? AND date=?", (user_id, date))
    cursor.execute("UPDATE users SET points = points + 2 WHERE user_id=?", (user_id,))
    conn.commit()

    await msg.answer("✅ Completed +2")

@dp.message(Command("YPT"))
async def ypt(msg: types.Message):
    user_id = msg.from_user.id
    parts = msg.text.split()

    if len(parts) < 2:
        await msg.answer("Use: /YPT 05:30")
        return

    minutes = parse_time_to_minutes(parts[1])
    if minutes is None:
        await msg.answer("Invalid format")
        return

    cursor.execute("SELECT target_minutes FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    target = result[0] if result else 0

    points = 2 if minutes > target else -1
    date = str(datetime.now().date())

    cursor.execute("UPDATE logs SET ypt_minutes=? WHERE user_id=? AND date=?", (minutes, user_id, date))
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (points, user_id))
    conn.commit()

    await msg.answer(f"⏱ {parts[1]} | Points: {points}")

@dp.message(Command("leaderboard"))
async def leaderboard(msg: types.Message):
    cursor.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT 10")
    rows = cursor.fetchall()

    text = "🏆 Leaderboard\n\n"
    for i, (name, pts) in enumerate(rows, 1):
        text += f"{i}. {name} - {pts}\n"

    await msg.answer(text)

# ===== RUN =====
async def main():
    print("🔥 Bot running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
