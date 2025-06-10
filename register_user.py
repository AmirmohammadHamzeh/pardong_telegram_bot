import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackContext
)
from config import API_BASE_URL
from to_english_digits import to_english_digits
from validation_input import validate_english_username, validate_numeric_input

API_URL = f"{API_BASE_URL}/auth/register/"
USERNAME_REGISTER_USER, PHONE_REGISTER_USER = range(2)


async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    context.user_data["user_id"] = user_id
    text = """
        سلام خوش اومدی👋
        نام کاربری خود را وارد کن:
    
    """
    await update.message.reply_text(text)
    return USERNAME_REGISTER_USER


@validate_english_username(USERNAME_REGISTER_USER)
async def get_username(update: Update, context: CallbackContext):
    context.user_data["username"] = update.message.text

    await update.message.reply_text("لطفاً شماره تلفن خود را وارد کنید:")
    return PHONE_REGISTER_USER


@validate_numeric_input(PHONE_REGISTER_USER)
async def get_phone(update: Update, context: CallbackContext):
    phone_number = to_english_digits(update.message.text.strip())

    if not phone_number.isdigit() or len(phone_number) != 11:
        await update.message.reply_text("❌ شماره تلفن نامعتبر است! لطفاً شماره ۱۱ رقمی معتبر وارد کنید:")
        return PHONE_REGISTER_USER

    context.user_data["phone_number"] = phone_number

    data = {
        "user_id": context.user_data["user_id"],
        "username": context.user_data["username"],
        "phone_number": context.user_data["phone_number"]
    }

    response = requests.post(API_URL, json=data)

    if response.status_code == 201:
        await update.message.reply_text("ثبت نام شما با موفقیت انجام شد")
    else:
        await update.message.reply_text(response.json())

    return ConversationHandler.END
