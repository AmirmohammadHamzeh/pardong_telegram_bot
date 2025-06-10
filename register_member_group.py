import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackContext, ConversationHandler, ContextTypes
)
from get_user_token import get_user_token
from config import API_BASE_URL
from get_user_data import get_user_data

API_REGISTER_URL = f"{API_BASE_URL}/group/add_member"
API_USER_DATA_URL = f"{API_BASE_URL}/auth/get_user_data/"
GROUP_ID_ADD_MEMBER = 1


async def start_add_member_group(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)

    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید. ابتدا لاگین کنید.")
        return ConversationHandler.END

    await update.message.reply_text("لطفا شناسه ی گروه را ارسال کنید")
    return GROUP_ID_ADD_MEMBER


async def get_groupid_add_member_group(update: Update, context: CallbackContext) -> int:
    group_id = update.message.text
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
    data = user_data["data"]
    response = requests.patch(f"{API_REGISTER_URL}/{group_id}", json=data, headers=headers)

    if response.status_code == 200:
        await update.message.reply_text(f"✅شما عضو شدی")
    else:
        await update.message.reply_text(f"❌ خطا در ثبت عضو: {response.json().get('detail', 'نامشخص')}")

    return ConversationHandler.END
