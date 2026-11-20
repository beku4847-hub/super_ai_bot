
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Men Super AI Botman! 🤖\nSavolingizni yozing."
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        url = "https://generativelanguage.googleapis.com/v1beta/interactions"

        response = requests.post(
            url,
            headers={
                "x-goog-api-key": os.getenv("GEMINI_API_KEY"),
                "Content-Type": "application/json"
            },
            json={
                "model": "gemini-3.5-flash-lite",
                "input": user_text
            },
            timeout=60
        )

        response.raise_for_status()
        data = response.json()

        answer = data.get("output_text", "")

        if not answer:
            for step in data.get("steps", []):
                for item in step.get("content", []):
                    if item.get("type") == "text":
                        answer += item.get("text", "")

        if not answer:
            answer = "AI javob qaytarmadi."

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
