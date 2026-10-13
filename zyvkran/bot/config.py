import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
    OWNER_ID = int(os.getenv("OWNER_ID", 0)) if os.getenv("OWNER_ID") else None

    # OAuth2 Configuration
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8080/callback")

    # Default values for bot settings
    DEFAULT_PREFIX = "/"
    BOT_COLOR = 0x2F3136  # Dark grey

    # --- New Configurations ---
    # Channels
    NO_MESSAGE_CHANNEL_ID = int(os.getenv("NO_MESSAGE_CHANNEL_ID", 0))
    LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
    FEEDBACK_CHANNEL_ID = int(os.getenv("FEEDBACK_CHANNEL_ID", 0))

    # Anti-spam
    MESSAGE_COOLDOWN = 2
    COMMAND_COOLDOWN = 3
    MAX_MESSAGES = 5
    TIME_WINDOW = 10
    SPAM_TIMEOUT_SECONDS = 60

    # Tickets
    MAX_OPEN_TICKETS_PER_USER = 1
    TICKET_COOLDOWN = 30

