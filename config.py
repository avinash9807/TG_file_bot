import os

# --- SECURE CONFIG ---

API_ID = int(os.environ.get("API_ID", "0"))

API_HASH = os.environ.get("API_HASH", "")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Owner IDs (Jinke paas access hai)
OWNER_IDS = list(map(int, os.environ.get("OWNER_IDS", "0").split(",")))

# Koyeb App URL
APP_URL = os.environ.get("APP_URL", "")

# NEW: Storage Channel ID (Jahan files save hongi)
# Default 0 hai, hum ise Koyeb Environment Variables se lenge
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "0"))

