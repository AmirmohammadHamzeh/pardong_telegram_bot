import logging
from aiohttp import ClientSession
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from get_user_data import get_user_token

API_BASE_URL = "http://localhost:8000"
# TODO fix this func

UNPAID_STATE = 1


# گرفتن توکن کاربر و ذخیره در context.user_data
async def ensure_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    user_id = update.effective_user.id
    token = await get_user_token(user_id)

    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید. ابتدا لاگین کنید.")
        return None

    context.user_data["token"] = token
    return token


async def get_unpaid_expenses(token: str):
    async with ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(f"{API_BASE_URL}/expense/expense_unpaid/", headers=headers) as resp:
            data = await resp.json()
            return data.get("data", [])


async def mark_as_paid(expense_id: str, token: str):
    async with ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        async with session.patch(f"{API_BASE_URL}/expense/change_paid_true/{expense_id}", headers=headers) as resp:
            return resp.status == 200


# استارت مکالمه با /unpaid
async def unpaid_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = await ensure_token(update, context)
    if not token:
        return ConversationHandler.END

    expenses = await get_unpaid_expenses(token)
    print(expenses)
    if not expenses:
        await update.message.reply_text("✅ همه هزینه‌های شما پرداخت شده‌اند.")
        return ConversationHandler.END
    for expense in expenses:
        expense_id = expense['expense_id']
        title = expense.get("description")
        amount = expense.get('amount', 0)

        keyboard = [
            [InlineKeyboardButton("✅ پرداخت انجام شد", callback_data=f"paid:{expense_id}")]
        ]
        await update.message.reply_text(
            f"🧾 {title}\n💵 مبلغ: {amount}\n🆔 کد هزینه: {expense_id}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    return UNPAID_STATE


async def unpaid_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    token = context.user_data.get("token")

    if not token:
        await query.edit_message_text("❌ شما لاگین نکرده‌اید. ابتدا لاگین کنید.")
        return ConversationHandler.END

    data = query.data
    if data.startswith("paid:"):
        expense_id = data.split(":")[1]
        success = await mark_as_paid(expense_id, token)
        if success:
            await query.edit_message_text("✅ پرداخت با موفقیت ثبت شد.")
        else:
            await query.edit_message_text("❌ خطا در ثبت پرداخت.")

    return ConversationHandler.END
