import logging
from typing import Optional, Dict, List, Any
from services.excel_service import load_class_data_cached
from utils.class_mapper import is_valid_class

logger = logging.getLogger(__name__)


def find_student_in_class(class_name: str, student_id: Any) -> Optional[Dict]:
    """
    Find a student by ID within a specific class.
    Equivalent to: findStudentInClass(className, studentId) in Node.js
    
    Args:
        class_name: Class name in Amharic (e.g., "ሳልሳይ")
        student_id: Student ID to search (string or number)
    
    Returns:
        Student dictionary if found, None otherwise
    """
    # Validate class first (exact same check as Node.js)
    if not is_valid_class(class_name):
        logger.error(f"❌ Invalid class: {class_name}")
        return None
    
    # Load cached student data (same caching behavior as Node.js)
    students = load_class_data_cached(class_name)
    
    # Clean the search ID: convert to string and trim whitespace
    clean_id = str(student_id).strip() if student_id is not None else ""
    
    # Search for student (exact same logic as Node.js .find())
    for student in students:
        if not student or "id" not in student:
            continue
        
        # Compare IDs: convert to string, trim, case-insensitive match
        student_id_val = str(student["id"]).strip()
        if student_id_val == clean_id:
            return student
    
    # Return None if not found (same as Node.js `return student || null`)
    return None


def format_student_result(student: Dict, class_name: str) -> Optional[Dict]:
    """
    Format student data for response.
    Equivalent to: formatStudentResult(student, className) in Node.js
    
    Args:
        student: Raw student dictionary from Excel
        class_name: Class name for context
    
    Returns:
        Formatted result dictionary with id, name, class, subjects, average
    """
    if not student:
        return None
    
    # Metadata keys to exclude from subjects list (exact same list as Node.js)
    metadata_keys = {
        'id', 'ክፍል', 'የአባሉ ሙሉ ሥም', 
        'class', 'name', 'fullName', 'ID', 'Name'
    }
    
    # Extract subjects: any key with numeric value that's not metadata
    subjects: Dict[str, float] = {}
    total_score: float = 0.0
    subject_count: int = 0
    
    for key, value in student.items():
        # Skip metadata keys (case-insensitive check for safety)
        if key.strip().lower() in {k.lower() for k in metadata_keys}:
            continue
        
        # Try to parse as numeric score (same as parseFloat + isNaN check)
        try:
            score = float(value)
            # Only include valid numeric scores
            if score >= 0:  # Optional: filter out negative/invalid scores
                subjects[key.strip()] = score
                total_score += score
                subject_count += 1
        except (ValueError, TypeError):
            # Skip non-numeric values (same as isNaN check in Node.js)
            continue
    
    # Calculate average (same logic as Node.js)
    average = None
    if subject_count > 0:
        average = round(total_score / subject_count, 2)
    
    # Build result object with fallback field names (exact same priority as Node.js)
    return {
        "id": student.get("id") or student.get("ID"),
        "name": (
            student.get("የአባሉ ሙሉ ሥም") 
            or student.get("name") 
            or student.get("fullName")
            or student.get("Name")
            or "Unknown"
        ),
        "class": class_name,
        "subjects": subjects,
        "average": average,
    }


def get_student_summary(student: Dict, class_name: str) -> str:
    """
    Bonus helper: Generate a simple text summary of student results.
    (Useful for debugging or plain-text responses)
    
    Args:
        student: Raw student dictionary
        class_name: Class name for context
    
    Returns:
        Formatted summary string
    """
    result = format_student_result(student, class_name)
    if not result:
        return "❌ ተማሪ አልተገኘም"
    
    lines = [
        f"👤 ስም: {result['name']}",
        f"🆔 መለያ: {result['id']}",
        f"📚 ክፍል: {result['class']}",
        "",
        "📊 ውጤቶች:"
    ]
    
    for subject, score in result["subjects"].items():
        lines.append(f"  • {subject}: {score}")
    
    if result["average"]:
        lines.append(f"\n📈 አማካይ: {result['average']}")
    
    return "\n".join(lines)


# Export all functions (for imports in handlers.py)
__all__ = [
    "find_student_in_class",
    "format_student_result",
    "get_student_summary",  # Bonus helper
]