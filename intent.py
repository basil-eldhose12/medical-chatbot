import difflib
import string
import re
from database import get_db_connection
import data


def generate_ngrams(words, n):
    """Generate all n-word phrases from a list of words."""
    return [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]


def detect_symptoms(text):
    """
    Detect medical symptoms from natural-language input with synonym mapping.
    """
    try:
        # Step 1: Pre-process and Normalize
        text = text.lower()
        
        # User requested mappings & existing synonyms
        normalization = {
            "shivering": "fever",
            "chills": "fever",
            "head pain": "headache",
            "body pain": "body ache",
            "vomit": "vomiting",
            "cold": "common cold",
            "shiver": "fever"
        }
        
        # Apply normalization first
        for phrase, replacement in normalization.items():
            text = re.sub(r'\b' + re.escape(phrase) + r'\b', replacement, text)

        # Apply the master map from data.py
        norm_map = sorted(data.NORMALIZATION_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        for phrase, replacement in norm_map:
            text = re.sub(r'\b' + re.escape(phrase) + r'\b', replacement, text)

        # Step 2: Extract base symptoms from the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT symptom FROM case_symptoms")
        db_symptoms = [row['symptom'].lower() for row in cursor.fetchall()]
        conn.close()

        # Combine with Medical Dictionary
        full_pool = list(set(db_symptoms + [s.lower() for s in data.MEDICAL_DICTIONARY]))
        
        detected = set()
        
        # Step 3: Keyword Search (Whole Word)
        for term in full_pool:
            if len(term) > 3:
                if re.search(r'\b' + re.escape(term) + r'\b', text):
                    detected.add(term)
            elif term in text.split(): # For short words like "flu" or "rash"
                detected.add(term)

        # Step 4: Deduplication (Keep longer phrases if they contain shorter ones)
        final_symptoms = set()
        sorted_detected = sorted(list(detected), key=len, reverse=True)
        for s in sorted_detected:
            if not any(s != other and s in other for other in final_symptoms):
                final_symptoms.add(s)

        return final_symptoms

    except Exception as e:
        print(f"[detect_symptoms] Error: {e}")
        return set()

    except Exception as e:
        print(f"[detect_symptoms] Error: {e}")
        return set()

def detect_appointment_intent(text):
    """Detect if the user wants to book an appointment."""
    keywords = ["appointment", "book", "meeting", "see a doctor", "visit hospital", "schedule", "suggest doctor"]
    text = text.lower()
    for kw in keywords:
        if kw in text:
            return True
    return False

def is_date(text):
    """Simple check for YYYY-MM-DD format."""
    return re.match(r"\d{4}-\d{2}-\d{2}", text.strip()) is not None

def is_time(text):
    """Simple check for HH:MM format."""
    return re.match(r"\d{1,2}:\d{2}", text.strip()) is not None

def is_affirmative(text):
    """Detect 'yes' type responses."""
    keywords = ["yes", "yeah", "yep", "sure", "definitely", "i do", "proceed", "okay", "ok", "yes please"]
    text = text.lower().strip()
    return any(kw == text or text.startswith(kw + " ") for kw in keywords)

def is_negative(text):
    """Detect 'no' type responses."""
    keywords = ["no", "nah", "nope", "never mind", "cancel", "actually no"]
    text = text.lower().strip()
    return any(kw == text or text.startswith(kw + " ") for kw in keywords)

def get_number(text):
    """Extract first number from text."""
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None

def normalize_specialization(text):
    """Normalize specialization strings for better matching."""
    if not text: return ""
    text = text.lower().strip()
    # Handle common abbreviations
    abbrevs = {"gp": "general physician", "er": "emergency"}
    if text in abbrevs:
        text = abbrevs[text]
    
    # Remove common suffixes/words for broader matching
    removals = ["ist", "ology", "ologist", "specialist", "medical", "doctor"]
    for r in removals:
        if text.endswith(r):
            text = text[:-len(r)]
    return text.strip()
