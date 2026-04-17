from typing import Optional, Dict, List


def format_result_message(result: Optional[Dict]) -> str:
    """
    Format student result for Telegram message.
    Equivalent to: formatResultMessage(result) in Node.js
    
    Args:
        result: Formatted student result dictionary (from student_service)
    
    Returns:
        Formatted message string with Telegram Markdown syntax
    """
    if not result:
        return "❌ ተማሪ አልተገኘም!\nእባክዎ መለያ ቁጥርዎን ይፈትሹ።"
    
    # Build message with Telegram Markdown (*bold* syntax)
    # Note: Telegram Markdown v1 uses * for bold, _ for italic
    msg = "📄 *የተማሪ ውጤት*\n\n"
    msg += f"👤 *ስም:* {result['name']}\n"
    msg += f"🆔 *መለያ:* {result['id']}\n"
    msg += f"🏫 *ክፍል:* {result['class']}\n\n"
    msg += "📚 *ውጤቶች:*\n"
    
    # Handle subjects dictionary (same logic as Object.entries in Node.js)
    subjects = result.get("subjects", {})
    entries = list(subjects.items())
    
    if not entries:
        msg += "  ምንም ውጤት አልተገኘም\n"
    else:
        for subject, score in entries:
            # Format score: remove trailing zeros if whole number
            score_display = f"{int(score)}" if score == int(score) else f"{score}"
            msg += f"  {subject}: {score_display}%\n"
    
    # Add average if available (same conditional logic as Node.js)
    if result.get("average") is not None:
        avg = result["average"]
        avg_display = f"{int(avg)}" if avg == int(avg) else f"{avg}"
        msg += f"\n📊 *አማካኝ:* {avg_display}%"
    
    # Footer message
    msg += "\n\n💡 ሌላ መረጃ ለማግኘት /start ይጫኑ"
    
    return msg


def format_class_selection_message() -> str:
    """
    Format class selection instruction message.
    Equivalent to: formatClassSelectionMessage() in Node.js
    
    Returns:
        Instruction message string with Telegram Markdown syntax
    """
    return (
        "🏫 *ክፍልዎን ይምረጡ:*\n\n"
        "ከታች ያሉትን ቁልፎች በመጫን ክፍልዎን ይምረጡ:\n"
    )


def format_id_input_message() -> str:
    """
    Format ID input instruction message.
    Equivalent to: formatIdInputMessage() in Node.js
    
    Returns:
        Instruction message string with Telegram Markdown syntax
    """
    return (
        "🆔 *የተማሪ መለያ ቁጥርዎን ያስገቡ:*\n\n"
        "ምሳሌ: `ፍብመ/1101/18`\n"
        "⚠️ ቁጥሩን በትክክል ያስገቡ!"
    )


def format_error_message(error_type: str, details: Optional[str] = None) -> str:
    """
    Bonus helper: Format consistent error messages.
    (Useful for centralized error handling)
    
    Args:
        error_type: Type of error ('not_found', 'invalid_id', 'system_error', etc.)
        details: Optional additional context
    
    Returns:
        Formatted error message string
    """
    errors = {
        "not_found": "❌ ተማሪ አልተገኘም!",
        "invalid_id": "❌ የተሳሳተ መለያ ቁጥር!",
        "invalid_class": "❌ የተሳሳተ ክፍል!",
        "system_error": "❌ ስርዓታዊ ስህተት ተፈጥሯል!",
        "pdf_failed": "❌ PDF ማውጣት አልተሳካም!",
    }
    
    base_msg = errors.get(error_type, "❌ ስህተት ተፈጥሯል!")
    
    if details:
        return f"{base_msg}\n\n🔍 {details}\n\n💡 /start ይጫኑ ለመጀመር"
    
    return f"{base_msg}\n\n💡 /start ይጫኑ ለመጀመር"


def format_success_message(action: str, details: Optional[str] = None) -> str:
    """
    Bonus helper: Format consistent success messages.
    
    Args:
        action: Action performed ('result_found', 'pdf_sent', etc.)
        details: Optional additional context
    
    Returns:
        Formatted success message string
    """
    messages = {
        "result_found": "✅ ውጤት ተገኝቷል!",
        "pdf_sent": "📄 PDF ተልኳል!",
        "class_selected": "🏫 ክፍል ተመርጧል!",
    }
    
    base_msg = messages.get(action, "✅ ተሳክቷል!")
    
    if details:
        return f"{base_msg}\n\n📋 {details}"
    
    return base_msg


# Export all functions (for imports in handlers.py)
__all__ = [
    "format_result_message",
    "format_class_selection_message",
    "format_id_input_message",
    "format_error_message",      # Bonus helper
    "format_success_message",    # Bonus helper
]