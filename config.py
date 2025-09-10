import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = "http://127.0.0.1:8000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
DB_NUM_CACHE_GROUP_ID = 1
DB_NUM_CACHE_EXPENSE_ID = 2