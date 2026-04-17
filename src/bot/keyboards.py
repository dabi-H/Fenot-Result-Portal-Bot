from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from utils.class_mapper import VALID_CLASSES


def create_class_keyboard() -> InlineKeyboardMarkup:
    """
    Create inline keyboard for class selection.
    Groups classes into rows of 2 for better UX.
    Equivalent to: createClassKeyboard() in Node.js
    """
    keyboard = []
    
    # Group classes into rows of 2 (same logic as Node.js)
    for i in range(0, len(VALID_CLASSES), 2):
        row_classes = VALID_CLASSES[i:i + 2]
        row = [
            InlineKeyboardButton(
                text=cls,
                callback_data=f"class:{cls}"
            )
            for cls in row_classes
        ]
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


def create_class_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Create simple reply keyboard alternative (not inline).
    Equivalent to: createClassReplyKeyboard() in Node.js
    """
    keyboard = [
        [KeyboardButton(text=cls)]
        for cls in VALID_CLASSES
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True
    )


def create_back_keyboard() -> InlineKeyboardMarkup:
    """
    Create back button keyboard.
    Equivalent to: createBackKeyboard() in Node.js
    """
    keyboard = [
        [InlineKeyboardButton(text="🔙 ወደ ኋላ", callback_data="back")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Create main menu keyboard with multiple action buttons.
    Equivalent to: createMainMenuKeyboard() in Node.js
    """
    keyboard = [
        [KeyboardButton(text="📊 ውጤት ይመልከቱ")],
        [
            KeyboardButton(text="❓ እርዳታ"),
            KeyboardButton(text="🔄 ይጀምሩ")
        ],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False  # Keep menu available for repeated use
    )


# Export all functions (for imports in handlers.py)
__all__ = [
    "create_class_keyboard",
    "create_class_reply_keyboard",
    "create_back_keyboard",
    "create_main_menu_keyboard",
]