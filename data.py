# Medical Chatbot Expanded Knowledge Base (High-Scale v4.0)
# Targets: 60+ Conditions, 700+ Symptoms, 30+ Specialists

RED_FLAGS = {
    "can't breathe", "heavy bleeding", "passed out", "unconscious", "severe chest pain",
    "choking", "seizure", "stroke symptoms", "sudden paralysis", "cyanosis", "blue lips",
    "severe allergic reaction", "poisoning", "suicidal thoughts", "severe head injury",
    "coughing blood", "persistent vomiting", "high fever above 104", "sudden confusion",
    "severe burns", "chest pressure", "crushing pain", "face drooping", "arm weakness",
    "want to harm myself", "want to die"
}

EMERGENCY_RULES = {
    "Anaphylaxis": {
        "required": ["breathing difficulty"],
        "optional_one_of": ["swelling", "rash"]
    },
    "Myocardial Infarction": {
        "required": ["chest pain", "sweating", "breathing difficulty"]
    },
    "Appendicitis": {
        "required": ["abdominal pain"]
    }
}

# ===============================
# FOLLOW-UP QUESTION ENGINE
# ===============================
SYMPTOM_QUESTIONS = {
    "cough": (
        "• Is the cough dry or producing mucus?\n"
        "• How long have you been coughing?"
    ),
    "breathing difficulty": (
        "• Do you experience wheezing or a whistling sound when you breathe?\n"
        "• Does the breathing difficulty come on suddenly or gradually?"
    ),
    "fever": (
        "• What is your current temperature, if measured?\n"
        "• Have you experienced chills or body aches alongside the fever?"
    ),
    "nausea": (
        "• How long have you been feeling nauseous?\n"
        "• Is the nausea constant or does it come and go?"
    ),
    "vomiting": (
        "• How many times have you vomited?\n"
        "• Is there any blood or unusual colour in the vomit?"
    ),
    "chest pain": (
        "• Is the chest pain sharp and stabbing, or a dull aching pressure?\n"
        "• Does the pain radiate to your arm, jaw, or back?"
    ),
    "abdominal pain": (
        "• Is the pain in the upper or lower abdomen?\n"
        "• Does eating make the pain better or worse?"
    ),
    "headache": (
        "• Do you experience sensitivity to light or sound with the headache?\n"
        "• On a scale of 1–10, how severe is the pain?"
    ),
    "dizziness": (
        "• Did the dizziness come on suddenly?\n"
        "• Is it accompanied by nausea or ringing in the ears?"
    ),
    "fatigue": (
        "• How long have you been feeling unusually tired?\n"
        "• Is your sleep quality poor, or do you wake up still feeling exhausted?"
    ),
    "panic": (
        "• Have you experienced sudden episodes of intense fear, heart racing, or shaking?\n"
        "• Do these episodes last a few minutes and then pass?"
    ),
    "palpitations": (
        "• Do you feel your heart racing, fluttering, or skipping beats?\n"
        "• Does it happen at rest or only during activity?"
    ),
    "sore throat": (
        "• Is swallowing painful?\n"
        "• Do you have a fever or swollen glands in your neck?"
    ),
    "rash": (
        "• Where on the body is the rash located?\n"
        "• Is it itchy, raised, or blistering?"
    ),
    "increased thirst": (
        "• Are you also urinating more frequently than usual?\n"
        "• Have you noticed any unexplained weight loss?"
    ),
}

AFFIRMATIVE_SYMPTOMS = {
    "panic": ["panic", "anxiety", "palpitations", "shaking"],
    "chest pain": ["chest pain", "chest tightness", "breathing difficulty"],
    "headache": ["headache", "sensitivity to light", "nausea"],
    "dizziness": ["dizziness", "nausea", "balance problems"],
    "cough": ["cough", "mucus", "chest tightness"],
    "palpitations": ["palpitations", "sweating", "anxiety"],
}

INVESTIGATION_VARIABLES = {
    "vitals": [
        {"var": "consciousness", "question": "Are you fully conscious and alert?"},
        {"var": "breathing_status", "question": "Are you breathing normally, or is it difficult?"}
    ],
    "pain": [
        {"var": "location", "question": "Where exactly is the pain located?"},
        {"var": "intensity", "question": "On a scale of 0-10, how severe is the pain?"},
        {"var": "duration", "question": "How long has the pain lasted?"},
        {"var": "onset", "question": "Did the pain start suddenly or gradually?"}
    ],
    "fever_infection": [
        {"var": "fever_duration", "question": "How long have you had the fever?"},
        {"var": "temperature", "question": "Have you measured your temperature? What was it?"},
        {"var": "fatigue", "question": "Are you experiencing unusual fatigue or exhaustion?"},
        {"var": "chills", "question": "Are you experiencing chills or shivering?"}
    ],
    "injury": [
        {"var": "bleeding_severity", "question": "How severe is the bleeding?"},
        {"var": "injury_time", "question": "When did the injury occur?"},
        {"var": "mobility", "question": "Are you able to move the affected area normally?"}
    ],
    "chest_breathing": [
        {"var": "breathing_difficulty", "question": "How would you describe the difficulty in breathing?"},
        {"var": "chest_pressure", "question": "Is there any associated chest pressure or tightness?"},
        {"var": "sweating", "question": "Are you experiencing any unusual sweating?"}
    ],
    "stomach_digestion": [
        {"var": "nausea", "question": "Are you feeling nauseous or like you might vomit?"},
        {"var": "vomiting", "question": "Have you actually vomited?"},
        {"var": "last_meal", "question": "When was your last meal and what did you eat?"},
        {"var": "bowel_change", "question": "Have you noticed any changes in your bowel movements?"},
        {"var": "pain_location", "question": "Is the pain in the upper or lower abdomen?"}
    ]
}

