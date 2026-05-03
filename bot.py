import telebot
import sqlite3
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

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

def parse_time(t):
    try:
        h, m = map(int, t.split(":"))
        return h*60 + m
    except:
        return None

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "🔥 AGHOR 🔥\nSend time (HH:MM) or 'new'")

@bot.message_handler(commands=['todo'])
def todo(msg):
    uid = msg.from_user.id
    date = str(datetime.now().date())

    cursor.execute("INSERT OR IGNORE INTO logs VALUES (?, ?, 0, 0, 0)", (uid, date))
    cursor.execute("UPDATE logs SET todo=1 WHERE user_id=? AND date=?", (uid, date))
    cursor.execute("UPDATE users SET points = points + 2 WHERE user_id=?", (uid,))
    conn.commit()

    bot.reply_to(msg, "📌 Todo +2")

@bot.message_handler(commands=['complete'])
def complete(msg):
    uid = msg.from_user.id
    date = str(datetime.now().date())

    cursor.execute("UPDATE logs SET complete=1 WHERE user_id=? AND date=?", (uid, date))
    cursor.execute("UPDATE users SET points = points + 2 WHERE user_id=?", (uid,))
    conn.commit()

    bot.reply_to(msg, "✅ Completed +2")

@bot.message_handler(commands=['YPT'])
def ypt(msg):
    uid = msg.from_user.id
    try:
        time_str = msg.text.split()[1]
    except:
        bot.reply_to(msg, "Use: /YPT 05:30")
        return

    mins = parse_time(time_str)
    if mins is None:
        bot.reply_to(msg, "Invalid format")
        return

    cursor.execute("SELECT target_minutes FROM users WHERE user_id=?", (uid,))
    res = cursor.fetchone()
    target = res[0] if res else 0

    pts = 2 if mins > target else -1
    date = str(datetime.now().date())

    cursor.execute("UPDATE logs SET ypt_minutes=? WHERE user_id=? AND date=?", (mins, uid, date))
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (pts, uid))
    conn.commit()

    bot.reply_to(msg, f"⏱ {time_str} | Points: {pts}")

@bot.message_handler(commands=['leaderboard'])
def leaderboard(msg):
    cursor.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT 10")
    rows = cursor.fetchall()

    text = "🏆 Leaderboard\n\n"
    for i, (name, pts) in enumerate(rows, 1):
        text += f"{i}. {name} - {pts}\n"

    bot.reply_to(msg, text)

@bot.message_handler(func=lambda m: True)
def register(msg):
    if msg.text.startswith("/"):
        return

    uid = msg.from_user.id
    name = msg.from_user.first_name

    if msg.text.lower() == "new":
        target = 0
    else:
        target = parse_time(msg.text)
        if target is None:
            bot.reply_to(msg, "Invalid format")
            return

    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, COALESCE((SELECT points FROM users WHERE user_id=?),0))",
                   (uid, name, target, uid))
    conn.commit()

    bot.reply_to(msg, "✅ Registered")

print("🔥 Bot running...")
bot.infinity_polling()
