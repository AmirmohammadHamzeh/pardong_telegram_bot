import requests
from telegram import Update
from telegram.ext import (

    CallbackContext, ConversationHandler
)
from get_user_token import get_user_token
from config import API_BASE_URL
from validation_input import validate_english_username

API_GET_GROUP_URL = f"{API_BASE_URL}/group/get_group"
API_USER_DATA_URL = f"{API_BASE_URL}/auth/get_user_data/"
GROUP_NAME_GET_GROUP_MEMBER = 1
GROUP_NAME_GET_GROUP_INFO = 1


# TODO create a func for get groups you are in


async def start_get_group_members(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)

    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید. ابتدا لاگین کنید.")
        return ConversationHandler.END

    await update.message.reply_text("لطفا نام دقیق گروه خود را وارد کنید")
    return GROUP_NAME_GET_GROUP_MEMBER


@validate_english_username(GROUP_NAME_GET_GROUP_MEMBER)
async def get_groupname_get_group_info(update: Update, context: CallbackContext) -> int:
    group_name = update.message.text
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)
    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید.")
        return ConversationHandler.END
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_GET_GROUP_URL}/{group_name}", headers=headers)
    if response.status_code == 200:
        response_data = response.json()["data"]["members"]
        output = ""
        for i, user in enumerate(response_data, start=1):
            output += f"کاربر:{i}\n"
            output += f"نام یوزر:{user['username']}\n"
            output += f"شماره تلفن:{user['phone_number']}\n\n"

        await update.message.reply_text(output)
    else:
        await update.message.reply_text(f"❌ خطا در ثبت عضو: {response.json().get('detail', 'نامشخص')}")

    return ConversationHandler.END


async def start_get_group_info(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)

    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید. ابتدا لاگین کنید.")
        return ConversationHandler.END

    await update.message.reply_text("لطفا نام دقیق گروه خود را وارد کنید")
    return GROUP_NAME_GET_GROUP_INFO


@validate_english_username(GROUP_NAME_GET_GROUP_INFO)
async def get_groupname_get_group_info(update: Update, context: CallbackContext) -> int:
    group_name = update.message.text
    user_id = update.message.from_user.id
    token = await get_user_token(user_id)
    if not token:
        await update.message.reply_text("❌ شما لاگین نکرده‌اید.")
        return ConversationHandler.END
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_GET_GROUP_URL}/{group_name}", headers=headers)
    if response.status_code == 200:
        response_data = response.json()["data"]

        owner_username = next(
            (member['username'] for member in response_data['members']
             if member['user_id'] == response_data['owner_id']),
            'نامشخص'
        )

        output = (
            f"✅ گروه با موفقیت ثبت شد.\n"
            f"📌 شناسه گروه:\n<code>{response_data['group_id']}</code>\n"
            f"برای کپی کردن روی شناسه کلیک کنید\n\n"
            f"📎 نام گروه: {response_data['group_name']}\n"
            f"👤 مالک گروه: {owner_username}\n\n"
            f"👥 اعضای گروه:\n"
        )

        for i, member in enumerate(response_data['members'], start=1):
            output += (
                f"— کاربر {i} —\n"
                f"🔹 نام کاربری: {member['username']}\n"
                f"📞 شماره تماس: {member['phone_number']}\n\n"
            )
        await update.message.reply_text(output, parse_mode="HTML")
    else:
        await update.message.reply_text(f"❌ خطا در ثبت عضو: {response.json().get('detail', 'نامشخص')}")

    return ConversationHandler.END
