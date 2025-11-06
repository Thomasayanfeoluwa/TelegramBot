from dotenv import load_dotenv
import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from groq import Groq   
import re

# --- load env ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# sanity checks (optional)
if not GROQ_API_KEY or not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Missing GROQ_API_KEY or TELEGRAM_BOT_TOKEN in .env")

# ✅ Groq API client
client = Groq(api_key=GROQ_API_KEY)

# --- small helper class to keep last assistant response ---
class Reference:
    def __init__(self):
        self.response = ""

reference = Reference()
model_name = "llama-3.3-70b-versatile"

# --- bot setup ---
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dispatcher = Dispatcher(bot)

def clean_text(text):
    return re.sub(r'[^a-zA-Z0-9\s]', '', text)

def clear_past():
    reference.response = ""

# Handlers
@dispatcher.message_handler(commands=['clear'])
async def clear_memory(message: types.Message):
    clear_past()
    await message.reply("🧠 Memory cleared. How can I assist you now?")

@dispatcher.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    start_command = (
        "👋 Welcome! I’m your AI-powered Telegram assistant.\n\n"
        "I can answer questions, write code, explain topics, generate content, and assist with projects.\n\n"
        "Type /help to see available commands.\n\n"
        "🛠️ Powered by AIogram + Groq AI\n👨‍💻 Developed by Thomas"
    )
    await message.reply(start_command)

@dispatcher.message_handler(commands=['help'])
async def help_handler(message: types.Message):
    help_command = (
        "🤖 Bot Help Menu\n\n"
        "Available Commands:\n"
        "/start - Restart the bot and show the welcome message\n"
        "/help  - Display this help menu\n"
        "/about - Information about the bot and creator\n"
        "/clear - Reset previous conversation memory\n\n"
        "Just type a normal message and I will respond."
    )
    await message.reply(help_command)

@dispatcher.message_handler(commands=['about'])
async def about_handler(message: types.Message):
    about_command = (
        "ℹ️ About This Bot\n\n"
        "This Telegram bot uses an AI language model to provide intelligent, real-time responses.\n\n"
        "Developer: Thomas Adegoke\nTech Stack: Python, Aiogram, Groq API\nVersion: v1.1"
    )
    await message.reply(about_command)

@dispatcher.message_handler()
async def chatgpt_handler(message: types.Message):
    user_text = message.text or ""
    print(f">>> USER: {user_text}")
    user_input = clean_text(message.text)

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "assistant", "content": reference.response},
                {"role": "user", "content": user_input}
            ],
            max_tokens=500,
            temperature=0.7
        )
        reply_text = response.choices[0].message.content.strip()
        reference.response = reply_text
        print(f">>> AI: {reply_text}")
        await message.reply(reply_text, parse_mode="HTML")

    except Exception as e:
        logging.exception("Groq API error: %s", e)
        await message.reply("⚠️ Error contacting AI API. Please try again later.")
        await message.reply(reply_text, parse_mode="MarkdownV2")


if __name__ == "__main__":
    executor.start_polling(dispatcher, skip_updates=True)
