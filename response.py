import data
from database import get_db_connection

DISCLAIMER = data.DISCLAIMER
RED_FLAGS = data.RED_FLAGS
INVESTIGATION_VARIABLES = data.INVESTIGATION_VARIABLES

def get_domain_keywords():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT domain, symptom FROM case_symptoms JOIN cases ON case_symptoms.case_id = cases.id")
    rows = cursor.fetchall()
    conn.close()
    
    domain_map = {}
    for row in rows:
        domain = row['domain']
        symptom = row['symptom']
        if domain not in domain_map:
            domain_map[domain] = set()
        domain_map[domain].add(symptom)
    return domain_map

# CORE CLINICAL SYMPTOMS
CORE_CLINICAL_SYMPTOMS = set(data.MEDICAL_DICTIONARY)

def calculate_severity(symptoms):
    """
    Categorizes severity based on clinical rules:
    LOW: mild headache, fatigue, runny nose, mild cough
    MODERATE: fever, vomiting, abdominal pain, persistent cough
    CRITICAL: breathing difficulty + chest pain, seizures, loss of consciousness, stroke symptoms
    """
    # CRITICAL
    if (("breathing difficulty" in symptoms or "shortness of breath" in symptoms) and "chest pain" in symptoms) or \
       "seizure" in symptoms or "unconscious" in symptoms or "paralysis" in symptoms:
        return "CRITICAL"
    
    # MODERATE
    if "vomiting" in symptoms or "abdominal pain" in symptoms or "fever" in symptoms or "cough" in symptoms:
        return "MODERATE"
    
    # LOW
    return "LOW"

def calculate_risk_score(symptoms):
    """
    Calculates a numeric risk score (0-10) based on detected symptoms.
    Uses data.SYMPTOM_WEIGHTS. Capped at 10.
    """
    if not symptoms:
        return 0, "LOW"
    
    score = 0
    for s in symptoms:
        weight = data.SYMPTOM_WEIGHTS.get(s, 1) # Default weight 1 if not in dict
        score += weight
    
    score = min(score, 10) # Cap at 10
    
    if score >= 7:
        classification = "HIGH"
    elif score >= 4:
        classification = "MODERATE"
    else:
        classification = "LOW"
        
    return score, classification

def detect_locked_domain(symptoms):
    """
    Maps symptoms to the most relevant medical domain for database filtering.
    Follows v3.0 spec: Respiratory, Digestive, Neuro, General.
    """
    # Domain mapping (per v3.0 spec)
    mappings = {
        "RESPIRATORY": {"cough", "breathing difficulty", "shortness of breath", "wheezing", "chest pain", "chest tightness", "fever"},
        "DIGESTIVE": {"abdominal pain", "nausea", "vomiting", "diarrhea", "bloating", "heartburn"},
        "NEURO": {"headache", "dizziness", "blurred vision", "confusion", "stiff neck", "sensitivity to light"},
        "ENT": {"ear pain", "sore throat", "difficulty swallowing", "swollen lymph nodes"},
        "ALLERGY": {"sneezing", "runny nose", "itching", "rash"},
        "GENITOURINARY": {"frequent urination", "burning sensation"},
        "MENTAL_HEALTH": {"anxiety", "stress", "panic", "insomnia", "sadness", "low mood"},
        "GENERAL": {"fever", "fatigue", "weakness", "body pain", "chills"}
    }
    
    # Check Respiratory first as it often mimics emergencies
    if symptoms & mappings["RESPIRATORY"]:
        return "RESPIRATORY"
    
    for domain, keywords in mappings.items():
        if symptoms & keywords:
            return domain
            
    return "GENERAL"

def fetch_cases_by_domain(domain):
    """
    Fetch cases from data.py instead of DB to use real medical data.
    """
    all_cases = data.ALL_CASES
    if domain == "ALL":
        return all_cases
    
    # Filter by domain
    # Simple mapping for filtering
    domain_map = {
        "EMERGENCY": data.EMERGENCY_CASES,
        "DIGESTIVE": data.DIGESTIVE_CASES,
        "RESPIRATORY": data.RESPIRATORY_CASES,
        "NEURO": data.NEURO_CASES,
        "ENT": data.ENT_CASES,
        "ALLERGY": data.ALLERGY_CASES,
        "GENITOURINARY": data.GENITOURINARY_CASES,
        "MENTAL_HEALTH": data.MENTAL_HEALTH_CASES,
        "GENERAL": data.GENERAL_CASES
    }
    
    return domain_map.get(domain, data.GENERAL_CASES)

