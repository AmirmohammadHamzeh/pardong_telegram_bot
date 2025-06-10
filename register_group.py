import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackContext, ConversationHandler
)
from validation_input import validate_english_username
from get_user_token import get_user_token
from config import API_BASE_URL
from get_user_data import get_user_data

API_REGISTER_URL = f"{API_BASE_URL}/group/register"
API_USER_DATA_URL = f"{API_BASE_URL}/auth/get_user_data/"
GROUPNAME_REGISTER_GROUP = 1


async def start_register_group(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)

    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید. ابتدا لاگین کنید.")
        return ConversationHandler.END

    await update.message.reply_text("لطفاً نام گروه خود را ارسال کنید.")

    return GROUPNAME_REGISTER_GROUP


@validate_english_username(GROUPNAME_REGISTER_GROUP)
async def get_groupname_register_group(update: Update, context: CallbackContext) -> int:
    group_name = update.message.text
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)

    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید.")
        return ConversationHandler.END

    user_data = get_user_data(token)
    if not user_data:
        await update.message.reply_text("❌ خطا در دریافت اطلاعات کاربر.")
        return ConversationHandler.END

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "group_name": group_name,
        "owner_id": user_id,
        "members": [user_data["data"]]

    }

    response = requests.post(API_REGISTER_URL, json=data, headers=headers)
    print(response)
    if response.status_code == 201:
        group_id = response.json()["data"]["group_id"]
        await update.message.reply_text(
            f"✅ گروه با موفقیت ثبت شد.\n📌 شناسه گروه:\n<code>{group_id}</code>\nبرای کپی کردن روی شناسه کلیک کنید",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(f"❌ خطا در ثبت گروه: {response.json().get('detail', 'نامشخص')}")

    return ConversationHandler.END
