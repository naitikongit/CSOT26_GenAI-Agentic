# Week 3: Research Desk (Finally did it!)

So, this week was a ride. The goal was to give our research agent some memory so it doesn't just forget everything the second I close the terminal. 

## What I actually built
- **Long-term memory:** Added a local storage thing so the agent remembers what we talked about even after I `exit`. It finally feels like an actual assistant now.
- **The "Hands" (Custom Tools):** Tossed out those MCP tools from last week. Built my own `paper_search` tool to hit the Hugging Face Papers API and a `write_file` tool so the agent can actually save its own research notes. 
- **The Brain:** Wrapped everything in a proper `Agent` class. Now I can run the same logic in a terminal REPL, a quick command, or that TUI I messed around with last week.

## How I tested it
Honestly, mostly just praying it didn't crash. But for real:
1. Checked if it could actually find papers on arXiv without failing.
2. Made sure it could save files and *remember* the filenames later.
3. Tested the CLI one-shot mode because I definitely didn't have time to open the full UI every single time.

## Stuff I learned (the hard way)
- **Git problem:** Spent lot time fighting merge conflicts and accidentally trying to push my `.env` key to GitHub. Huge shoutout to `.gitignore` for saving my API credits.
- **Modularity:** Trying to keep the TUI, CLI, and REPL all running the same agent code taught me that keeping the logic separate from the UI is the only way to stay sane.

---