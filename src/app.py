import os
import asyncio
import logging
import threading
from flask import Flask
from dotenv import load_dotenv
from bot.bot import setup_application

# 1. Quiet Logging Configuration
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Disable "noisy" logs from external libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.ERROR) # Only shows Flask errors

logger = logging.getLogger(__name__)

# --- 2. Web Server for Render Health Checks ---
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running", 200

def run_web_server():
    port = int(os.environ.get("PORT", 3000))
    # Flask logs are now disabled via the werkzeug logger above
    web_app.run(host="0.0.0.0", port=port, use_reloader=False)

# --- 3. Main Async Logic ---
async def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        raise ValueError("TELEGRAM_BOT_TOKEN not found in .env")

    application = setup_application(token)

    # Start health server silently in background
    threading.Thread(target=run_web_server, daemon=True).start()

    logger.info("🤖 Bot is starting...")

    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        
        logger.info("🤖 Bot is now polling for updates!")
        
        stop_signal = asyncio.Event()
        await stop_signal.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot process stopped.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")