def find_best_match(symptoms, cases):
    """
    Find the best matching conditions using the confidence formula:
    confidence = (matched symptoms / total symptoms of disease) * 100
    Applies emergency guardrails and filters matches < 40%.
    """
    if not symptoms:
        return None, 0, []

    matches = []
    
    for case in cases:
        condition_name = case["associations"][0] if case["associations"] else "Unknown"
        
        # Emergency Guardrails
        if condition_name in data.EMERGENCY_RULES:
            rules = data.EMERGENCY_RULES[condition_name]
            required = set(rules.get("required", []))
            optional_one_of = set(rules.get("optional_one_of", []))
            
            # Check required
            if not required.issubset(symptoms):
                continue
            
            # Check optional if exists
            if optional_one_of and not (symptoms & optional_one_of):
                continue

        matched_syms = symptoms & case["symptoms"]
        if not matched_syms:
            continue
            
        # Confidence calculation
        total_case_symptoms = len(case["symptoms"])
        confidence = len(matched_syms) / max(total_case_symptoms, 1)
        
        if confidence >= 0.15:
            matches.append({
                "case": case,
                "confidence": round(confidence, 2),
                "matched_count": len(matched_syms)
            })

    # Sort by confidence descending
    matches.sort(key=lambda x: (x["confidence"], x["matched_count"]), reverse=True)
    
    if not matches:
        return None, 0, []
        
    return matches[0]["case"], matches[0]["confidence"], matches[:3]

def format_clinical_response(best_match, symptoms, collected_vars, confidence, all_matches=None):
    """
    Formats the clinical report as requested:
    Clinical Diagnostic Report
    1. Clinical Summary (with durations)
    2. Risk Score
    3. Severity Assessment
    4. Possible Conditions (Top 3)
    5. Recommended Specialist
    6. Suggested Action
    """
    # 1. Clinical Summary with duration tracking
    formatted_symptoms = []
    if symptoms:
        for s in sorted(symptoms):
            # Check if we have duration data for this symptom
            duration = ""
            if s == "fever" and "fever_duration" in collected_vars:
                duration = f": {collected_vars['fever_duration']}"
            elif s in ["chest pain", "abdominal pain", "ear pain", "joint pain", "back pain"] and "duration" in collected_vars:
                 duration = f": {collected_vars['duration']}"
            
            formatted_symptoms.append(f"- {s.title()}{duration}")
            
    summary_text = "\n".join(formatted_symptoms) if formatted_symptoms else "No specific symptoms detected."
    summary = f"**Symptoms detected:**\n{summary_text}"

    # 2. Possible Conditions
    conditions_list = []
    top_confidence = confidence
    
    if all_matches:
        for m in all_matches:
             name = m["case"]["associations"][0] if m["case"]["associations"] else "Unknown"
             pct = int(m["confidence"] * 100)
             conditions_list.append(f"{len(conditions_list)+1}. {name} ({pct}%)")
    
    conditions_text = "\n".join(conditions_list)
    if not conditions_list:
        conditions_text = "None identified above threshold."
    
    if top_confidence < 0.40:
        # Check if the domain is Mental Health
        domain = detect_locked_domain(symptoms)
        if domain == "MENTAL_HEALTH":
            advisory = "*Note: It appears your symptoms may be related to anxiety or panic episodes. These experiences can feel overwhelming but are treatable with proper support.*"
        else:
            advisory = "*Note: Your symptom profile is currently broad. This may represent an early-stage condition or a mild viral response. Please monitor your symptoms closely.*"
        
        if conditions_text == "None identified above threshold.":
            conditions_text = advisory
        else:
            conditions_text += f"\n\n{advisory}"

    # 3. Severity Assessment & Risk Score
    score, risk_class = calculate_risk_score(symptoms)
    severity_icon = "🟢" if risk_class == "LOW" else "🟡" if risk_class == "MODERATE" else "🔴"

    # 4. Immediate Advice -> Suggested Action
    default_advice = (
        "• Rest and avoid strenuous activity\n"
        "• Drink plenty of fluids to stay hydrated\n"
        "• Use fever-reducing medication if temperature exceeds 38°C\n"
        "• Seek medical care if symptoms worsen or breathing difficulty develops"
    )
    
    advice = default_advice
    if best_match and best_match.get("first_aid"):
        advice = "\n".join([f"• {step}" for step in best_match["first_aid"]])

    # 5. Recommended Specialist
    specialist = best_match["specialist"] if best_match else "General Physician"

    response = (
        f"# 🏥 Clinical Diagnostic Report\n\n"
        f"### Clinical Summary\n{summary}\n\n"
        f"### Risk Score\n**{score} / 10**\n\n"
        f"### Severity\n{severity_icon} **{risk_class}**\n\n"
        f"### Top Probable Conditions\n{conditions_text}\n\n"
        f"### Recommended Specialist\n**{specialist}**\n\n"
        f"### Suggested Action\n{advice}\n\n"
        f"---\n"
        f"⚠️ *{DISCLAIMER}*"
    )
    
    return response

