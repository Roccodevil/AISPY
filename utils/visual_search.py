import os
from serpapi import GoogleSearch

# Get key from https://serpapi.com/ (Free Tier available)
SERP_API_KEY = os.getenv("SERPAPI_API_KEY")

def google_lens_search(image_url):
    """
    Performs a Reverse Image Search using Google Lens engine via SerpApi.
    Returns list of 'Visual Matches' and 'Knowledge Graph' data.
    """
    if not SERP_API_KEY:
        print("⚠️ SerpApi Key missing. Skipping Visual Search.")
        return []

    print(f"🕵️‍♂️ Running Google Lens Search on: {image_url[:50]}...")
    
    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": SERP_API_KEY
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        matches = []
        
        # 1. Exact Visual Matches
        if "visual_matches" in results:
            for item in results["visual_matches"][:3]: # Top 3 matches
                matches.append({
                    "title": item.get("title", "Visual Match"),
                    "source": item.get("source", "Web Source"),
                    "link": item.get("link", "#"),
                    "thumbnail": item.get("thumbnail", "")
                })

        # 2. Knowledge Graph (If Google recognizes a celebrity/object)
        if "knowledge_graph" in results:
            kg = results["knowledge_graph"]
            matches.append({
                "title": f"Identified Entity: {kg.get('title')}",
                "source": kg.get("subtitle", "Google Knowledge Graph"),
                "link": kg.get("link", "#"),
                "thumbnail": kg.get("image", "")
            })

        print(f"✅ Found {len(matches)} visual references.")
        return matches

    except Exception as e:
        print(f"❌ Visual Search Error: {e}")
        return []