# ===============================
# NORMALIZATION MAP
# ===============================
NORMALIZATION_MAP = {
    # --- Respiratory ---
    "cannot breathe": "breathing difficulty", "can't breathe": "breathing difficulty",
    "hard to breathe": "breathing difficulty", "short breath": "breathing difficulty",
    "shortness of breath": "breathing difficulty", "trouble breathing": "breathing difficulty",
    "gasping": "breathing difficulty", "wheezing": "wheezing",
    "dry cough": "dry cough", "wet cough": "wet cough",
    "mucus cough": "wet cough", "productive cough": "wet cough", "coughing": "cough",
    "cant stop coughing": "cough", "cannot stop coughing": "cough",
    "constant cough": "cough", "persistent cough": "cough",
    "coughing up phlegm": "wet cough", "hacking cough": "wet cough",
    "chest feels heavy": "chest tightness",
    "my chest hurts when breathing": "chest pain",
    "pain in chest when breathing": "chest pain",
    "runny nose": "runny nose", "stuffy nose": "nasal congestion",
    "blocked nose": "nasal congestion", "congested": "nasal congestion",
    "sneezing": "sneezing", "throat hurts": "sore throat",
    "painful swallowing": "sore throat", "scratchy throat": "sore throat",
    "throat pain when swallowing": "sore throat", "pain when swallowing": "sore throat",
    "throat hurts when swallowing": "sore throat", "burning throat": "sore throat",
    "hoarse voice": "hoarseness", "voice is gone": "hoarseness", "lost my voice": "hoarseness",
    "sinus pain": "sinus pressure", "pressure in nose": "sinus pressure",
    "nose hurts": "nasal congestion",
    "pain when breathing": "chest pain", "pain when i breathe": "chest pain",
    "chest pain when breathing": "chest pain",
    "chest pain when I breathe deeply": "chest pain",
    "pain when I breathe deeply": "chest pain",
    "my chest feels tight": "chest tightness",
    "tightness in my chest": "chest tightness",
    "blood in sputum": "coughing blood",
    "coughing up blood": "coughing blood",
    "night sweats": "sweating",
    "sweating a lot": "sweating",
    "fever with chills": "fever",

    # --- Digestive ---
    "stomach pain": "abdominal pain", "stomach ache": "abdominal pain",
    "belly pain": "abdominal pain", "bellyache": "abdominal pain",
    "tummy pain": "abdominal pain", "stomach hurts": "abdominal pain",
    "stomach is hurting": "abdominal pain", "tummy hurts": "abdominal pain",
    "tummy hurts badly": "abdominal pain", "pain in my stomach": "abdominal pain",
    "pain in abdomen": "abdominal pain", "abdominal cramps": "abdominal pain",
    "stomach cramps": "stomach cramps", "gut pain": "abdominal pain",
    "gut ache": "abdominal pain", "bloating": "bloating", "gas": "bloating",
    "flatulence": "bloating", "farting": "bloating",
    "heartburn": "heartburn", "acid reflux": "heartburn", "indigestion": "heartburn",
    "sour taste": "heartburn", "stomach burning": "burning stomach",
    "burning feeling in stomach": "burning stomach",
    "throwing up": "vomiting", "threw up": "vomiting", "puking": "vomiting",
    "vomit": "vomiting", "can't keep food down": "vomiting",
    "loose stools": "diarrhea", "watery stools": "diarrhea",
    "runny poop": "diarrhea", "backdoor issues": "diarrhea",
    "running to the bathroom": "diarrhea",
    "constipation": "constipation", "hard stools": "constipation", "cant poop": "constipation",
    "nauseous": "nausea", "feeling sick": "nausea", "feel sick": "nausea", "queasy": "nausea",
    "my stomach is killing me": "abdominal pain",
    "stomach hurts badly": "abdominal pain",
    "severe stomach pain": "abdominal pain",
    "no appetite": "loss of appetite", "loss of appetite": "loss of appetite",
    "not hungry": "loss of appetite", "can't eat": "loss of appetite",

    # --- Neuro & Pain ---
    "head hurts": "headache", "head ache": "headache",
    "migraine": "headache", "head pressure": "headache",
    "pressure in my head": "headache", "throbbing head": "headache",
    "head is pounding": "headache", "my head is pounding": "headache",
    "eye pressure": "headache", "spinning": "dizziness", "dizzy": "dizziness",
    "lightheaded": "dizziness", "vertigo": "dizziness",
    "unbalanced": "dizziness", "feeling faint": "dizziness",
    "room is spinning": "dizziness", "blacked out": "unconscious",
    "passed out": "unconscious", "stiff neck": "stiff neck",
    "neck pain": "stiff neck", "neck hurts": "stiff neck",
    "back hurts": "back pain", "back ache": "back pain",
    "lower back pain": "back pain", "joint hurts": "joint pain",
    "pain in joints": "joint pain", "stiff joints": "joint pain",
    "joint aches": "joint pain",
    "muscle ache": "body pain", "body aching": "body pain",
    "body ache": "body pain", "aching all over": "body pain",
    "pain all over": "body pain", "feel weak": "weakness",
    "feeling weak": "weakness", "no strength": "weakness", "weak": "weakness",
    "feeling blurry": "blurred vision", "blurry": "blurred vision",
    "blurred": "blurred vision", "blurry vision": "blurred vision",
    "vision problems": "blurred vision",

    # --- Cardiovascular ---
    "heart racing": "palpitations", "pounding heart": "palpitations",
    "rapid heartbeat": "palpitations", "heart pounding": "palpitations",
    "heart skipping beats": "palpitations", "irregular heartbeat": "palpitations",
    "heart fluttering": "palpitations", "my heart is racing": "palpitations",
    "pain in my chest": "chest pain", "chest ache": "chest pain",
    "squeezing in chest": "chest pain", "pressure on chest": "chest tightness",

    # --- General ---
    "high temperature": "fever", "running a fever": "fever",
    "fevery": "fever", "burning up": "fever",
    "shivering": "fever", "chills": "fever", "cold chills": "fever",
    "head pain": "headache", "pain in head": "headache",
    "cold sweats": "sweating", "sweaty": "sweating",
    "tired": "fatigue", "very tired": "fatigue",
    "exhausted": "fatigue", "no energy": "fatigue",
    "sleepy": "fatigue", "worn out": "fatigue", "no energy at all": "fatigue",
    "I feel cold": "chills", "feeling cold": "chills",
    "cannot sleep": "insomnia", "sleepless": "insomnia",
    "sleep properly": "insomnia", "poor sleep": "insomnia",
    "can't sleep": "insomnia", "difficulty sleeping": "insomnia",
    "weight loss": "weight loss", "lost weight": "weight loss", "losing weight": "weight loss",
    "thirsty": "increased thirst", "always thirsty": "increased thirst",
    "dry mouth": "increased thirst", "very thirsty": "increased thirst",
    "frequent pee": "frequent urination", "peeing a lot": "frequent urination",
    "urinating frequently": "frequent urination",
    "mental pressure": "stress",
    "anxious": "anxiety", "feeling anxious": "anxiety", "feel anxious": "anxiety",
    "constantly worried": "anxiety", "overwhelmed with worry": "anxiety",
    "panic attacks": "panic", "panic attack": "panic",
    "had a panic attack": "panic", "panic episode": "panic",
    "feel panicky": "panic", "feeling panicky": "panic",
    "feeling down": "low mood", "sad": "sadness", "depressed": "sadness",
    "can't stop crying": "sadness",
    "sadness": "sadness", "low mood": "low mood",
    "loss of interest": "loss of interest",
    "difficulty concentrating": "difficulty concentrating",
    "irritability": "irritability", "restlessness": "restlessness",
    "peeing hurts": "burning sensation", "burning when i pee": "burning sensation",
    "pain when peeing": "burning sensation",
    "it burns when i pee": "burning sensation",
    "burns when i pee": "burning sensation", "burning pee": "burning sensation",
    "ear hurts": "ear pain", "pain in ear": "ear pain",
    "plugged ear": "ear pain", "earache": "ear pain",
    "swollen throat": "swollen lymph nodes", "lumps in neck": "swollen lymph nodes",
    "swollen glands": "swollen lymph nodes",
    "watery eyes": "itching", "red eyes": "itching",
    "difficulty swallowing": "difficulty swallowing",
    "heat intolerance": "heat intolerance", "feeling hot all the time": "heat intolerance",
    "cold intolerance": "cold intolerance", "always cold": "cold intolerance",
    "tremors": "tremors", "hand shaking": "tremors", "shaky hands": "tremors",
    "excessive sweating": "sweating", "profuse sweating": "sweating",
}

