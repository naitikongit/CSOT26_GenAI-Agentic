import requests

def paper_search(query: str, limit: int = 5) -> dict:
    """Search for papers on Hugging Face."""
    url = "https://huggingface.co/api/papers"
    params = {"q": query, "limit": limit}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        papers = response.json()
        
        results = []
        for p in papers:
            results.append(f"Title: {p.get('title')}\nID: {p.get('id')}\nSummary: {p.get('summary')}\n---")
            
        if not results:
            return {"content": "No papers found.", "error": None}
            
        return {"content": "\n".join(results), "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}

def read_paper(arxiv_id: str) -> dict:
    """Read the content or abstract of a paper using its ID."""
    # Assuming HF Papers uses standard arxiv ID formatting for fetch
    url = f"https://huggingface.co/api/papers/{arxiv_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        paper = response.json()
        
        content = f"# {paper.get('title')}\n\n**Authors:** {', '.join([a['name'] for a in paper.get('authors', [])])}\n\n**Abstract:**\n{paper.get('summary')}"
        return {"content": content, "error": None}
    except Exception as e:
        return {"content": None, "error": f"Failed to read paper: {str(e)}"}