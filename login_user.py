import requests
import redis.asyncio as redis
from telegram import Update
from telegram.ext import CallbackContext
from config import API_BASE_URL, REDIS_HOST, REDIS_PORT

API_URL = f"{API_BASE_URL}/auth/login/"
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


async def login(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    try:
        response = requests.get(API_URL, params={"user_id": user_id})

        if response.status_code == 401:
            await update.message.reply_text("❌ شما ثبت‌نام نکرده‌اید!")
            return

        data = response.json()

        token = data["data"]["token"]

        await redis_client.setex(name=f"user:{user_id}:token", time=3600, value=token)

        await update.message.reply_text("✅ لاگین موفق! توکن شما ذخیره شد.")

    except requests.RequestException as e:
        await update.message.reply_text(f"❌ خطا در ارتباط با سرور: {str(e)}")

