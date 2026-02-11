import os
import json
import re
from groq import Groq

# Initialize Groq Client
# Ensure GROQ_API_KEY is correct in .env
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_verdict(query, deepfake_data, search_data):
    """
    Uses Groq (Llama-3) to synthesize the report.
    Includes ERROR HANDLING to prevent 'Expecting value' crashes.
    """
    print("🧠 Brain is thinking (via Groq)...")

    system_prompt = """
    You are AI-SPY, a Digital Forensics Analyst.
    
    RULES FOR VERDICT:
    1. If 'Visual Evidence' suggests High Probability (>80%) of AI/Deepfake -> Verdict: "Fake" (unless proven otherwise by trusted news).
    2. If Search Results explicitly say "Debunked" or "False" -> Verdict: "Fake" or "Misleading".
    3. If Search Results confirm the event happened exactly as shown -> Verdict: "Real".
    
    Output strictly VALID JSON:
    {
        "verdict": "Real" | "Fake" | "Misleading" | "Unverified",
        "confidence": 0-100,
        "reasoning": "Concise explanation citing specific evidence."
    }
    """

    user_prompt = f"""
    QUERY: {query}
    VISUAL EVIDENCE: {deepfake_data}
    SEARCH CONTEXT: {search_data}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"} 
        )

        # 1. CAPTURE RAW OUTPUT
        raw_content = completion.choices[0].message.content
        print(f"🔍 DEBUG: Raw Groq Response: '{raw_content}'") # Check your terminal for this!

        if not raw_content:
            raise ValueError("Groq returned an empty string.")

        # 2. ATTEMPT PARSE
        return raw_content

    except Exception as e:
        print(f"❌ CRITICAL BRAIN ERROR: {e}")
        
        # 3. FALLBACK (Prevents the crash!)
        # If Groq fails, we return this default report so the app keeps running.
        fallback_report = json.dumps({
            "verdict": "Unverified",
            "confidence": 0,
            "reasoning": f"AI Analysis failed. (Error: {str(e)}). Please check your API Key or Quota."
        })
        return fallback_report