import os
import signal
import logging
import threading
from flask import Flask

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot.handlers import (
    start_command,
    help_command,
    handle_text_message,
    handle_callback_query,
    error_handler,
    health_check,
)

logger = logging.getLogger(__name__ )

# ----------------------------------------
# 🌐 1. Web Server for Kubernetes (NEW)
# ----------------------------------------
web_app = Flask(__name__ )

@web_app.route("/")
def home():
    return "Bot is running", 200

@web_app.route("/health")
def health():
    return "OK", 200

def run_web_server():
    logger.info("🌐 Starting health server on port 3000...")
    web_app.run(host="0.0.0.0", port=3000)


# ----------------------------------------
# 🤖 2. Telegram Bot Setup (UNCHANGED)
# ----------------------------------------
def setup_application(token: str) -> Application:
    """
    Create and configure the PTB Application instance.
    """
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )
    
    app.add_error_handler(error_handler)
    
    app.add_handler(CommandHandler("health", health_check))
    
    return app


# ----------------------------------------
# 🚀 3. Start Bot (UPDATED)
# ----------------------------------------
def start_bot() -> Application:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("🔑 TELEGRAM_BOT_TOKEN not found in environment variables")
    
    application = setup_application(token)

    # ✅ Start web server in background (IMPORTANT FIX)
    threading.Thread(target=run_web_server, daemon=True).start()

    # Graceful shutdown handler
    def graceful_stop(signum=None, frame=None):
        logger.info("🛑 Stopping bot...")
        application.stop()
        application.shutdown()

    signal.signal(signal.SIGINT, graceful_stop)
    signal.signal(signal.SIGTERM, graceful_stop)

    logger.info("🤖 Bot launched successfully!")

    application.run_polling(drop_pending_updates=True)

    return application