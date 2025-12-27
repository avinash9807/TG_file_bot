import os

# --- SECURE CONFIG ---
# Ab hum values direct yahan nahi likhenge
# Ye values hum Koyeb ki Settings me dalenge

API_ID = int(os.environ.get("API_ID", "0"))

API_HASH = os.environ.get("API_HASH", "")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Owner IDs ko comma se split karke list banayenge
OWNER_IDS = list(map(int, os.environ.get("OWNER_IDS", "0").split(",")))

APP_URL = os.environ.get("APP_URL", "")

