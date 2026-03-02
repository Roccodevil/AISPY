import os
import json
from groq import Groq

# Initialize Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_verdict(query, deepfake_data, search_data):
    """
    Synthesizes Forensic Data + Search Data into a Final Verdict using Groq API.
    """
    print("🧠 Brain is thinking (via Groq Llama 3.3)...")

    system_prompt = """
    You are AI-SPY, an expert Digital Forensics & Fact-Checking Analyst.
    Determine if the input (media or text claim) is Real, Fake, or Misleading.
    
    INPUT DATA:
    1. User Query/Claim: {query}
    2. Visual Forensics: {deepfake_data}
    3. Web Search Context: {search_data}
    
    RULES:
    - IF VISUAL DATA IS PROVIDED: Use it to detect manipulated media. (>80% fake score = FAKE).
    - IF TEXT ONLY ("N/A"): Ignore visual rules and fact-check purely based on the Web Search Context.
    - If Web Search proves the claim is false or "Debunked", verdict is FAKE.
    - If Web Search confirms the claim with reliable sources, verdict is REAL.
    - If evidence is conflicting or missing, verdict is UNVERIFIED.
    
    OUTPUT JSON ONLY:
    {
        "verdict": "Real" | "Fake" | "Misleading" | "Unverified",
        "confidence": 0-100,
        "reasoning": "Short explanation."
    }
    """

    user_message = f"Query: {query}\nVisuals: {deepfake_data}\nSearch: {search_data}"

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        return completion.choices[0].message.content

    except Exception as e:
        print(f"❌ Brain Error: {e}")
        return json.dumps({
            "verdict": "Unverified",
            "confidence": 0,
            "reasoning": "AI Brain disconnected."
        })