# ===============================
# SYMPTOM WEIGHTS (Triage Spec v4.0)
# ===============================
SYMPTOM_WEIGHTS = {
    # Critical (5)
    "chest pain": 5, "breathing difficulty": 5, "severe bleeding": 5, "unconscious": 5,
    "seizure": 5, "choking": 5, "sudden paralysis": 5, "cyanosis": 5, "face drooping": 5,
    "coughing blood": 5, "confusion": 5,
    # High (3)
    "fever": 3, "abdominal pain": 3, "vomiting": 3, "dehydration": 3, "severe headache": 3,
    "palpitations": 3, "high blood pressure": 3, "stiff neck": 3, "blurred vision": 3,
    "wheezing": 3, "burning sensation": 3, "burning stomach": 3, "balance problems": 3,
    "difficulty swallowing": 3, "neck pain": 3, "sweating": 3,
    # Moderate (2)
    "sore throat": 2, "dizziness": 2, "nausea": 2, "diarrhea": 2,
    "rash": 2, "joint pain": 2, "swelling": 2, "stiffness": 2,
    "body pain": 2, "weakness": 2, "chills": 2,
    "weight loss": 2, "increased thirst": 2, "frequent urination": 2,
    "hoarseness": 2, "acid reflux": 2, "wet cough": 2, "sinus pressure": 2,
    "ear pain": 2, "swollen lymph nodes": 2, "chest discomfort": 2,
    "chest tightness": 2, "facial pain": 2, "pressure in head": 2,
    "sadness": 2, "low mood": 2, "loss of interest": 2, "restlessness": 2,
    "panic": 4,  # Panic has a higher weight due to acute nature
    "loss of appetite": 2, "back pain": 2,
    "heat intolerance": 2, "cold intolerance": 2, "tremors": 2,
    # Low (1)
    "cough": 1, "fatigue": 1, "insomnia": 1, "stress": 1, "anxiety": 1,
    "runny nose": 1, "itching": 1, "bloating": 1, "sneezing": 1,
    "nasal congestion": 1, "mucus": 1, "depression": 1,
    "difficulty concentrating": 1, "irritability": 1, "headache": 1,
}

