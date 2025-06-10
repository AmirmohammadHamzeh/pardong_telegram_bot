import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from config import API_BASE_URL
from get_user_token import get_user_token

API_USER_DATA_URL = f"{API_BASE_URL}/auth/get_user_data/"


def get_user_data(token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_USER_DATA_URL, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None


async def get_user_information(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)
    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید. ابتدا لاگین کنید.")
        return ConversationHandler.END
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_USER_DATA_URL, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        user_information = f"""
         
         نام شما :  {response_data["data"]["username"]}
شماره تلفن شما :   {response_data["data"]["phone_number"]}
         
                            """
        await update.message.reply_text(user_information)
    else:
        await update.message.reply_text(f"❌ خطا : {response.json().get('detail')}")
        return ConversationHandler.END
