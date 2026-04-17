import os
import signal
import logging
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
)

logger = logging.getLogger(__name__)

def setup_application(token: str) -> Application:
    """
    Create and configure the PTB Application instance.
    Equivalent to: new Telegraf(process.env.BOT_TOKEN)
    """
    # Build the application with your bot token
    app = Application.builder().token(token).build()
    
    # Register command handlers: /start and /help
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Register callback query handler (for inline buttons)
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Register text message handler (exclude commands to avoid double-trigger)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )
    
    # Register global error handler (equivalent to bot.catch())
    app.add_error_handler(error_handler)
    
    return app


def start_bot() -> Application:
    """
    Main entry point to launch the bot.
    Equivalent to: startBot() in Node.js
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("🔑 TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Setup the application
    application = setup_application(token)
    
    # Graceful shutdown handler (SIGINT / SIGTERM)
    def graceful_stop(signum=None, frame=None):
        logger.info("🛑 Stopping bot...")
        application.stop()
        application.shutdown()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_stop)
    signal.signal(signal.SIGTERM, graceful_stop)
    
    # Launch the bot (blocking call, handles async loop internally)
    logger.info("🤖 Bot launched successfully!")
    
    # run_polling() is blocking and manages the event loop
    # drop_pending_updates=True clears old updates on restart
    application.run_polling(drop_pending_updates=True)
    
    return application