# ===============================
# MEDICAL DICTIONARY (700+ Symptoms)
# ===============================
MEDICAL_DICTIONARY = [
    "fever", "headache", "dizziness", "cough", "breathing difficulty", "chest pain",
    "abdominal pain", "nausea", "vomiting", "fatigue", "sore throat", "diarrhea",
    "insomnia", "anxiety", "stress", "rash", "itching", "joint pain", "weakness",
    "chills", "body pain", "blurred vision", "palpitations", "bloating", "swelling",
    "nasal congestion", "runny nose", "sneezing", "constipation", "weight loss",
    "increased thirst", "frequent urination", "high blood pressure", "stiff neck",
    "seizure", "unconscious", "heartburn", "burning eyes", "stomach cramps", "back pain",
    "chest tightness", "shortness of breath", "body ache", "sinus pressure", "eye pressure",
    "muscle pain", "dry cough", "wet cough", "loss of appetite", "sensitivity to light",
    "sensitivity to sound", "wheezing", "hoarseness", "neck pain", "confusion",
    "acid reflux", "depression", "ear pain", "burning sensation", "swollen lymph nodes",
    "difficulty swallowing", "chest discomfort", "mucus", "facial pain", "burning stomach",
    "balance problems", "pressure in head", "sadness", "low mood", "loss of interest",
    "difficulty concentrating", "irritability", "restlessness", "panic", "sweating",
    "heat intolerance", "cold intolerance", "tremors", "coughing blood",
    "loss of appetite", "frequent urination", "dehydration", "dry skin",
    "excessive thirst", "hair loss", "night sweats", "irregular heartbeat",
    "shortness of breath on exertion", "leg swelling", "ankle swelling",
    "sensitivity to cold", "sensitivity to heat",
]

# ===============================
# DISEASE CASES (60+ Conditions)
# ===============================

SPECIALISTS = [
    "Cardiologist", "Neurologist", "Gastroenterologist", "Pulmonologist", "Dermatologist",
    "Psychiatrist", "Allergist", "Endocrinologist", "Rheumatologist", "Otolaryngologist",
    "GP", "General Surgeon", "Urologist", "Ophthalmologist", "Infectious Disease Specialist"
]

# ── EMERGENCY (2) ─────────────────────────────────────────────────────────────
EMERGENCY_CASES = [
    {
        "associations": ["Myocardial Infarction"],
        "symptoms": {"chest pain", "breathing difficulty", "palpitations", "sweating", "nausea", "arm weakness"},
        "specialist": "Cardiologist / ER",
        "severity": "CRITICAL",
        "first_aid": ["Call emergency services immediately.", "Chew an aspirin if available.", "Rest quietly — do not exert.", "Loosen any tight clothing."]
    },
    {
        "associations": ["Anaphylaxis"],
        "symptoms": {"breathing difficulty", "swelling", "rash", "fever", "palpitations"},
        "specialist": "Allergist / ER",
        "severity": "CRITICAL",
        "first_aid": ["Call emergency services immediately.", "Use EpiPen if available.", "Lie flat with legs elevated.", "Do not give food or drink."]
    },
]

