import os
import json
import traceback
from google import genai
from dotenv import load_dotenv

# Load .env from parent directory explicitly
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

# Try to initialize the client, but don't crash if the key is missing or invalid
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and len(api_key) > 10:
        client = genai.Client(api_key=api_key)
    else:
        print("[WARNING] GEMINI_API_KEY is missing or too short. AI features will use local fallback.")
        client = None
except Exception as e:
    print(f"[WARNING] Failed to initialize Gemini Client: {e}")
    client = None

def get_chatbot_response(user_input):
    prompt = f"""
You are a medical triage assistant. Analyze symptoms and respond ONLY in the following JSON format:
{{
  "condition": "Likely condition",
  "severity": "Normal/Serious/Emergency",
  "specialist": "Doctor specialization",
  "advice": "Short advice"
}}
Input: {user_input}
"""
    # If client wasn't initialized or models crashed, use local fallback
    if client:
        # Try Fast model first, then fall back to Pro
        models_to_try = ["gemini-2.5-flash", "gemini-2.5-pro"]
        
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                text = response.text.strip()
                
                # Extract JSON
                if "```json" in text:
                    text = text.split("```json")[-1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[-1].split("```")[0].strip()
                    
                data = json.loads(text)
                print(f"[AI INFO] Successfully parsed intent using {model_name}")
                return data
                
            except Exception as e:
                # If flash crashes or fails mapping JSON, it loops back and tries pro
                print(f"--- {model_name} API Error: {e} ---")
                continue
                
        print("--- Both Gemini Flash and Pro failed. Triggering Local Fallback ---")
    else:
        print("--- Gemini API not configured. Triggering Local Fallback ---")
        

    # LOCAL FALLBACK FOR RATE LIMITS OR OFFLINE
    # This ensures the user gets a response even if the API is throttled
    ui = user_input.lower()
    if any(w in ui for w in ["headache", "head", "nausea", "light"]):
        return {
            "condition": "Migraine / Tension Headache (Local Analysis)",
            "severity": "Serious",
            "specialist": "Neurologist",
            "advice": "Rest in a dark, quiet room. Stay hydrated. If it's the worst headache of your life, seek emergency care."
        }
    elif any(w in ui for w in ["chest", "breath", "heart"]):
        return {
            "condition": "Cardiovascular Distress (Local Analysis)",
            "severity": "Emergency",
            "specialist": "Cardiologist",
            "advice": "Seek immediate medical attention. Call 108/112 if you have crushing pain or shortness of breath."
        }
    elif any(w in ui for w in ["stomach", "vomit", "belly"]):
        return {
            "condition": "Gastrointestinal Issue (Local Analysis)",
            "severity": "Normal",
            "specialist": "Gastroenterologist",
            "advice": "Eat bland foods, stay hydrated with electrolytes, and monitor for fever."
        }
    elif any(w in ui for w in ["pain", "body", "muscle", "back", "joint"]):
        return {
            "condition": "Musculoskeletal strain or generalized body ache (Local Analysis)",
            "severity": "Normal",
            "specialist": "Orthopedist",
            "advice": "Rest the affected area. Apply ice or heat. Over-the-counter pain relievers may help. See a doctor if pain persists."
        }
        
    return {
        "error": "API Throttled",
        "condition": "Unidentified symptoms (Local Analysis)",
        "severity": "Normal",
        "specialist": "General Physician",
        "advice": "The AI is currently under high load and relies on local fallbacks. I cannot definitively diagnose your condition. Please consult a General Physician."
    }