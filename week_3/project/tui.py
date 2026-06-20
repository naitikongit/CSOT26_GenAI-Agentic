from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog
from textual.containers import Vertical
from agent import Agent

class TUIAgent(Agent):
    def __init__(self, log_widget: RichLog):
        super().__init__()
        self.log_widget = log_widget

    def _emit(self, message: str):
        
        self.log_widget.write(f"[italic grey]{message}[/italic grey]")

class TUIApp(App):
    CSS = """
    #chat-log { height: 1fr; border: solid green; margin: 1; }
    #user-input { dock: bottom; margin: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield RichLog(id="chat-log", markup=True, wrap=True)
            yield Input(placeholder="Ask the Research Agent...", id="user-input")
        yield Footer()

    def on_mount(self) -> None:
        self.chat_log = self.query_one("#chat-log", RichLog)
        self.agent = TUIAgent(log_widget=self.chat_log)
        self.chat_log.write("[bold green]Research Desk Initialized.[/bold green]")
        self.chat_log.write(f"Session ID: {self.agent.session_id}")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value
        if not user_text.strip():
            return
            
        event.input.value = ""
        self.chat_log.write(f"\n[bold blue]You:[/bold blue] {user_text}")
        
        import asyncio
        response = await asyncio.to_thread(self.agent.chat, user_text)
        
        self.chat_log.write(f"\n[bold magenta]Agent:[/bold magenta] {response}")

if __name__ == "__main__":
    app = TUIApp()
    app.run()