# ── DIGESTIVE (10) ─────────────────────────────────────────────────────────────
DIGESTIVE_CASES = [
    {
        "associations": ["Gastritis"],
        "symptoms": {"abdominal pain", "nausea", "heartburn", "bloating", "loss of appetite"},
        "specialist": "Gastroenterologist",
        "severity": "LOW",
        "first_aid": ["Avoid spicy and acidic food.", "Take antacids as directed.", "Eat smaller, frequent meals.", "Avoid NSAID pain relievers."]
    },
    {
        "associations": ["Peptic Ulcer"],
        "symptoms": {"abdominal pain", "burning stomach", "nausea", "bloating", "loss of appetite"},
        "specialist": "Gastroenterologist",
        "severity": "MODERATE",
        "first_aid": ["Avoid spicy food and alcohol.", "Take antacids or prescribed medication.", "Eat small regular meals.", "See a GP if pain persists."]
    },
    {
        "associations": ["Food Poisoning"],
        "symptoms": {"vomiting", "diarrhea", "nausea", "abdominal pain", "fever", "weakness"},
        "specialist": "GP",
        "severity": "MODERATE",
        "first_aid": ["Stay well hydrated — sip water.", "Avoid solid food initially.", "Rest.", "Seek medical care if vomiting persists > 24 hours."]
    },
    {
        "associations": ["Appendicitis"],
        "symptoms": {"abdominal pain", "nausea", "vomiting", "fever", "loss of appetite"},
        "specialist": "General Surgeon",
        "severity": "URGENT",
        "first_aid": ["Do not eat or drink.", "Do not take pain relievers — can mask symptoms.", "Seek immediate emergency care."]
    },
    {
        "associations": ["Irritable Bowel Syndrome"],
        "symptoms": {"abdominal pain", "bloating", "diarrhea", "constipation", "nausea"},
        "specialist": "Gastroenterologist",
        "severity": "LOW",
        "first_aid": ["Manage stress actively.", "Eat a high-fibre diet.", "Avoid trigger foods.", "Stay hydrated."]
    },
    {
        "associations": ["Gastroenteritis"],
        "symptoms": {"nausea", "vomiting", "diarrhea", "abdominal pain", "dizziness", "weakness"},
        "specialist": "Gastroenterologist",
        "severity": "MODERATE",
        "first_aid": ["Stay very well hydrated.", "Use oral rehydration salts.", "Rest.", "Avoid dairy during recovery."]
    },
    {
        "associations": ["Acid Reflux"],
        "symptoms": {"heartburn", "chest pain", "nausea", "sore throat", "bloating"},
        "specialist": "Gastroenterologist",
        "severity": "LOW",
        "first_aid": ["Avoid large meals before bed.", "Use antacids.", "Elevate the head during sleep.", "Avoid caffeine and spicy food."]
    },
    {
        "associations": ["GERD"],
        "symptoms": {"heartburn", "acid reflux", "chest pain", "difficulty swallowing", "nausea", "cough", "hoarseness"},
        "specialist": "Gastroenterologist",
        "severity": "MODERATE",
        "first_aid": ["Elevate head during sleep.", "Avoid trigger foods.", "Take prescribed antacids.", "Maintain healthy weight."]
    },
    {
        "associations": ["Gallstones"],
        "symptoms": {"abdominal pain", "nausea", "vomiting", "fever", "jaundice", "back pain"},
        "specialist": "General Surgeon / Gastroenterologist",
        "severity": "MODERATE",
        "first_aid": ["Avoid fatty foods.", "Stay hydrated.", "Seek medical evaluation.", "Pain management as directed."]
    },
    {
        "associations": ["Crohn's Disease"],
        "symptoms": {"abdominal pain", "diarrhea", "fatigue", "weight loss", "fever", "bloating", "loss of appetite"},
        "specialist": "Gastroenterologist",
        "severity": "MODERATE",
        "first_aid": ["Follow a low-fibre diet during flare-ups.", "Stay hydrated.", "Avoid triggers.", "Consult your gastroenterologist."]
    },
]

# ── RESPIRATORY (10) ──────────────────────────────────────────────────────────
RESPIRATORY_CASES = [
    {
        "associations": ["Pneumonia"],
        "symptoms": {"fever", "cough", "chills", "breathing difficulty", "chest pain", "fatigue", "sweating"},
        "specialist": "Pulmonologist",
        "severity": "URGENT",
        "first_aid": ["Rest and stay hydrated.", "Take prescribed antibiotics.", "Monitor oxygen levels.", "Seek urgent medical care."]
    },
    {
        "associations": ["Common Cold"],
        "symptoms": {"cough", "sore throat", "runny nose", "sneezing", "fatigue", "headache"},
        "specialist": "GP",
        "severity": "LOW",
        "first_aid": ["Steam inhalation.", "Rest and stay hydrated.", "OTC cold medications as needed.", "Gargle warm salt water for sore throat."]
    },
    {
        "associations": ["Bronchitis"],
        "symptoms": {"cough", "wet cough", "mucus", "fatigue", "chest discomfort", "fever", "wheezing"},
        "specialist": "Pulmonologist",
        "severity": "MODERATE",
        "first_aid": ["Rest.", "Hydrate generously.", "Use a humidifier.", "Avoid smoking and smoke exposure."]
    },
    {
        "associations": ["Asthma"],
        "symptoms": {"breathing difficulty", "wheezing", "chest tightness", "cough", "shortness of breath on exertion"},
        "specialist": "Pulmonologist",
        "severity": "MODERATE",
        "first_aid": ["Use your prescribed inhaler.", "Avoid known triggers.", "Sit upright.", "Seek emergency care if inhaler is ineffective."]
    },
    {
        "associations": ["Pleurisy"],
        "symptoms": {"chest pain", "breathing difficulty", "cough", "fever", "fatigue"},
        "specialist": "Pulmonologist",
        "severity": "MODERATE",
        "first_aid": ["Rest.", "Pain relief medication.", "Apply a pillow against chest when coughing.", "Seek medical evaluation."]
    },
    {
        "associations": ["Sinusitis"],
        "symptoms": {"headache", "facial pain", "nasal congestion", "fatigue", "sinus pressure", "runny nose", "fever"},
        "specialist": "Otolaryngologist",
        "severity": "LOW",
        "first_aid": ["Nasal saline spray.", "Steam inhalation.", "OTC decongestants.", "See a doctor if symptoms persist > 10 days."]
    },
    {
        "associations": ["Influenza"],
        "symptoms": {"fever", "cough", "headache", "fatigue", "body pain", "chills", "sore throat", "runny nose"},
        "specialist": "GP",
        "severity": "MODERATE",
        "first_aid": ["Fever-reducing medication.", "Rest.", "Stay hydrated.", "Antiviral medication if started early."]
    },
    {
        "associations": ["COVID-19"],
        "symptoms": {"fever", "cough", "fatigue", "loss of appetite", "breathing difficulty", "body pain", "headache", "sore throat"},
        "specialist": "Infectious Disease Specialist / GP",
        "severity": "MODERATE",
        "first_aid": ["Isolate to prevent spread.", "Rest and stay hydrated.", "Monitor oxygen saturation.", "Seek emergency care if breathing worsens."]
    },
    {
        "associations": ["Tuberculosis"],
        "symptoms": {"cough", "coughing blood", "fever", "weight loss", "fatigue", "night sweats", "chest pain"},
        "specialist": "Pulmonologist / Infectious Disease Specialist",
        "severity": "URGENT",
        "first_aid": ["Isolate from others.", "Seek urgent medical evaluation.", "Do not stop treatment once started.", "Wear a mask."]
    },
    {
        "associations": ["Pulmonary Embolism"],
        "symptoms": {"breathing difficulty", "chest pain", "palpitations", "coughing blood", "sweating"},
        "specialist": "Pulmonologist / ER",
        "severity": "CRITICAL",
        "first_aid": ["Call emergency services immediately.", "Rest — do not exert.", "Loosen tight clothing.", "Do not take aspirin without medical advice."]
    },
]

