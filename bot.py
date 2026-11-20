cd ~/super_ai_bot
cat > bot.py <<'PY'
import os
import sqlite3
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

DB = "super_ai_memory.db"
MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = """
Sen Super AI Assistant nomli aqlli yordamchisan.
Foydalanuvchiga o'zbek tilida aniq va tushunarli javob ber.
Dasturlash, matematika, fanlar, darslar, tarjima,
ijod va kundalik savollarda yordam ber.
O'zingni Gemini emas, Super AI Assistant deb tanishtir.
Agar bilmasang, bilmasligingni ochiq ayt.
O'quvchilarga mavzularni sodda misollar bilan tushuntir.
"""

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT
            )
        """)

def get_history(user_id):
    with sqlite3.connect(DB) as con:
        rows = con.execute(
            "SELECT role, content FROM memory "
            "WHERE user_id=? ORDER BY id DESC LIMIT 12",
            (user_id,)
        ).fetchall()
    return list(reversed(rows))

def save_message(user_id, role, content):
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO memory (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Men Super AI Assistantman! 🤖\n"
        "Savolingizni yozing.\n\n"
        "/memory — xotirani ko'rish\n"
        "/forget — xotirani tozalash"
    )

async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = get_history(user_id)

    if not history:
        await update.message.reply_text("Hozircha xotiram bo'sh.")
        return

    result = "🧠 Oxirgi suhbatlar xotirasi:\n\n"
    for role, content in history[-6:]:
        name = "Siz" if role == "user" else "Super AI"
        result += f"{name}: {content[:250]}\n\n"

    await update.message.reply_text(result[:4000])

async def forget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with sqlite3.connect(DB) as con:
        con.execute("DELETE FROM memory WHERE user_id=?", (user_id,))
    await update.message.reply_text("Xotirangiz tozalandi. 🧹")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        await update.message.reply_text("Gemini API kaliti topilmadi.")
        return

    try:
        contents = []
        for role, content in get_history(user_id):
            contents.append({
                "role": role,
                "parts": [{"text": content}]
            })

        contents.append({
            "role": "user",
            "parts": [{"text": user_text}]
        })

        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{MODEL}:generateContent"
        )

        response = requests.post(
            url,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "system_instruction": {
                    "parts": [{"text": SYSTEM_PROMPT}]
                },
                "contents": contents
            },
            timeout=60
        )

        print("GEMINI STATUS:", response.status_code)

        if not response.ok:
            print("GEMINI BODY:", response.text[:1000])
            response.raise_for_status()

        data = response.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"]

        save_message(user_id, "user", user_text)
        save_message(user_id, "model", answer)

        for i in range(0, len(answer), 4000):
            await update.message.reply_text(answer[i:i+4000])

    except Exception as e:
        print("AI XATOLIGI:", repr(e))
        await update.message.reply_text(
            "AI bilan bog'lanishda xatolik yuz berdi."
        )

init_db()

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("memory", memory_command))
app.add_handler(CommandHandler("forget", forget_command))
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
)

print("Super AI Assistant ishga tushdi!")
app.run_polling()
PY
