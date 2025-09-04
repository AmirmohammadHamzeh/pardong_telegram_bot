import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from textwrap import dedent

API_USER_DATA_URL = "/auth/get_user_data/"
from make_request import api_request


def get_user_data(token: str) -> dict:
    # Deprecated: kept for compatibility; should be replaced by async usage of api_request
    return None


async def get_user_information(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    result = await api_request("GET", API_USER_DATA_URL, params={"user_id": user_id})
    if result is None:
        await update.message.reply_text("❌ ارتباط با سرور برقرار نشد.")
        return ConversationHandler.END

    status_code, response = result

    if status_code == 200:
        response_data = response["data"]
        user_information = f"""
         
          👤نام کاربری :{response_data["username"]}
📱شماره تلفن :{response_data["phone_number"]}
         
                            """
        await update.message.reply_text(dedent(user_information))
    else:
        return ConversationHandler.END
