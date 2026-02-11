import os
from tavily import TavilyClient

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# List of High-Trust Domains for Fact Checking
TRUSTED_DOMAINS = [
    "reuters.com", "apnews.com", "bbc.com", "snopes.com", 
    "factcheck.org", "politifact.com", "nytimes.com", 
    "washingtonpost.com", "theguardian.com", "dw.com",
    "france24.com", "aljazeera.com", "npr.org", "pbs.org"
]

def verify_claims(query):
    """
    Performs a professional-grade fact check using strict domain filtering.
    """
    # Construct an Investigative Query
    # If the query is just a description like "Image showing Obama...", 
    # we turn it into a fact check request.
    if "fact check" not in query.lower():
        investigative_query = f"Fact check: {query}"
    else:
        investigative_query = query
        
    print(f"🔎 Investigator Searching: '{investigative_query}'")
    
    try:
        response = tavily_client.search(
            query=investigative_query,
            search_depth="advanced",
            include_answer=True,
            max_results=5,
            include_domains=TRUSTED_DOMAINS # STRICT MODE
        )
        
        sources = response.get('results', [])
        
        # If strict search fails (returns 0 results), try a broader search
        if not sources:
            print("⚠️ Strict search yielded 0 results. widening scope...")
            response = tavily_client.search(
                query=investigative_query,
                search_depth="basic",
                include_answer=True,
                max_results=5
                # No domain restriction this time
            )
            sources = response.get('results', [])

        return {
            "ai_summary": response.get('answer', 'No direct verified reports found.'),
            "sources": sources
        }
        
    except Exception as e:
        print(f"❌ Search Error: {e}")
        return {"ai_summary": "Search unavailable.", "sources": []}