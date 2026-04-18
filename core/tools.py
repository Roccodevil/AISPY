import os
import time
import base64
import json
import requests
from crewai.tools import tool
from tavily import TavilyClient
from groq import Groq

# ==========================================
# 1. FORENSICS TOOLS (Used by LangGraph Router)
# ==========================================

def run_hf_deepfake(image_path: str) -> dict:
    """Sends an image to Hugging Face to check for deepfake manipulation."""
    hf_token = os.getenv("HUGGINGFACE_API_KEY")
    if not hf_token:
        return {"fake_prob": 0.0, "evidence": "Hugging Face API key missing."}

    headers = {"Authorization": f"Bearer {hf_token}"}
    models = [
        "prithivMLmods/deepfake-detector-model-v1",
        "dima806/deepfake_vs_real_image_detection"
    ]

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
    except Exception as e:
        return {"fake_prob": 0.0, "evidence": f"Failed to read image: {e}"}

    for model_id in models:
        url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
        print(f"  ☁️ Querying HF Deepfake Model: {model_id}...")
        
        try:
            response = requests.post(url, headers=headers, data=image_data)
            
            # Handle cold-start loading
            if response.status_code == 503:
                print("  💤 Model is loading. Waiting 3 seconds...")
                time.sleep(3)
                response = requests.post(url, headers=headers, data=image_data)

            if response.status_code == 200:
                scores = response.json()
                if isinstance(scores, list) and isinstance(scores[0], list): 
                    scores = scores[0]
                
                for item in scores:
                    label = item.get('label', '').lower()
                    if label in ['fake', 'artificial', 'deepfake', 'ai', 'generated']:
                        prob = item.get('score', 0.0)
                        return {"fake_prob": prob, "evidence": f"Flagged by {model_id} ({prob:.1%} confidence)"}
                    elif label in ['real', 'human', 'realism'] and item.get('score', 0.0) > 0.9:
                        return {"fake_prob": 0.0, "evidence": f"Classified as Real ({item.get('score'):.1%} confidence)"}
                
                return {"fake_prob": 0.0, "evidence": "Inconclusive results."}
        except Exception as e:
            print(f"  ❌ HF Connection Error on {model_id}: {e}")

    return {"fake_prob": 0.0, "evidence": "All Deepfake models failed or timed out."}

def run_groq_vision(image_path: str) -> str:
    """Uses Groq Vision (Llama-4-Scout) to generate a highly detailed caption of the media."""
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return "Groq API key missing. Cannot generate context."

    print("  👁️ Asking Groq Vision to analyze scene context...")
    client = Groq(api_key=groq_key)
    
    try:
        with open(image_path, "rb") as image_file:
            b64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        prompt = "Describe this image in detail. What is happening? Who is in it? Return ONLY a JSON object: {\"caption\": \"detailed description\", \"subject\": \"name or 'Unknown'\"}"

        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct", # Updated to the active 2026 model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
                    ],
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(completion.choices[0].message.content)
        return f"{data.get('caption', 'Image content')}. Subject: {data.get('subject', 'Unknown')}."
        
    except Exception as e:
        print(f"  ❌ Groq Vision Error: {e}")
        return "Failed to extract vision context."

# ==========================================
# 2. OSINT TOOLS (Used by CrewAI Agents)
# ==========================================

@tool("Tavily Web Search Tool")
def tavily_search_tool(query: str) -> str:
    """
    Searches the web for facts, news articles, and debunks regarding a specific claim.
    Always pass a detailed search query to this tool.
    """
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        return "Error: Tavily API key is missing."
    
    print(f"  🔎 CrewAI Agent Searching Web: '{query}'")
    
    try:
        client = TavilyClient(api_key=tavily_key)
        # We append 'Fact check:' to nudge the search engine toward verification articles
        response = client.search(query=f"Fact check: {query}", search_depth="basic", max_results=4)
        
        results_text = ""
        for item in response.get('results', []):
            results_text += f"Source ({item['url']}): {item['content']}\n\n"
            
        return results_text if results_text else "No relevant web search results found."
        
    except Exception as e:
        return f"Web search failed: {str(e)}"
