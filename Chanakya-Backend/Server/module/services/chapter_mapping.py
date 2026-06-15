"""
Chapter Name Mapping Service
============================

Maps NCERT book codes to human-readable chapter names.
Updated with 2026 NCERT syllabus chapter names.
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Comprehensive mapping from book codes to chapter names (2026 syllabus)
CHAPTER_MAPPINGS: Dict[str, str] = {
    # ============= CLASS 6 SCIENCE (fesc101 - fesc116) =============
    "fesc101": "Chapter 1: The Ever-Evolving World of Science",
    "fesc102": "Chapter 2: Exploring Substances – Acidic and Basic",
    "fesc103": "Chapter 3: Mindful Eating: A Path to a Healthy Body",
    "fesc104": "Chapter 4: Exploring Materials",
    "fesc105": "Chapter 5: Measurement",
    "fesc106": "Chapter 6: Light, Shadows and Reflections",
    "fesc107": "Chapter 7: Electricity and Circuits",
    "fesc108": "Chapter 8: Fun with Magnets",
    "fesc109": "Chapter 9: Moving Things, People and Ideas",
    "fesc110": "Chapter 10: The Living World",
    "fesc111": "Chapter 11: Nature's Treasures",
    "fesc112": "Chapter 12: Beyond Earth",
    "fesc113": "Chapter 13: Water",
    "fesc114": "Chapter 14: Habitat and Adaptation",
    "fesc115": "Chapter 15: Waste Management",
    "fesc116": "Chapter 16: Air Around Us",
    "fesc1ps": "Projects and Activities",
    
    # ============= CLASS 7 SCIENCE (gesc101 - gesc119) =============
    "gesc101": "Chapter 1: Exploring the Investigative World of Science",
    "gesc102": "Chapter 2: The Interdependence of Plants and Animals",
    "gesc103": "Chapter 3: Heat and Temperature",
    "gesc104": "Chapter 4: Acids and Bases",
    "gesc105": "Chapter 5: Physical and Chemical Changes",
    "gesc106": "Chapter 6: Respiration in Organisms",
    "gesc107": "Chapter 7: Transportation in Plants and Animals",
    "gesc108": "Chapter 8: Reproduction in Plants",
    "gesc109": "Chapter 9: Motion and Time",
    "gesc110": "Chapter 10: Electric Current and its Effects",
    "gesc111": "Chapter 11: Light",
    "gesc112": "Chapter 12: Sound",
    "gesc113": "Chapter 13: Weather, Climate and Adaptations",
    "gesc114": "Chapter 14: Forests: Our Lifeline",
    "gesc115": "Chapter 15: Wastewater Story",
    "gesc116": "Chapter 16: Soil",
    "gesc117": "Chapter 17: Water: A Precious Resource",
    "gesc118": "Chapter 18: Winds, Storms and Cyclones",
    "gesc119": "Chapter 19: Structure of the Atom",
    "gesc1ps": "Projects and Activities",
    
    # ============= CLASS 8 SCIENCE (hesc101 - hesc118) =============
    "hesc101": "Chapter 1: Exploring the Investigative World of Science",
    "hesc102": "Chapter 2: The Interdependence of Plants and Animals",
    "hesc103": "Chapter 3: Synthetic Fibres and Plastics",
    "hesc104": "Chapter 4: Metals and Non-metals",
    "hesc105": "Chapter 5: Coal and Petroleum",
    "hesc106": "Chapter 6: Combustion and Flame",
    "hesc107": "Chapter 7: Conservation of Plants and Animals",
    "hesc108": "Chapter 8: Cell - Structure and Functions",
    "hesc109": "Chapter 9: Reproduction in Animals",
    "hesc110": "Chapter 10: Reaching the Age of Adolescence",
    "hesc111": "Chapter 11: Force and Pressure",
    "hesc112": "Chapter 12: Friction",
    "hesc113": "Chapter 13: Sound",
    "hesc114": "Chapter 14: Chemical Effects of Electric Current",
    "hesc115": "Chapter 15: Some Natural Phenomena",
    "hesc116": "Chapter 16: Light",
    "hesc117": "Chapter 17: Stars and the Solar System",
    "hesc118": "Chapter 18: Pollution of Air and Water",
    "hesc1ps": "Projects and Activities",
    
    # ============= CLASS 6 GEOGRAPHY (fess201 - fess208) =============
    "fess201": "Chapter 1: The Earth in the Solar System",
    "fess202": "Chapter 2: Globe: Latitudes and Longitudes",
    "fess203": "Chapter 3: Motions of the Earth",
    "fess204": "Chapter 4: Maps",
    "fess205": "Chapter 5: Major Domains of the Earth",
    "fess206": "Chapter 6: Major Landforms of the Earth",
    "fess207": "Chapter 7: Our Country - India",
    "fess208": "Chapter 8: India: Climate, Vegetation and Wildlife",
    "fess2ps": "Projects and Activities",
    
    # ============= CLASS 6 SOCIAL AND POLITICAL LIFE (fess301 - fess309) =============
    "fess301": "Chapter 1: Understanding Diversity",
    "fess302": "Chapter 2: Diversity and Discrimination",
    "fess303": "Chapter 3: What is Government?",
    "fess304": "Chapter 4: Key Elements of a Democratic Government",
    "fess305": "Chapter 5: Panchayati Raj",
    "fess306": "Chapter 6: Rural Administration",
    "fess307": "Chapter 7: Urban Administration",
    "fess308": "Chapter 8: Rural Livelihoods",
    "fess309": "Chapter 9: Urban Livelihoods",
    "fess3ps": "Projects and Activities",
    
    # ============= CLASS 7 GEOGRAPHY (gess201 - gess210) =============
    "gess201": "Chapter 1: Environment",
    "gess202": "Chapter 2: Inside Our Earth",
    "gess203": "Chapter 3: Our Changing Earth",
    "gess204": "Chapter 4: Air",
    "gess205": "Chapter 5: Water",
    "gess206": "Chapter 6: Natural Vegetation and Wildlife",
    "gess207": "Chapter 7: Human Environment - Settlement, Transport and Communication",
    "gess208": "Chapter 8: Human Environment Interactions - The Tropical and Subtropical Region",
    "gess209": "Chapter 9: Desert Life",
    "gess210": "Chapter 10: Life in the Temperate Grasslands",
    "gess2er": "Extra Reading: Life in the Polar Regions",
    "gess2ps": "Projects and Activities",
    
    # ============= CLASS 7 SOCIAL AND POLITICAL LIFE (gess301 - gess310) =============
    "gess301": "Chapter 1: On Equality",
    "gess302": "Chapter 2: Role of the Government in Health",
    "gess303": "Chapter 3: How the State Government Works",
    "gess304": "Chapter 4: Growing up as Boys and Girls",
    "gess305": "Chapter 5: Women Change the World",
    "gess306": "Chapter 6: Understanding Media",
    "gess307": "Chapter 7: Understanding Advertising",
    "gess308": "Chapter 8: Markets Around Us",
    "gess309": "Chapter 9: A Shirt in the Market",
    "gess310": "Chapter 10: Struggles for Equality",
    "gess3ps": "Projects and Activities",
    
    # ============= CLASS 8 GEOGRAPHY (hess401 - hess406) =============
    "hess401": "Chapter 1: Resources",
    "hess402": "Chapter 2: Land, Soil, Water, Natural Vegetation and Wildlife Resources",
    "hess403": "Chapter 3: Mineral and Power Resources",
    "hess404": "Chapter 4: Agriculture",
    "hess405": "Chapter 5: Industries",
    "hess406": "Chapter 6: Human Resources",
    "hess4ps": "Projects and Activities",
    
    # ============= CLASS 8 SOCIAL AND POLITICAL LIFE (hess301 - hess310) =============
    "hess301": "Chapter 1: The Indian Constitution",
    "hess302": "Chapter 2: Understanding Secularism",
    "hess303": "Chapter 3: Why Do We Need Parliament?",
    "hess304": "Chapter 4: Understanding Laws",
    "hess305": "Chapter 5: Judiciary",
    "hess306": "Chapter 6: Understanding Our Criminal Justice System",
    "hess307": "Chapter 7: Understanding Marginalization",
    "hess308": "Chapter 8: Confronting Marginalization",
    "hess309": "Chapter 9: Public Facilities",
    "hess310": "Chapter 10: Law and Social Justice",
    "hess3ps": "Projects and Activities"
}


def get_chapter_name(book_code: str) -> str:
    """
    Get human-readable chapter name for a book code.
    
    Args:
        book_code: Book code like 'fesc101', 'gesc102', etc.
        
    Returns:
        Human-readable chapter name or formatted fallback
    """
    if book_code in CHAPTER_MAPPINGS:
        return CHAPTER_MAPPINGS[book_code]
    
    # Fallback: try to create a meaningful name from the code
    return _generate_fallback_name(book_code)


def _generate_fallback_name(book_code: str) -> str:
    """
    Generate a fallback chapter name when mapping is not found.
    
    Args:
        book_code: Book code like 'fesc101'
        
    Returns:
        Formatted chapter name with extracted chapter number
    """
    # Extract numeric part for chapter number
    numeric_part = ''.join(filter(str.isdigit, book_code))
    
    if numeric_part:
        # Try to extract meaningful chapter number
        if len(numeric_part) >= 2:
            chapter_num = int(numeric_part[-2:])
        else:
            chapter_num = int(numeric_part)
        
        # Check for special suffixes
        if book_code.endswith('ps'):
            return "Projects and Activities"
        elif book_code.endswith('er'):
            return "Extra Reading"
        else:
            return f"Chapter {chapter_num}"
    
    # Ultimate fallback
    return book_code.upper()


def get_book_code_from_name(chapter_name: str) -> Optional[str]:
    """
    Reverse lookup: Get book code from human-readable chapter name.
    
    Args:
        chapter_name: Human-readable chapter name like 'Chapter 14: Forests: Our Lifeline'
        
    Returns:
        Book code like 'gesc114', or None if not found
    """
    # First try exact match
    for code, name in CHAPTER_MAPPINGS.items():
        if name == chapter_name:
            return code
    
    # Try case-insensitive match
    chapter_name_lower = chapter_name.lower().strip()
    for code, name in CHAPTER_MAPPINGS.items():
        if name.lower().strip() == chapter_name_lower:
            return code
    
    # Try partial match (in case of minor differences)
    for code, name in CHAPTER_MAPPINGS.items():
        if chapter_name_lower in name.lower() or name.lower() in chapter_name_lower:
            return code
    
    logger.warning(f"No book code found for chapter name: {chapter_name}")
    return None


def get_all_mappings() -> Dict[str, str]:
    """Get all chapter mappings."""
    return CHAPTER_MAPPINGS.copy()


def add_mapping(book_code: str, chapter_name: str) -> None:
    """
    Add or update a chapter mapping.
    
    Args:
        book_code: Book code like 'fesc101'
        chapter_name: Human-readable chapter name
    """
    CHAPTER_MAPPINGS[book_code] = chapter_name
    logger.info(f"Added mapping: {book_code} -> {chapter_name}")


def get_chapters_for_subject(class_name: str, subject: str) -> Dict[str, str]:
    """
    Get all chapters for a specific class and subject.
    
    Args:
        class_name: Class name like 'Class_6'
        subject: Subject name like 'Science'
        
    Returns:
        Dictionary of book codes to chapter names for the subject
    """
    # Define subject-to-code-prefix mapping
    subject_prefixes = {
        ('Class_6', 'Science'): 'fesc1',
        ('Class_6', 'Geography - The earth_Our Habitat'): 'fess2',
        ('Class_6', 'Social and Political Life'): 'fess3',
        ('Class_7', 'Geography'): 'gess2',
        ('Class_7', 'Science'): 'gesc1',
        ('Class_7', 'Social and Political Life'): 'gess3',
        ('Class_8', 'Geography - Resourse and Developement (Geography)'): 'hess4',
        ('Class_8', 'Science'): 'hesc1',
        ('Class_8', 'Social and Political Life'): 'hess3',
    }
    
    prefix = subject_prefixes.get((class_name, subject))
    if not prefix:
        return {}
    
    # Filter mappings by prefix
    filtered = {
        code: name for code, name in CHAPTER_MAPPINGS.items()
        if code.startswith(prefix)
    }
    
    return filtered


def format_topic_display_name(book_code: str, chapter_number: Optional[int] = None) -> str:
    """
    Format a display-friendly topic name from book code.
    
    Args:
        book_code: Original book code
        chapter_number: Chapter number if available
        
    Returns:
        Formatted display name
    """
    # Try to get proper chapter name first
    chapter_name = get_chapter_name(book_code)
    
    if chapter_name and chapter_name != book_code.upper():
        return chapter_name
    
    # Fallback: try to format the book code nicely
    if chapter_number:
        return f"Chapter {chapter_number}"
    
    # Last resort: clean up the book code
    import re
    # Extract subject and number from codes like "fess201"
    match = re.match(r'([a-z]+)(\d+)', book_code.lower())
    if match:
        subject_code, number = match.groups()
        
        # Try to map subject codes to names
        subject_mapping = {
            'fess': 'Social Science',
            'gesc': 'Science',  
            'gess': 'Geography',
            'hess': 'History',
            'hesc': 'Science'
        }
        
        subject = subject_mapping.get(subject_code, subject_code.upper())
        
        # Extract chapter number from the end
        chapter_num = number[-2:] if len(number) >= 2 else number
        if chapter_num.lstrip('0').isdigit():
            return f"{subject} - Chapter {int(chapter_num.lstrip('0'))}"
    
    return book_code.upper()  # Fallback to uppercase book code