def format_triage_initial(symptoms, all_matches, question):
    """
    STEP 1 — Initial Triage Output.
    Shows detected symptoms, preliminary conditions, and the first follow-up question.
    Does NOT include risk score, severity, or the final specialist recommendation.
    """
    # Detected symptoms list
    sym_lines = "\n".join(f"- {s.title()}" for s in sorted(symptoms))
    if not sym_lines:
        sym_lines = "- (none detected yet)"

    # Preliminary conditions (top 3 from matching engine)
    if all_matches:
        cond_lines = "\n".join(
            f"{i+1}. {m['case']['associations'][0]}"
            for i, m in enumerate(all_matches[:3])
            if m['case']['associations']
        )
    else:
        cond_lines = "- Gathering more information…"

    question_block = f"**To refine the diagnosis, I need to ask:**\n\n{question}" if question else \
        "Could you describe your symptoms in a bit more detail?"

    return (
        f"## 🩺 Clinical Summary\n\n"
        f"**Detected symptoms:**\n{sym_lines}\n\n"
        f"---\n\n"
        f"**Preliminary Possible Conditions:**\n{cond_lines}\n\n"
        f"---\n\n"
        f"{question_block}"
    )


def format_investigation_update(new_symptoms, all_symptoms):
    """
    STEP 2 — Investigation Update.
    Shown after a user answers a follow-up question.
    Briefly confirms new symptoms detected in the answer and lists the merged symptom set.
    """
    new_lines = "\n".join(f"- {s.title()}" for s in sorted(new_symptoms)) if new_symptoms else \
        "- (answer recorded — no new clinical symptom identified)"

    all_lines = "\n".join(f"- {s.title()}" for s in sorted(all_symptoms))

    return (
        f"**Answer processed.**\n\n"
        f"**New symptom detected:**\n{new_lines}\n\n"
        f"**Updated symptoms:**\n{all_lines}"
    )


def get_next_investigation_question(symptoms, collected_vars):
    """
    Ask questions related ONLY to detected symptoms.
    """
    for s in symptoms:
        if s in data.SYMPTOM_QUESTIONS:
            if s not in collected_vars:
                return data.SYMPTOM_QUESTIONS[s], [s]
    
    return None, None

def expand_affirmative_symptoms(symptom, answer):
    """
    If a user answers 'yes' to a follow-up question, expand the symptom set.
    """
    affirmative_keywords = ["yes", "yeah", "yep", "sure", "definitely", "i do", "it is", "correct"]
    answer_clean = answer.lower().strip()
    
    if any(keyword in answer_clean for keyword in affirmative_keywords):
        return data.AFFIRMATIVE_SYMPTOMS.get(symptom, [])
    return []

MENTAL_HEALTH_RED_FLAGS = {
    "want to die", "suicidal thoughts", "want to harm myself", "kill myself",
    "harming myself", "end my life"
}

def get_emergency_type(text, symptoms):
    """
    Detects if the user is in a physical medical emergency or a mental health crisis.
    Returns: "PHYSICAL", "MENTAL", or None.
    """
    text_lower = text.lower()
    
    # 1. Check Mental Health First (High Priority Support)
    if any(flag in text_lower for flag in MENTAL_HEALTH_RED_FLAGS) or \
       "suicidal thoughts" in symptoms:
        return "MENTAL"
    
    # 2. Check Physical Red Flags
    if any(flag in text_lower for flag in data.RED_FLAGS) or \
       any(s in data.RED_FLAGS for s in symptoms):
        return "PHYSICAL"
        
    return None

def get_emergency_response():
    """Returns the standard template for physical medical emergencies."""
    return (
        "🚨 **EMERGENCY MEDICAL ALERT**\n\n"
        "Your description includes critical indicators that require immediate medical attention.\n\n"
        "**Immediate Actions:**\n"
        "1. **Call 911** or your local emergency services immediately.\n"
        "2. Do not attempt to drive yourself to the hospital.\n"
        "3. Keep the airway clear and stay in a rested position.\n"
        "4. Notify someone nearby of your situation.\n\n"
        "**Potential Severity:** CRITICAL\n"
        "**Recommended Facility:** Emergency Department\n\n"
        f"⚠️ *{DISCLAIMER}*"
    )

def get_mental_health_crisis_response():
    """Returns the supportive template for mental health crises."""
    return (
        "🚨 **Mental Health Crisis Alert**\n\n"
        "I'm really sorry that you're feeling this way. You are not alone.\n\n"
        "**Immediate Support Options:**\n"
        "• Contact a crisis hotline (e.g., 988 in the US)\n"
        "• Reach out to a trusted friend or family member\n"
        "• Seek professional mental health support\n\n"
        "**Recommended Specialist:**\n"
        "**Psychiatrist / Mental Health Counselor**\n\n"
        f"⚠️ *{DISCLAIMER}*"
    )