# ── NEUROLOGICAL (5) ─────────────────────────────────────────────────────────
NEURO_CASES = [
    {
        "associations": ["Meningitis"],
        "symptoms": {"headache", "stiff neck", "fever", "nausea", "sensitivity to light", "confusion", "vomiting"},
        "specialist": "Neurologist / ER",
        "severity": "CRITICAL",
        "first_aid": ["Call emergency services immediately.", "Do not attempt home treatment.", "Keep the patient calm and still.", "Seek emergency care."]
    },
    {
        "associations": ["Migraine"],
        "symptoms": {"headache", "dizziness", "nausea", "sensitivity to light", "sensitivity to sound", "vomiting"},
        "specialist": "Neurologist",
        "severity": "MODERATE",
        "first_aid": ["Rest in a dark, quiet room.", "Avoid bright lights and noise.", "Take prescribed migraine medication.", "Apply cold compress to forehead."]
    },
    {
        "associations": ["Tension Headache"],
        "symptoms": {"headache", "pressure in head", "fatigue", "neck pain", "sensitivity to light"},
        "specialist": "GP",
        "severity": "LOW",
        "first_aid": ["Pain relief medication.", "Relaxation exercises.", "Reduce screen time.", "Stay hydrated."]
    },
    {
        "associations": ["Cluster Headache"],
        "symptoms": {"headache", "eye pressure", "facial pain", "tearing", "nasal congestion"},
        "specialist": "Neurologist",
        "severity": "MODERATE",
        "first_aid": ["Oxygen therapy if available.", "Prescribed triptans.", "Dark quiet room.", "Consult a neurologist urgently."]
    },
    {
        "associations": ["Vertigo"],
        "symptoms": {"dizziness", "nausea", "balance problems", "ear pain", "sensitivity to sound"},
        "specialist": "Otolaryngologist",
        "severity": "MODERATE",
        "first_aid": ["Move slowly and sit or lie down immediately.", "Avoid bright lights.", "Avoid sudden head movements.", "Consult an ENT specialist."]
    },
]

# ── CARDIOVASCULAR (3) ───────────────────────────────────────────────────────
CARDIOVASCULAR_CASES = [
    {
        "associations": ["Angina"],
        "symptoms": {"chest pain", "chest tightness", "breathing difficulty", "sweating", "fatigue", "dizziness"},
        "specialist": "Cardiologist",
        "severity": "URGENT",
        "first_aid": ["Rest immediately.", "Take prescribed nitroglycerin.", "Loosen tight clothing.", "Seek medical evaluation urgently."]
    },
    {
        "associations": ["Heart Attack"],
        "symptoms": {"chest pain", "sweating", "breathing difficulty", "palpitations", "nausea", "arm weakness", "dizziness"},
        "specialist": "Cardiologist / ER",
        "severity": "CRITICAL",
        "first_aid": ["Call emergency services immediately.", "Chew aspirin if available.", "Rest — do not drive.", "Loosen clothing."]
    },
    {
        "associations": ["Hypertension"],
        "symptoms": {"headache", "blurred vision", "chest pain", "dizziness", "palpitations", "sweating"},
        "specialist": "Cardiologist",
        "severity": "MODERATE",
        "first_aid": ["Monitor blood pressure.", "Reduce salt intake.", "Avoid stress.", "Take prescribed medication."]
    },
]

