import logging
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from utils.class_mapper import get_file_for_class

logger = logging.getLogger(__name__)

# Base path for Excel files (equivalent to path.join(__dirname, '../data'))
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Cache for loaded data (same as Node.js dataCache)
_data_cache: Dict[str, List[Dict]] = {}


def load_class_data(class_name: str) -> List[Dict]:
    """
    Load student data from the correct Excel file based on class.
    Equivalent to: loadClassData(className) in Node.js
    
    Args:
        class_name: Class name in Amharic (e.g., "ሳልሳይ")
    
    Returns:
        List of student dictionaries with cleaned keys
    """
    file_name = get_file_for_class(class_name)
    
    if not file_name:
        logger.error(f"❌ Invalid class: {class_name}")
        return []
    
    file_path = DATA_DIR / f"{file_name}.xlsx"
    
    if not file_path.exists():
        logger.error(f"❌ File not found: {file_path}")
        return []
    
    try:
        # Read Excel file with openpyxl engine (handles Amharic sheet names)
        df = pd.read_excel(file_path, engine="openpyxl")
        
        # Convert DataFrame to list of dicts (same as sheet_to_json)
        raw_data = df.to_dict(orient="records")
        
        # Clean keys: trim whitespace from all column names (exact Node.js behavior)
        cleaned_data = []
        for row in raw_data:
            cleaned_row = {key.strip(): value for key, value in row.items()}
            cleaned_data.append(cleaned_row)
        
        return cleaned_data
        
    except Exception as e:
        logger.error(f"❌ Error loading {file_name}.xlsx: {e}", exc_info=True)
        return []


def load_class_data_cached(class_name: str) -> List[Dict]:
    """
    Load student data with caching for better performance.
    Equivalent to: loadClassDataCached(className) in Node.js
    
    Args:
        class_name: Class name in Amharic
    
    Returns:
        List of student dictionaries (cached if previously loaded)
    """
    file_name = get_file_for_class(class_name)
    if not file_name:
        return []
    
    # Return cached data if available (exact same cache logic as Node.js)
    if file_name in _data_cache:
        return _data_cache[file_name]
    
    # Load fresh data and cache it
    data = load_class_data(class_name)
    
    if data:  # Only cache if data was successfully loaded
        _data_cache[file_name] = data
    
    return data


def clear_cache() -> None:
    """
    Clear the data cache (use when Excel files are updated).
    Equivalent to: clearCache() in Node.js
    """
    global _data_cache
    _data_cache.clear()
    logger.info("🗑️ Excel data cache cleared")


def refresh_cache(class_name: Optional[str] = None) -> None:
    """
    Optional helper: Refresh cache for specific class or all classes.
    (Bonus function not in original, but useful for production)
    
    Args:
        class_name: Specific class to refresh, or None to refresh all
    """
    if class_name:
        file_name = get_file_for_class(class_name)
        if file_name and file_name in _data_cache:
            del _data_cache[file_name]
            # Reload immediately
            load_class_data_cached(class_name)
            logger.info(f"🔄 Cache refreshed for: {class_name}")
    else:
        clear_cache()
        logger.info("🔄 All cache refreshed")


# Export all functions (for imports in student_service.py)
__all__ = [
    "load_class_data",
    "load_class_data_cached", 
    "clear_cache",
    "refresh_cache",  # Bonus helper
]