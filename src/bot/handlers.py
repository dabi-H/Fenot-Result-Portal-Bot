import os
import asyncio
import logging
import concurrent.futures
from datetime import datetime
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from services.student_service import find_student_in_class, format_student_result
from services.pdf_service import generate_result_pdf, delete_pdf
from utils.formatter import format_result_message, format_class_selection_message, format_id_input_message
from utils.class_mapper import is_valid_class
from bot.keyboards import create_class_keyboard, create_back_keyboard, create_main_menu_keyboard
from ethiopian_date import EthiopianDateConverter
from pytz import timezone

logger = logging.getLogger(__name__)

# Session storage for user flow (in-memory, like your Node version)
# For production: consider Redis or database
user_sessions: dict[int, dict] = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - reset session and show class selection"""
    user_id = update.effective_user.id
    
    # Clear session for this user
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    await update.message.reply_text(
        "እንኳን ደህና መጡ!\n"
        "ይህ ቦት የተማሪ ውጤት ለማየት ያገለግላል።\n\n"
        "ለመጀመር ክፍልዎን ይምረጡ:",
        reply_markup=create_class_keyboard(),
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    await update.message.reply_text(
        "እርዳታ:\n\n"
        "1. ክፍልዎን ይምረጡ (ከቁልፎች)\n"
        "2. የተማሪ መለያ ቁጥርዎን ያስገቡ\n"
        "3. ውጤትዎን ይመልከቱ!\n\n"
        "ችግር ካጋጠመዎት አስተዳዳሪዎን ያግኙ።",
        parse_mode="Markdown"
    )


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple health check for Fly.io monitoring"""
    await update.message.reply_text("🟢 Bot is alive!")


