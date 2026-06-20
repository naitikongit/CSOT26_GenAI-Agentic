import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
class ChatW:
    def __init__(self, botname, memory=5):
        # FIX: Build the telephone inside the robot!
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
        )
        
        self.botname=botname
        self.memory=memory
        self.messages=[{"role": "system", "content": f"You are a helpful assistant named {self.botname}."}]

    def user_msg(self,msg):
        self.messages.append({"role": "user", "content": msg})
        
    def remove_old_msgs(self):
        while len(self.messages)>self.memory:
            self.messages.pop(1)
    
    def bot_reply(self):
        # FIX: Use self.client to make the call
        reply = self.client.chat.completions.create(
            model="openrouter/free",    
            messages=self.messages,
        )

        ai_ans= reply.choices[0].message.content
        self.messages.append({"role": "assistant", "content": ai_ans})

        return ai_ans
if __name__ == "__main__":
    print("Welcome, I am your chatbot assistant.\n")

    chosen_model = input("Choose a model (press Enter for openrouter/free): ")
    if chosen_model == "":
        chosen_model = "openrouter/free"

    bot = ChatW(botname=chosen_model, memory=5)

    print("\nChat started. Type 'exit' or 'quit' to end the session.\n")
    
    while True:
        user_input= input("[YOU] ")
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        bot.user_msg(user_input)
        bot.remove_old_msgs()
        response= bot.bot_reply()
        print(f"\n[{bot.botname}] {response}\n")
