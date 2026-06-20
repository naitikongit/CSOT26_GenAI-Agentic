import os
import json
import uuid
import argparse
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Import our custom tools
from tools.web import web_search, web_fetch
from tools.papers import paper_search, read_paper
from tools.files import list_files, write_file, read_file, edit_file

load_dotenv()

SESSIONS_DIR = ".agent/sessions"
AGENTS_MD_PATH = "AGENTS.md"

# ---------------------------------------------------------------------------
# Tool Schemas for the LLM
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "web_search", "description": "Search the web for general info.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "web_fetch", "description": "Read a webpage.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "paper_search", "description": "Search arXiv papers via Hugging Face.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 5}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "read_paper", "description": "Read paper abstract/content via arXiv ID.", "parameters": {"type": "object", "properties": {"arxiv_id": {"type": "string"}}, "required": ["arxiv_id"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files in notes directory.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write a new note.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "content": {"type": "string"}}, "required": ["filename", "content"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a note file with pagination.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "start_line": {"type": "integer", "default": 1}, "read_lines": {"type": "integer", "default": 50}}, "required": ["filename"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Edit a file (append, delete, replace).", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "action": {"type": "string", "enum": ["append", "delete", "replace"]}, "line_number": {"type": "integer"}, "text": {"type": "string"}}, "required": ["filename", "action"]}}}
]

# ---------------------------------------------------------------------------
# Core Agent Class
# ---------------------------------------------------------------------------
class Agent:
    def __init__(self, session_id=None):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.model = "gpt-4o-mini" # Fast, smart, and handles tools well
        
        if not os.path.exists(SESSIONS_DIR):
            os.makedirs(SESSIONS_DIR)
            
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.title = "New Research Session"
        self.history = []
        
        if session_id and self._load_session():
            self._emit(f"Loaded session: {self.session_id} - {self.title}")
        else:
            self._init_system_prompt()
            
    def _init_system_prompt(self):
        rules = "You are a helpful research agent."
        if os.path.exists(AGENTS_MD_PATH):
            with open(AGENTS_MD_PATH, "r", encoding="utf-8") as f:
                rules = f.read()
        self.history = [{"role": "system", "content": rules}]
        self._save_session()

    def _save_session(self):
        filepath = os.path.join(SESSIONS_DIR, f"{self.session_id}.json")
        data = {"id": self.session_id, "title": self.title, "updated_at": datetime.now().isoformat(), "history": self.history}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_session(self):
        filepath = os.path.join(SESSIONS_DIR, f"{self.session_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.title = data.get("title", "Untitled")
                self.history = data.get("history", [])
            return True
        return False

    def _emit(self, message: str):
        """Hook for subclasses to override printing behavior."""
        pass

    def _auto_title(self):
        """Bonus Challenge: Generate a 5-word title after first exchange."""
        if len(self.history) == 3 and self.title == "New Research Session":
            title_prompt = [{"role": "user", "content": f"Summarize this query in exactly 5 words: {self.history[1]['content']}"}]
            try:
                response = self.client.chat.completions.create(model=self.model, messages=title_prompt, max_tokens=10)
                self.title = response.choices[0].message.content.strip().replace('"', '')
                self._save_session()
            except Exception:
                pass

    def _execute_tool(self, name: str, args: dict) -> str:
        self._emit(f"🔧 Tool Call: {name}({args})")
        tools = {
            "web_search": web_search, "web_fetch": web_fetch,
            "paper_search": paper_search, "read_paper": read_paper,
            "list_files": list_files, "write_file": write_file,
            "read_file": read_file, "edit_file": edit_file
        }
        if name in tools:
            result = tools[name](**args)
            return result.get("content") or result.get("error")
        return f"Error: Tool {name} not found."

    def chat(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})
        self._auto_title()
        
        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                tools=TOOL_SCHEMAS,
                tool_choice="auto"
            )
            msg = response.choices[0].message
            self.history.append(msg.model_dump(exclude_none=True))
            
            if not msg.tool_calls:
                self._save_session()
                return msg.content
                
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                result_str = self._execute_tool(func_name, args)
                
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": str(result_str)
                })

# ---------------------------------------------------------------------------
# Terminal / REPL Subclass
# ---------------------------------------------------------------------------
class REPLAgent(Agent):
    def _emit(self, message: str):
        print(f"\033[90m{message}\033[0m") # Print logs in grey

    def show_sessions(self):
        """Bonus Challenge: List sessions"""
        files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
        if not files:
            print("No saved sessions.")
            return
        print("\n--- Saved Sessions ---")
        for f in files:
            with open(os.path.join(SESSIONS_DIR, f), "r") as file:
                data = json.load(file)
                print(f"[{data['id']}] {data['title']}")
        print("----------------------\n")

    def run_once(self, query: str):
        print(f"Query: {query}\nThinking...")
        answer = self.chat(query)
        print(f"\nResponse:\n{answer}")

    def run(self):
        print(f"Research Desk REPL (Session: {self.session_id})")
        print("Type 'exit' to quit, '/sessions' to list, '/resume <id>' to load.")
        while True:
            try:
                user_in = input("\nYou> ").strip()
                if user_in.lower() in ['exit', 'quit']:
                    break
                elif user_in == "/sessions":
                    self.show_sessions()
                    continue
                elif user_in.startswith("/resume "):
                    target_id = user_in.split(" ")[1]
                    self.session_id = target_id
                    if self._load_session():
                        print(f"Switched to session {target_id}: {self.title}")
                    else:
                        print("Session not found.")
                        self.session_id = str(uuid.uuid4())[:8] # Revert
                    continue
                if not user_in:
                    continue
                
                print("Thinking...")
                answer = self.chat(user_in)
                print(f"\nAgent> {answer}")
            except KeyboardInterrupt:
                break

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Research Desk Agent")
    parser.add_argument("query", nargs="?", help="One-shot query")
    parser.add_argument("--tui", action="store_true", help="Launch Textual UI")
    args = parser.parse_args()

    if args.tui:
        from tui import TUIApp
        app = TUIApp()
        app.run()
    else:
        agent = REPLAgent()
        if args.query:
            agent.run_once(args.query)
        else:
            agent.run()