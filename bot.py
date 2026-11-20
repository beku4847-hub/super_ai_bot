
import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Men Super AI Botman! 🤖\nSavolingizni yozing."
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        await update.message.reply_text("Gemini API kaliti topilmadi.")
        return

    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"

        response = requests.post(
            url,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "contents": [{
                    "role": "user",
                    "parts": [{"text": user_text}]
                }]
            },
            timeout=60
        )

        if not response.ok:
            print("GEMINI XATOSI:", response.status_code, response.text)
            response.raise_for_status()

        data = response.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"]

        await update.message.reply_text(answer[:4000])

    except Exception as e:
        print("AI XATOLIGI:", repr(e))
        await update.message.reply_text(
            "AI bilan bog‘lanishda xatolik yuz berdi."
        )

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

print("Super AI Bot ishga tushdi!")
app.run_polling()
