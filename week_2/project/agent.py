import os
import json
import requests
import trafilatura
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path


from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

# 3. Define the AI's "Hands" (The Tools)
def web_search(query: str) -> str:
    """Searches the web using Serper.dev"""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': os.environ.get("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error searching the web: {str(e)}"

def web_fetch(url: str) -> str:
    """Fetches and extracts clean text from a webpage."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return "Error: Could not fetch webpage."
        result = trafilatura.extract(downloaded)
        return result if result else "Error: Could not extract text."
    except Exception as e:
        return f"Error reading the webpage: {str(e)}"


tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Searches Google for up-to-date information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The Google search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetches the full text content of a specific URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to read"}
                },
                "required": ["url"]
            }
        }
    }
]


def run_agent(user_message: str):
    messages = [
        {"role": "system", "content": "You are a research AI. Use web_search to find information, and web_fetch to read the links. Always cite your sources."},
        {"role": "user", "content": user_message}
    ]
    
    for _ in range(5): 
        response = client.chat.completions.create(
            model="openrouter/free", # You can change this if you bought a better model
            messages=messages,
            tools=tools
        )
        
        message = response.choices[0].message
        messages.append(message) 
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                print(f"\n[SYSTEM] AI is using tool: {tool_call.function.name} with args: {args}")
                
                if tool_call.function.name == "web_search":
                    result = web_search(args["query"])
                elif tool_call.function.name == "web_fetch":
                    result = web_fetch(args["url"])
                else:
                    result = "Error: Unknown tool"
                    
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            return message.content
            
    return "Error: Agent stopped after 5 iterations to save tokens."

if __name__ == "__main__":
    print("Research Agent Started! Ask a question about current events:")
    q = input("\n[YOU] ")
    print(f"\n[FINAL ANSWER] {run_agent(q)}")