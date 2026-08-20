import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# App Settings
APP_TITLE = "ChatScope"
APP_ICON = "WA"
LAYOUT = "wide"

# Chat Analysis Settings
CONVERSATION_GAP_MINUTES = 30
TOP_USERS_LIMIT = 10
TOPIC_COUNT = 5

# AI / Gemini Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AI_MAX_MESSAGES_CONTEXT = 500  # Prevent token limit exhaustion
AI_MODEL_NAME = "gemini-2.5-flash" # Use flash for speed, or pro if needed

# NLP Settings
SENTIMENT_THRESHOLD_POS = 0.05
SENTIMENT_THRESHOLD_NEG = -0.05

# Caching Settings
CACHE_TTL = 3600  # 1 hour