async def handle_class_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callback for class selection"""
    query = update.callback_query
    await query.answer()  # Always answer callback queries
    
    data = query.data
    if not data or not data.startswith("class:"):
        await query.answer("ስህተት", show_alert=True)
        return
    
    class_name = data.replace("class:", "")
    user_id = query.from_user.id
    
    # Save session state
    user_sessions[user_id] = {
        "class": class_name,
        "step": "waiting_for_id",
    }
    
    await query.answer(f"{class_name} ተመርጧል")
    
    await query.edit_message_text(
        format_id_input_message(),
        reply_markup=create_back_keyboard(),
        parse_mode="Markdown"
    )


async def send_pdf_result(update: Update, context: ContextTypes.DEFAULT_TYPE, student: dict) -> None:
    """Generate and send PDF result to user"""
    try:
        # Send "generating" message
        generating_msg = await update.message.reply_text(
            "🔄 PDF እየተዘጋጀ ነው... እባክዎ ይጠብቁ።"
        )
        
        # Generate PDF in thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pdf_path = await loop.run_in_executor(pool, generate_result_pdf, student)
        
        # Delete "generating" message
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=generating_msg.message_id
            )
        except Exception as e:
            logger.warning(f"Could not delete generating message: {e}")
        
        # Send PDF document
        student_id_safe = student["id"].replace("/", "_")
        filename = f"Result_{student_id_safe}.pdf"
        
        # Get Ethiopian date and time
        eth_tz = timezone('Africa/Addis_Ababa')
        now = datetime.now(eth_tz)
        edc = EthiopianDateConverter()
        et_year, et_month, et_day = edc.to_ethiopian(now.year, now.month, now.day)
        date_str = f"{et_day}/{et_month}/{et_year}"
        time_str = now.strftime('%I:%M %p')
        
        caption = (
            f"የተማሪ ውጤት ለ {student['name']}\n\n"
            f"የተዘጋጀበት ቀን: {date_str} {time_str}"
        )
        
        # Send with increased timeouts
        with open(pdf_path, "rb") as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=filename,
                caption=caption,
                parse_mode="Markdown",
                read_timeout=60,      # 60 seconds to read response
                write_timeout=60,     # 60 seconds to upload
                connect_timeout=30,   # 30 seconds to connect
                pool_timeout=30       # 30 seconds for connection pool
            )
        
        # Cleanup: delete PDF after 10 seconds (non-blocking)
        asyncio.create_task(_delayed_delete(pdf_path))
        
    except TimeoutError as e:
        logger.error(f"PDF generation/sending timeout: {e}", exc_info=True)
        await update.message.reply_text(
            "⏰ ጊዜው አልፏል። ፋይሉ ለመላክ በጣም ቀርፋፋ ነው።\n"
            "እባክዎ እንደገና ይሞክሩ ወይም ትንሽ ቆይተው ይሞክሩ።"
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ PDF ማውጣት አልተሳካም። እባክዎ እንደገና ይሞክሩ።"
        )


async def _delayed_delete(file_path: str, delay: int = 10) -> None:
    """Helper: delete file after delay (non-blocking)"""
    await asyncio.sleep(delay)
    try:
        delete_pdf(file_path)
    except Exception as e:
        logger.warning(f"Failed to delete PDF {file_path}: {e}")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all text messages - main conversation flow"""
    if not update.message or not update.message.text:
        return
        
    text = update.message.text.strip()
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    # ─────────────────────────────────────
    # Handle "Back" button
    # ─────────────────────────────────────
    if text == "ወደ ኋላ":
        if user_id in user_sessions:
            del user_sessions[user_id]
        await update.message.reply_text(
            format_class_selection_message(),
            reply_markup=create_class_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # ─────────────────────────────────────
    # Handle main menu buttons
    # ─────────────────────────────────────
    if text == "ውጤት ይመልከቱ":
        return await start_command(update, context)
    if text == "እርዳታ":
        return await help_command(update, context)
    if text == "ይጀምሩ":
        return await start_command(update, context)
    
    # ─────────────────────────────────────
    # Handle PDF request button
    # ─────────────────────────────────────
    if text in ("📄 PDF ውጤት", "PDF"):
        session = user_sessions.get(user_id)
        if not session or "last_result" not in session:
            await update.message.reply_text(
                "የቅርብ ጊዜ ውጤት አልተገኘም። በመጀመሪያ ውጤትዎን ይመልከቱ /start",
                reply_markup=create_main_menu_keyboard()
            )
            return
        return await send_pdf_result(update, context, session["last_result"])
    
    # ─────────────────────────────────────
    # No active session: check if user sent class name directly
    # ─────────────────────────────────────
    if not session:
        if is_valid_class(text):
            user_sessions[user_id] = {
                "class": text,
                "step": "waiting_for_id",
            }
            await update.message.reply_text(
                format_id_input_message(),
                reply_markup=create_back_keyboard(),
                parse_mode="Markdown"
            )
            return
        else:
            await update.message.reply_text(
                format_class_selection_message(),
                reply_markup=create_class_keyboard(),
                parse_mode="Markdown"
            )
            return
    
    # ─────────────────────────────────────
    # Handle ID input (session step: waiting_for_id)
    # ─────────────────────────────────────
    if session.get("step") == "waiting_for_id":
        class_name = session["class"]
        student_id = text
        
        # Search for student
        raw_student = find_student_in_class(class_name, student_id)
        
        if not raw_student:
            await update.message.reply_text(
                "ተማሪ አልተገኘም!\n\n"
                "• መለያ ቁጥርዎን ይፈትሹ\n"
                "• ክፍልዎን ይፈትሹ\n\n"
                "እንደገና ለመሞከር /start ይጫኑ",
                reply_markup=create_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            return
        
        # Format and save result
        result = format_student_result(raw_student, class_name)
        message = format_result_message(result)
        
        # Save for later PDF generation
        user_sessions[user_id]["last_result"] = result
        
        # Send result with PDF button keyboard
        pdf_keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("📄 PDF ውጤት")],
            [KeyboardButton("ውጤት ይመልከቱ"), KeyboardButton("ይጀምሩ")],
        ], resize_keyboard=True, one_time_keyboard=False)
        
        await update.message.reply_text(
            message,
            reply_markup=pdf_keyboard,
            parse_mode="Markdown"
        )
        return
    
    # ─────────────────────────────────────
    # Fallback: unrecognized message
    # ─────────────────────────────────────
    await update.message.reply_text(
        "ያልተረዳሁት መልእክት። /help ይጫኑ ለእርዳታ።"
    )


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries (inline buttons)"""
    query = update.callback_query
    if not query or not query.data:
        await query.answer("ያልተረዳሁት ጥያቄ")
        return
    
    # Route class selection callbacks
    if query.data.startswith("class:"):
        return await handle_class_selection(update, context)
    
    # Handle back button
    if query.data == "back":
        user_id = query.from_user.id
        # Clear session
        if user_id in user_sessions:
            del user_sessions[user_id]
        await query.edit_message_text(
            "እንኳን ደህና መጡ!\n"
            "ይህ ቦት የተማሪ ውጤት ለማየት ያገለግላል።\n\n"
            "ለመጀመር ክፍልዎን ይምረጡ:",
            reply_markup=create_class_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Default: unknown callback
    await query.answer("ያልተረዳሁት ጥያቄ")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler (equivalent to bot.catch())"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=True)
    
    # Try to notify user if possible
    if context.error and hasattr(context, "update") and context.update:
        try:
            if hasattr(context.update, "effective_message") and context.update.effective_message:
                await context.update.effective_message.reply_text(
                    "申し訳ありませんが、エラーが発生しました。しばらくしてからもう一度お試しください。"
                )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")


# Export all functions (for imports in bot.py)
__all__ = [
    "start_command",
    "help_command", 
    "handle_text_message",
    "handle_callback_query",
    "error_handler",
    "user_sessions",
    "send_pdf_result",
]