import requests
from telegram import Update
from telegram.ext import (
    CallbackContext, ConversationHandler
)
from get_user_token import get_user_token
from config import API_BASE_URL
from get_user_data import get_user_data
from datetime import datetime
import pytz

API_GET_GROUP_INFO = f"{API_BASE_URL}/group/get_group"
API_REGISTER_EXPENSE_URL = f"{API_BASE_URL}/expense/add_expense"
GROUP_NAME_REGISTER_EXPENSE, DESCRIPTION_REGISTER_EXPENSE, AMOUNT_REGISTER_EXPENSE = range(3)


async def start_register_expense(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    context.user_data["user_id"] = user_id
    token = await get_user_token(user_id)

    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید. ابتدا لاگین کنید.")
        return ConversationHandler.END

    await update.message.reply_text("لطفاً شناسه گروه خود را ارسال کنید.")
    return GROUP_NAME_REGISTER_EXPENSE


async def get_groupid_register_expense(update: Update, context: CallbackContext):
    group_id = update.message.text.strip()
    context.user_data["group_id"] = group_id
    token = await get_user_token(context.user_data["user_id"])
    if not token:
        await update.message.reply_text("❌ خطا در دریافت توکن. لطفاً دوباره لاگین کنید.")
        return ConversationHandler.END

    url = f"{API_GET_GROUP_INFO}/{group_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            await update.message.reply_text("✅ گروه تأیید شد.\nلطفاً توضیحی درمورد خرید وارد کنید:")
            return DESCRIPTION_REGISTER_EXPENSE
        elif response.status_code == 404:
            await update.message.reply_text("❌ گروهی با این شناسه پیدا نشد. لطفاً دوباره شناسه گروه را وارد کنید:")
            return GROUP_NAME_REGISTER_EXPENSE
        else:
            await update.message.reply_text("⚠️ خطا در ارتباط با سرور. لطفاً بعداً تلاش کنید.")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"⛔️ خطا در ارتباط:\n{e}")
        return ConversationHandler.END


async def get_description_register_expense(update: Update, context: CallbackContext):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("لطفاً مبلغ خرید خود وارد کنید")
    return AMOUNT_REGISTER_EXPENSE


async def get_amount_register_expense(update: Update, context: CallbackContext):
    amount = update.message.text

    if not amount.isdigit():
        await update.message.reply_text("❌ شماره تلفن نامعتبر است! لطفاً شماره ۱۱ رقمی معتبر وارد کنید:")
        return AMOUNT_REGISTER_EXPENSE

    context.user_data["amount"] = amount
    user_id = context.user_data["user_id"]
    token = await get_user_token(user_id)
    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید.")
        return ConversationHandler.END

    user_data = get_user_data(token)

    if not user_data:
        await update.message.reply_text("❌ خطا در دریافت اطلاعات کاربر.")
        return ConversationHandler.END

    iran_tz = pytz.timezone("Asia/Tehran")
    current_time_iran = datetime.now(iran_tz)
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "group_id": context.user_data["group_id"],
        "creator_id": user_id,
        "amount": int(context.user_data["amount"]),
        "description": context.user_data["description"],
        "timestamp": str(current_time_iran),
        "status": "pending",
        "participants": [
            "string"
        ]

    }
    response = requests.post(f"{API_REGISTER_EXPENSE_URL}/{context.user_data["group_id"]}", json=data,
                             headers=headers)
    if response.status_code == 201:
        expense = response.json()
        await update.message.reply_text(
            f"✅ خرید با موفقیت ثبت شد.\n📌 شناسه خرید:\n<code>{expense["data"]["expense_id"]}"
            f"</code>\nبرای کپی کردن روی شناسه کلیک کنید",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(f"❌ خطا در ثبت گروه: {response.json().get('detail', 'نامشخص')}")

    return ConversationHandler.END
