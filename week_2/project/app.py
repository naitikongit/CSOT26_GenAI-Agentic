import os
import json
import requests
import trafilatura
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog
from textual.binding import Binding
from textual import work


load_dotenv(find_dotenv(), override=True)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)


def web_search(query: str) -> str:
    """Searches Google and returns clean snippets."""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': os.environ.get("SERPER_API_KEY"), 'Content-Type': 'application/json'}
    try:
        res = requests.post(url, headers=headers, data=payload)
        res.raise_for_status()
        data = res.json()
        # Filter out the garbage JSON so the free AI can read it easily
        snippets = [item.get("snippet", "") for item in data.get("organic", [])[:3]]
        if "answerBox" in data:
            snippets.insert(0, data["answerBox"].get("snippet", data["answerBox"].get("answer", "")))
        return "\n".join(snippets) if snippets else "No results found."
    except Exception as e:
        return f"Error: {str(e)}"

def web_fetch(url: str) -> str:
    """Reads a webpage."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded: return "Error fetching webpage."
        ext = trafilatura.extract(downloaded)
        return ext[:2000] if ext else "Error extracting text." # Truncate to save tokens
    except Exception as e:
        return f"Error: {str(e)}"

def discover_papers(query: str) -> str:
    """AlphaXiv MCP: Searches for academic papers."""
    return f"AlphaXiv Paper Search Results for '{query}': 'Recent Advancements in {query}' (ID: ax-101)."

def get_paper_content(paper_id: str) -> str:
    """AlphaXiv MCP: Reads the full content of a paper."""
    return f"Content of paper {paper_id}: This paper concludes that the subject is highly complex and requires further study."

tools = [
    {"type": "function", "function": {"name": "web_search", "description": "Searches Google.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "web_fetch", "description": "Reads a webpage.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "discover_papers", "description": "Searches AlphaXiv for academic papers.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "get_paper_content", "description": "Reads an AlphaXiv paper.", "parameters": {"type": "object", "properties": {"paper_id": {"type": "string"}}, "required": ["paper_id"]}}}
]


class PerplexityApp(App):
    CSS = """
    Input { dock: bottom; margin: 1 0; }
    RichLog { height: 1fr; border: solid green; padding: 1; }
    """
    
    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear Log"),
        Binding("ctrl+k", "clear_history", "Clear History (Reset)"),
        Binding("ctrl+q", "quit", "Quit App")
    ]

    def __init__(self):
        super().__init__()
        self.chat_history = [{"role": "system", "content": "You are a terminal-based Perplexity AI. Use your tools to search the web and academic papers. Give concise answers with citations."}]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="chat_log", wrap=True)
        yield Input(placeholder="Ask your research question...", id="user_input")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Input).focus()
        self.query_one(RichLog).write("[bold green]Welcome to Terminal Perplexity! Ask a question to begin.[/]")

    def action_clear_display(self) -> None:
        self.query_one(RichLog).clear()
        self.query_one(RichLog).write("[italic dim]Display cleared.[/]")

    def action_clear_history(self) -> None:
        self.chat_history = [self.chat_history[0]]
        self.query_one(RichLog).clear()
        self.query_one(RichLog).write("[bold yellow]Memory wiped. Fresh start![/]")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_msg = event.value
        if not user_msg: return
        
        event.input.value = ""
        log = self.query_one(RichLog)
        log.write(f"\n[bold blue]You:[/] {user_msg}")
        
        self.chat_history.append({"role": "user", "content": user_msg})
        self.run_agent_loop()

    @work(exclusive=True, thread=True)
    def run_agent_loop(self) -> None:
        log = self.app.query_one(RichLog)
        
        for _ in range(5):
            try:
                response = client.chat.completions.create(
                    model="openrouter/free",
                    messages=self.chat_history,
                    tools=tools
                )
            except Exception as e:
                self.app.call_from_thread(log.write, f"[bold red]API Error: {str(e)}[/]")
                return

            msg = response.choices[0].message
            self.chat_history.append(msg)

            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    func_name = tool_call.function.name
                    self.app.call_from_thread(log.write, f"[dim yellow]System:[/] Using {func_name} tool...")
                    
                    if func_name == "web_search": res = web_search(args.get("query", ""))
                    elif func_name == "web_fetch": res = web_fetch(args.get("url", ""))
                    elif func_name == "discover_papers": res = discover_papers(args.get("query", ""))
                    elif func_name == "get_paper_content": res = get_paper_content(args.get("paper_id", ""))
                    else: res = "Unknown tool."
                        
                    self.chat_history.append({"role": "tool", "tool_call_id": tool_call.id, "content": res})
            else:
                self.app.call_from_thread(log.write, f"\n[bold magenta]Perplexity:[/] {msg.content}")
                return
                
        self.app.call_from_thread(log.write, "\n[bold red]System:[/] Stopped after 5 loops to save tokens.")

if __name__ == "__main__":
    app = PerplexityApp()
    app.run()