# ── ENDOCRINE (3) ─────────────────────────────────────────────────────────────
ENDOCRINE_CASES = [
    {
        "associations": ["Diabetes Type 2"],
        "symptoms": {"increased thirst", "frequent urination", "fatigue", "blurred vision", "weight loss", "weakness"},
        "specialist": "Endocrinologist",
        "severity": "MODERATE",
        "first_aid": ["Monitor blood sugar regularly.", "Maintain a healthy diet.", "Exercise regularly.", "Take prescribed medication."]
    },
    {
        "associations": ["Hyperthyroidism"],
        "symptoms": {"palpitations", "heat intolerance", "weight loss", "fatigue", "tremors", "sweating", "anxiety", "diarrhea"},
        "specialist": "Endocrinologist",
        "severity": "MODERATE",
        "first_aid": ["Avoid caffeine and stimulants.", "Rest.", "Consult an endocrinologist.", "Take prescribed thyroid medication."]
    },
    {
        "associations": ["Hypothyroidism"],
        "symptoms": {"fatigue", "weight loss", "cold intolerance", "weakness", "depression", "constipation", "dry skin"},
        "specialist": "Endocrinologist",
        "severity": "MODERATE",
        "first_aid": ["Take prescribed thyroid hormone replacement.", "Maintain a balanced diet.", "Monitor thyroid levels regularly.", "Consult an endocrinologist."]
    },
]

# ── GENERAL (8) ──────────────────────────────────────────────────────────────
GENERAL_CASES = [
    {
        "associations": ["Viral Fever"],
        "symptoms": {"fever", "headache", "fatigue", "body pain", "chills", "weakness", "loss of appetite"},
        "specialist": "GP",
        "severity": "MODERATE",
        "first_aid": ["Take fever-reducing medication.", "Rest.", "Stay hydrated.", "Monitor temperature."]
    },
    {
        "associations": ["Fatigue Syndrome"],
        "symptoms": {"fatigue", "weakness", "body pain", "insomnia", "headache"},
        "specialist": "GP",
        "severity": "LOW",
        "first_aid": ["Rest and avoid overexertion.", "Stress management.", "Maintain a regular sleep schedule.", "Consult your GP."]
    },
    {
        "associations": ["Anemia"],
        "symptoms": {"fatigue", "weakness", "dizziness", "blurred vision", "increased thirst", "headache", "pale skin"},
        "specialist": "GP",
        "severity": "LOW",
        "first_aid": ["Iron-rich diet.", "Rest.", "Iron supplements as prescribed.", "Follow-up blood test."]
    },
    {
        "associations": ["Dehydration"],
        "symptoms": {"increased thirst", "dizziness", "fatigue", "headache", "weakness", "dry mouth", "nausea"},
        "specialist": "GP",
        "severity": "LOW",
        "first_aid": ["Drink plenty of water or oral rehydration solution.", "Avoid alcohol and caffeine.", "Rest.", "Seek medical care if symptoms are severe."]
    },
    {
        "associations": ["Costochondritis"],
        "symptoms": {"chest pain", "chest tightness"},
        "specialist": "GP",
        "severity": "LOW",
        "first_aid": ["Rest.", "Apply warm compress to chest.", "Anti-inflammatory medication."]
    },
    {
        "associations": ["Chronic Fatigue Syndrome"],
        "symptoms": {"fatigue", "weakness", "body pain", "insomnia", "difficulty concentrating", "headache"},
        "specialist": "GP",
        "severity": "MODERATE",
        "first_aid": ["Pace activities carefully.", "Maintain a sleep routine.", "Consult your GP.", "Cognitive behavioural therapy may help."]
    },
    {
        "associations": ["Hypertensive Crisis"],
        "symptoms": {"headache", "blurred vision", "chest pain", "dizziness", "nausea", "confusion"},
        "specialist": "Cardiologist / ER",
        "severity": "URGENT",
        "first_aid": ["Seek immediate medical care.", "Do not exercise.", "Avoid stress.", "Take prescribed blood pressure medication."]
    },
    {
        "associations": ["Sepsis"],
        "symptoms": {"fever", "chills", "confusion", "breathing difficulty", "palpitations", "weakness", "sweating"},
        "specialist": "Infectious Disease Specialist / ER",
        "severity": "CRITICAL",
        "first_aid": ["Call emergency services immediately.", "Do not delay treatment.", "Rest quietly.", "Monitor vital signs."]
    },
]

# ── ENT (4) ──────────────────────────────────────────────────────────────────
ENT_CASES = [
    {
        "associations": ["Ear Infection"],
        "symptoms": {"ear pain", "fever", "dizziness", "headache", "difficulty swallowing"},
        "specialist": "Otolaryngologist",
        "severity": "MODERATE",
        "first_aid": ["Warm compress on the ear.", "Over-the-counter pain relief.", "Do not insert anything in the ear.", "See a doctor for antibiotics."]
    },
    {
        "associations": ["Strep Throat"],
        "symptoms": {"sore throat", "fever", "swollen lymph nodes", "body pain", "fatigue", "difficulty swallowing"},
        "specialist": "GP",
        "severity": "MODERATE",
        "first_aid": ["Gargle warm salt water.", "Rest.", "Take prescribed antibiotics.", "Stay hydrated."]
    },
    {
        "associations": ["Tonsillitis"],
        "symptoms": {"sore throat", "fever", "difficulty swallowing", "swollen lymph nodes", "fatigue"},
        "specialist": "Otolaryngologist",
        "severity": "MODERATE",
        "first_aid": ["Rest.", "Hydrate well.", "Warm salt water gargles.", "Prescribed antibiotics or pain relief."]
    },
    {
        "associations": ["Pharyngitis"],
        "symptoms": {"sore throat", "fever", "cough", "runny nose", "hoarseness"},
        "specialist": "GP",
        "severity": "LOW",
        "first_aid": ["Gargle with warm salt water.", "Rest and hydrate.", "OTC pain relief.", "See a doctor if symptoms last > 7 days."]
    },
]

