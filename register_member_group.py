import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackContext, ConversationHandler, ContextTypes
)

from cancel_conversation import cancel
from config import DB_NUM_CACHE_GROUP_ID
from cache_data import RedisManager
from make_request import api_request

API_REGISTER_MEMBER_GROUP_URL = "/group/add_member"
API_USER_DATA_URL = "/auth/get_user_data"
API_GROUP_DATA_URL = "/group/get_group"
GROUP_ID_ADD_MEMBER = 1
cache_group_id = RedisManager(db=DB_NUM_CACHE_GROUP_ID)


async def start_add_member_group(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(f"""
        لطفا شناسه گروهی که میخوایی عضو شوی رو وارد کن:
        """)
    return GROUP_ID_ADD_MEMBER


async def get_groupid_add_member_group(update: Update, context: CallbackContext) -> int:
    group_id = update.message.text
    user_id = update.message.from_user.id
    result = await api_request("GET", f"{API_USER_DATA_URL}/", params={"user_id":user_id})
    if result is None:
        await update.effective_message.reply_text("❌ ارتباط با سرور برقرار نشد.")
        return ConversationHandler.END
    status_code, response = result
    if status_code == 200:
        user_data = response["data"]
        result2 = await api_request("GET", f"{API_GROUP_DATA_URL}/{group_id}")
        if result2 is None:
            await update.effective_message.reply_text("❌ ارتباط با سرور برقرار نشد.")
            return ConversationHandler.END
        status_code2, response2 = result2
        if status_code2 == 404:
            await update.message.reply_text(f"❌ شناسه ی گروهی که فرستادی اشتباهه! لطفا دوباره شناسه صحیح گروه را وارد کنید:")
            return GROUP_ID_ADD_MEMBER  # Return to same state to retry
        elif status_code2 == 200:
            result3 = await api_request("PATCH", f"{API_REGISTER_MEMBER_GROUP_URL}/{group_id}", data=user_data)
            status_code3, response3 = result3
            if result3 is None:
                await update.effective_message.reply_text("❌ ارتباط با سرور برقرار نشد.")
                return ConversationHandler.END
            if status_code3 == 409:
                await update.message.reply_text(f"شما قبلا عضو شدی")
                return ConversationHandler.END
            if status_code3 == 200:
                group_name = response3["data"]["group_name"]
                start_cache_group_id = cache_group_id.add_to_dict(user_data["user_id"], group_name, group_id)
                if start_cache_group_id:
                    await update.message.reply_text(f"✅شما با موفقیت عضو گروه {group_name}شدی ")
                else:
                    await update.message.reply_text("❌ خطا در ذخیره اطلاعات در کش.")
            else:
                await update.message.reply_text("❌ خطا در ربات لطفا به ادمین اطلاع دهید.")
        else:
            await update.message.reply_text("❌ خطا در ربات لطفا به ادمین اطلاع دهید.")
    elif status_code == 404:
        await update.effective_message.reply_text("❌ کاربر پیدا نشد ")
        return ConversationHandler.END
    else:
        await update.effective_message.reply_text("❌ ارتباط با سرور برقرار نشد.")
        return ConversationHandler.END

    return ConversationHandler.END


def get_add_member_group_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("add_group_members", start_add_member_group)],
        states={GROUP_ID_ADD_MEMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_groupid_add_member_group)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
