import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")

# AI Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
AI_MODEL = "z-ai/glm-4.5-air:free"

# Site Configuration (for OpenRouter headers)
SITE_URL = "https://github.com/TelegramBot"
SITE_NAME = "LangAssistBot"

# Messages
WELCOME_MESSAGE = "سلام خوشگلهه 🥰. خوش اومدی به دستیار تیچر. من بت کمک میکنم تو یادگیری زبان جدیدت خیلی اسون تر و سریع تر باشی . استفاده ازمم خیلی راحته . میخوای بدونی چطوری ؟پس کلیک کن رو این دستور 👈 /help"