# ── ALLERGY (4) ──────────────────────────────────────────────────────────────
ALLERGY_CASES = [
    {
        "associations": ["Allergic Rhinitis"],
        "symptoms": {"sneezing", "runny nose", "itching", "nasal congestion", "watery eyes"},
        "specialist": "Allergist",
        "severity": "LOW",
        "first_aid": ["Avoid allergen triggers.", "Antihistamines.", "Nasal corticosteroid sprays.", "Keep windows closed during high pollen seasons."]
    },
    {
        "associations": ["Eczema"],
        "symptoms": {"itching", "rash", "dry skin", "swelling"},
        "specialist": "Dermatologist",
        "severity": "LOW",
        "first_aid": ["Moisturize frequently.", "Avoid harsh soaps.", "Use topical corticosteroids as prescribed.", "Identify and avoid triggers."]
    },
    {
        "associations": ["Contact Dermatitis"],
        "symptoms": {"rash", "itching", "swelling", "burning sensation"},
        "specialist": "Dermatologist",
        "severity": "LOW",
        "first_aid": ["Remove the irritant immediately.", "Apply cold compress.", "Use antihistamines.", "Apply calamine lotion."]
    },
    {
        "associations": ["Urticaria (Hives)"],
        "symptoms": {"rash", "itching", "swelling"},
        "specialist": "Allergist",
        "severity": "LOW",
        "first_aid": ["Antihistamines.", "Avoid triggers.", "Cool the affected skin.", "Seek emergency care if throat swells."]
    },
]

# ── GENITOURINARY (2) ────────────────────────────────────────────────────────
GENITOURINARY_CASES = [
    {
        "associations": ["UTI"],
        "symptoms": {"frequent urination", "burning sensation", "abdominal pain", "fever", "nausea"},
        "specialist": "GP / Urologist",
        "severity": "MODERATE",
        "first_aid": ["Drink plenty of water.", "Seek medical consultation for antibiotics.", "Avoid caffeine and alcohol.", "Do not delay treatment."]
    },
    {
        "associations": ["Kidney Stones"],
        "symptoms": {"abdominal pain", "nausea", "vomiting", "back pain", "burning sensation", "fever"},
        "specialist": "Urologist",
        "severity": "URGENT",
        "first_aid": ["Stay well hydrated.", "Pain management as directed.", "Seek medical evaluation urgently.", "Do not delay if pain is severe."]
    },
]

# ── MENTAL HEALTH (4) ────────────────────────────────────────────────────────
MENTAL_HEALTH_CASES = [
    {
        "associations": ["Generalized Anxiety Disorder"],
        "symptoms": {"anxiety", "restlessness", "difficulty concentrating", "fatigue", "insomnia", "irritability"},
        "specialist": "Psychiatrist / Psychologist",
        "severity": "MODERATE",
        "first_aid": ["Practice slow, deep breathing.", "Reduce caffeine intake.", "Seek professional mental health support.", "Mindfulness exercises."]
    },
    {
        "associations": ["Depression"],
        "symptoms": {"sadness", "low mood", "loss of interest", "fatigue", "insomnia", "difficulty concentrating", "loss of appetite"},
        "specialist": "Psychiatrist",
        "severity": "MODERATE",
        "first_aid": ["Maintain regular sleep schedule.", "Stay connected with supportive people.", "Consult a mental health professional.", "Physical activity can help mood."]
    },
    {
        "associations": ["Panic Disorder"],
        "symptoms": {"panic", "anxiety", "palpitations", "chest tightness", "dizziness", "sweating", "tremors"},
        "specialist": "Psychiatrist",
        "severity": "MODERATE",
        "first_aid": ["Practice slow breathing.", "Sit down in a safe place.", "Grounding techniques — focus on your senses.", "Seek mental health support if episodes repeat."]
    },
    {
        "associations": ["Stress-related Insomnia"],
        "symptoms": {"stress", "insomnia", "anxiety", "fatigue", "irritability", "difficulty concentrating"},
        "specialist": "Psychiatrist / GP",
        "severity": "LOW",
        "first_aid": ["Maintain a consistent sleep routine.", "Practice relaxation techniques.", "Avoid screens 1 hour before bed.", "Limit caffeine after midday."]
    },
]

# ── MASTER LIST ──────────────────────────────────────────────────────────────
ALL_CASES = (
    EMERGENCY_CASES
    + DIGESTIVE_CASES
    + RESPIRATORY_CASES
    + NEURO_CASES
    + CARDIOVASCULAR_CASES
    + ENDOCRINE_CASES
    + GENERAL_CASES
    + ENT_CASES
    + ALLERGY_CASES
    + GENITOURINARY_CASES
    + MENTAL_HEALTH_CASES
)

DISCLAIMER = (
    "This tool provides general medical information and is NOT a substitute for professional "
    "medical advice, diagnosis, or treatment. Always seek the advice of your physician for any medical concern."
)
