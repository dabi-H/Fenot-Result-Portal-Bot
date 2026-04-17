from typing import Optional, List, Dict

# Map user-friendly class names to Excel filenames
# Equivalent to: CLASS_TO_FILE in Node.js
CLASS_TO_FILE: Dict[str, str] = {
    'ህፃናት 1': 'ህፃናት_1',
    'ህፃናት 2': 'ህፃናት_2',
    'ህፃናት 3': 'ህፃናት_3',
    'አዳጊ 1': 'አዳጊ_1',
    'አዳጊ 2': 'አዳጊ_2',
    'ማዕከላውያን': 'ማዕከላውያን',
    'ቀዳማይ': 'ቀዳማይ',
    'ካልዓይ': 'ካልዓይ',
    'ሳልሳይ': 'ሳልሳይ',
    'ራብዓይ': 'ራብዓይ',
    'ወጣቶች': 'ወጣቶች',
}

# Valid classes list for validation (derived from dict keys)
# Equivalent to: VALID_CLASSES = Object.keys(CLASS_TO_FILE)
VALID_CLASSES: List[str] = list(CLASS_TO_FILE.keys())


def get_file_for_class(class_name: Optional[str]) -> Optional[str]:
    """
    Get filename for a class (returns None if invalid).
    Equivalent to: getFileForClass(className) in Node.js
    
    Args:
        class_name: Class name in Amharic (e.g., "ሳልሳይ")
    
    Returns:
        Excel filename without extension, or None if class is invalid
    """
    # Handle None/empty input (same as className?.trim() in Node.js)
    if not class_name:
        return None
    
    clean_name = class_name.strip()
    
    # Return mapped filename or None (exact same behavior as Node.js)
    return CLASS_TO_FILE.get(clean_name)


def is_valid_class(class_name: Optional[str]) -> bool:
    """
    Check if class is valid.
    Equivalent to: isValidClass(className) in Node.js
    
    Args:
        class_name: Class name in Amharic
    
    Returns:
        True if class exists in VALID_CLASSES, False otherwise
    """
    # Handle None/empty input safely
    if not class_name:
        return False
    
    clean_name = class_name.strip()
    
    # Check membership in valid classes list (same as .includes() in Node.js)
    return clean_name in VALID_CLASSES


def get_display_name_for_file(filename: str) -> Optional[str]:
    """
    Bonus helper: Reverse lookup - get display name from filename.
    (Useful for logging or UI display)
    
    Args:
        filename: Excel filename without extension (e.g., "ሳልሳይ")
    
    Returns:
        User-friendly class name, or None if not found
    """
    # Search for filename in mapping values
    for display_name, file_name in CLASS_TO_FILE.items():
        if file_name == filename:
            return display_name
    return None


def list_available_classes() -> List[str]:
    """
    Bonus helper: Get sorted list of available classes.
    (Useful for admin commands or debugging)
    
    Returns:
        List of valid class names in Amharic
    """
    return sorted(VALID_CLASSES)


# Export all functions and constants (for imports in other modules)
__all__ = [
    "CLASS_TO_FILE",
    "VALID_CLASSES",
    "get_file_for_class",
    "is_valid_class",
    "get_display_name_for_file",  # Bonus helper
    "list_available_classes",     # Bonus helper
]