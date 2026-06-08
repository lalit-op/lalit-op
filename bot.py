import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def script_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("latest_script.txt", "r", encoding="utf-8") as f:
            script = f.read()

        for i in range(0, len(script), 4000):
            await update.message.reply_text(script[i:i + 4000])

    except FileNotFoundError:
        await update.message.reply_text(
            "स्क्रिप्ट उपलब्ध नहीं है। कृपया 4:15 PM के बाद प्रयास करें।"
        )


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("script", script_command))

print("Bot Started...")
app.run_polling()
