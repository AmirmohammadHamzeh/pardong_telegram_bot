import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackContext, ConversationHandler, ContextTypes
)
from get_user_token import get_user_token
from config import API_BASE_URL
from get_user_data import get_user_data
import json

API_GET_GROUP_URL = f"{API_BASE_URL}/group/get_group"
API_REGISTER_URL = f"{API_BASE_URL}/expense/add_participants"
GROUP_NAME_ADD_MEMBER_EXPENSE, SELECT_MEMBER, AMOUNT, EXPENSE_ID = range(4)


async def start_add_members_expense(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)

    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید. ابتدا لاگین کنید.")
        return ConversationHandler.END

    await update.message.reply_text("لطفا شناسه گروه خود را وارد کنید")
    return GROUP_NAME_ADD_MEMBER_EXPENSE


async def get_groupname_add_member_expense(update: Update, context: CallbackContext):
    group_id = update.message.text
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)
    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید.")
        return ConversationHandler.END
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_GET_GROUP_URL}/{group_id}", headers=headers)
    # TODO make output better
    if response.status_code == 200:
        members = response.json()["data"]["members"]
        if not members:
            await update.message.reply_text("⚠️ هیچ عضوی در این گروه یافت نشد.")
            return ConversationHandler.END
        else:
            # ایجاد دیکشنری مورد نظر
            formatted_members = {
                m["username"]: {
                    "user_id": m["user_id"],
                    "username": m["username"]
                }
                for m in members
            }
            context.user_data["members"] = formatted_members

            keyboard = [[InlineKeyboardButton(key, callback_data=key)] for key in formatted_members.keys()]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("👥 لطفاً یکی از اعضا را انتخاب کنید:", reply_markup=reply_markup)

            return SELECT_MEMBER  # انتقال به مرحله بعد

    else:
        await update.message.reply_text(f"❌ خطا در دریافت اعضا: {response.json().get('detail', 'نامشخص')}")
        return ConversationHandler.END


async def member_button_callback_add_member_expense(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    selected_member = query.data

    if "members" in context.user_data and selected_member in context.user_data["members"]:
        member_info = context.user_data["members"][selected_member]
        context.user_data["selected_member_info"] = member_info
        await query.message.edit_text(f"عضو {selected_member} انتخاب شد.\nمبلغ را وارد کنید:")
        return AMOUNT

    else:
        await query.message.reply_text("❌ اطلاعات این کاربر یافت نشد.")

    return ConversationHandler.END


async def get_amount_add_member_expense(update: Update, context: CallbackContext):
    amount = update.message.text
    context.user_data["amount"] = amount
    member_info = context.user_data.get("selected_member_info")
    if member_info:
        await update.message.reply_text(
            f"اطلاعات عضو انتخاب ‌شده:\n"
            f"🆔 user_id: {member_info['user_id']}\n"
            f"👤 username: {member_info['username']}\n💰 مبلغ: {amount}\n"
            "حالا آيدی اکسپنس مورد نظر رو بفرست:"
        )
        return EXPENSE_ID
    else:
        await update.message.reply_text("❌ اطلاعاتی پیدا نشد.")

    return ConversationHandler.END


async def get_member_add_member_expense(update: Update, context: CallbackContext):
    expense_id = update.message.text
    context.user_data["expense_id"] = expense_id
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)

    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید.")
        return ConversationHandler.END

    selected_member_info = context.user_data.get("selected_member_info")
    username_selected_member = selected_member_info["username"]
    user_id_selected_member = selected_member_info["user_id"]
    share = context.user_data.get("amount")

    data = {
        "user_id": user_id_selected_member,
        "username": username_selected_member,
        "share": share,
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.patch(f"{API_REGISTER_URL}/{expense_id}", json=data, headers=headers)

    if response.status_code == 200:
        await update.message.reply_text("دنگ با موفقیت ثبت شد✅")

        try:
            await context.bot.send_message(
                chat_id=user_id_selected_member,
                text=f"🧾 دنگ شما به مبلغ {share} تومان در خرید با شناسه <code>{expense_id}</code> ثبت شد."
                     f"برای کپی کردن روی شناسه کلیک کنید",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"❌ ارسال پیام به کاربر {user_id_selected_member} با خطا مواجه شد: {e}")

    else:
        await update.message.reply_text(
            f"❌ خطا در ثبت عضو: {response.json().get('detail', 'خطای نامشخص')}"
        )

    return ConversationHandler.END
