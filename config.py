import os

TOKEN = os.environ.get("BOT_TOKEN")
API_BASE_URL = os.environ.get("API_URL")
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
DB_NUM_CACHE_GROUP_ID = 1
DB_NUM_CACHE_EXPENSE_ID = 2
