import os
from dotenv import load_dotenv
from bot.bot import setup_application

from telegram.ext import CommandHandler

async def health_check(update, context):
    """Simple health check for Fly.io monitoring"""
    await update.message.reply_text("🟢 Bot is alive!")

def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in .env")

    app = setup_application(token)
    print("🤖 Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()