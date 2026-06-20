# Week 1 Submission: LLM APIs & Conversation State

## 1. Core implementation
* **Security:** I used `python-dotenv` to load my api key. I stored the OpenRouter key inside a `.env` file in the root directory and added `.env` to my `.gitignore` file.
* **The API:** I solved the amnesia problem by maintaining a `messages` list. Every time the user types, I append it as a `"user"` role, send the entire transcript to the API, and append the model's reply as an `"assistant"` role.
* **The Rolling Buffer:** To prevent the `messages` list from growing infinitely and crashing the token budget, I implemented a rolling buffer in my `ChatW` class using the `remove_old_msgs` function. If the conversation exceeds my memory limit of 5 turns, I use `self.messages.pop(1)` to drop the oldest message pair, specifically targeting Index 1 so the system prompt at Index 0 is never deleted.

## 2. Custom implementations by me
Based on the project requirements, I implemented a few extra features to make the code more robust:
* **Dynamic Model Routing:** Instead of hardcoding the `deepseek/deepseek-v4-flash:free` model, I set my default model to `openrouter/free` as deepseek model was more busier. I learned that this acts as an auto-routing tag that automatically finds and uses whatever free model is currently online and available, to prevent my code from breaking if anothr model's server is overloaded.
* **"Folder-Proof" Pathing:** I noticed that depending on whether I ran my script from the root folder or inside `week_1`, `load_dotenv()` would sometimes fail to find the `.env` file. I fixed this by using the `pathlib` library to explicitly map the path: `env_path = Path(__file__).resolve().parent.parent / '.env'`. 
* **Ghost Key Protection:** I added `override=True` to my `load_dotenv()` function. I realized that the Mac terminal can sometimes cache old or broken environment variables, so this forces Python to strictly use the key currently written in the `.env` file.

## 3. Challenges, Failures, and Debugging
I ran into several roadblocks during setup that got me learning a lot about how environments work:
* **Terminal vs. Vault Confusion:** At one point, I accidentally typed my `pip install openai python-dotenv` commands directly inside my `.env` file instead of the terminal. I quickly learned the difference between a secure storage vault (`.env`) and the command execution shell.
* **The 401 Unauthorized Bug:** Even after setting up my key, I kept getting a `401 User not found` error. I eventually debugged it and found two issues: first, I had accidentally duplicated the prefix when pasting my key (`sk-or-v1-sk-or-v1-`), and second, my terminal was holding onto an old cached version of the key. I had to kill the terminal completely, fix the prefix, and use `override=True` to finally get a `200 OK` response.
* **Virtual Environment Pathing:** I struggled heavily with `[Errno 2] No such file or directory` because I was trying to run files while standing in the wrong directory relative to my `.venv`. I ended up pivoting to a global installation to hit my deadline, but I now understand why `.venv` isolation is important for long-term projects.

## 4.What I Learned
The biggest "aha" moment for me was realizing that LLMs literally have zero memory. When you use ChatGPT on the web, it feels like it knows you, but what actually happens us that it's completely stateless. The only way it "remembers" is because we are programmatically handing it a massive, scrolling transcript of the entire conversation every single time we press enter. 
