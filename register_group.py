import requests
from telegram import Update
from telegram.ext import (
    CallbackContext, ConversationHandler, MessageHandler, CommandHandler, filters
)

from cancel_conversation import cancel
from make_request import api_request
from validation_input import validate_english_username
from config import API_BASE_URL, DB_NUM_CACHE_GROUP_ID
from cache_data import RedisManager

API_REGISTER_URL = "/group/register/"
API_USER_DATA_URL = "/auth/get_user_data/"

GROUPNAME_REGISTER_GROUP = 1
cache_group_id = RedisManager(db=DB_NUM_CACHE_GROUP_ID)


async def start_register_group(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("لطفاً یه اسم برای گروهت انتخاب کن:")
    return GROUPNAME_REGISTER_GROUP


@validate_english_username(GROUPNAME_REGISTER_GROUP)
async def get_groupname_register_group(update: Update, context: CallbackContext) -> int:
    group_name = update.message.text
    user_id = update.message.from_user.id
    result = await api_request("GET", API_USER_DATA_URL, params={"user_id": user_id})
    if result is None:
        await update.message.reply_text("❌ ارتباط با سرور برقرار نشد.")
        return ConversationHandler.END

    status_code, response = result

    data = {
        "group_name": group_name,
        "owner_id": user_id,
        "members": [response["data"]]

    }

    result2 = await api_request("POST", API_REGISTER_URL, data=data)
    status_code2, response2 = result2
    if status_code2 == 201:
        start_cache_group_id = cache_group_id.add_to_dict(user_id, group_name, response2["data"]["group_id"])
        if start_cache_group_id:
            await update.message.reply_text(
                f"✅ گروه با موفقیت ثبت شد.\n📌 شناسه گروه:\n<code>{response2["data"]["group_id"]}</code>\nبرای اینکه کسی بخواد عضو گروه "
                f"بشه، باید دستور /add_group_members رو بزنه و همین شناسه گروه رو بفرسته.",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("❌ خطا در ذخیره اطلاعات در کش.")
    else:
        await update.message.reply_text("❌ خطا در ثبت گروه")

    return ConversationHandler.END


def register_group_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("register_group", start_register_group)],
        states={GROUPNAME_REGISTER_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                          get_groupname_register_group)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
