import os
import requests
import trafilatura

def web_search(query: str) -> dict:
    """Search the web using Serper API."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return {"content": None, "error": "SERPER_API_KEY is missing from .env"}
    
    url = "https://google.serper.dev/search"
    payload = {"q": query}
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        results = response.json().get("organic", [])
        
        formatted_results = []
        for r in results[:5]:  # Limit to top 5 results
            formatted_results.append(f"Title: {r.get('title')}\nLink: {r.get('link')}\nSnippet: {r.get('snippet')}\n---")
            
        if not formatted_results:
            return {"content": "No results found.", "error": None}
            
        return {"content": "\n".join(formatted_results), "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}

def web_fetch(url: str) -> dict:
    """Fetch and extract text from a webpage using trafilatura."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return {"content": None, "error": "Failed to download the webpage."}
        
        text = trafilatura.extract(downloaded)
        if text is None:
            return {"content": None, "error": "Failed to extract text from the webpage."}
            
        # Truncating to 5000 characters to avoid massive token usage
        return {"content": text[:5000], "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}