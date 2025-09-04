import requests
from telegram import Update
from telegram.ext import (
    CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackContext
)
from cancel_conversation import cancel
from config import API_BASE_URL, DB_NUM_CACHE_GROUP_ID
from make_request import api_request
from to_english_digits import to_english_digits
from validation_input import validate_english_username, validate_numeric_input
from cache_data import RedisManager
from textwrap import dedent

API_REGISTER_USER = "/auth/register/"
API_USER_INFO = "/auth/check-registration/"
START, USERNAME_REGISTER_USER, PHONE_REGISTER_USER, CARD_REGISTER_USER = range(4)  # 👈 مرحله جدید اضافه شد
cache_group_id = RedisManager(db=DB_NUM_CACHE_GROUP_ID)


async def start_register_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    result = await api_request("GET", API_USER_INFO, params={"user_id": user_id})
    if result is None:
        await update.message.reply_text("❌ ارتباط با سرور برقرار نشد.")
        return ConversationHandler.END

    status_code, response = result

    if status_code == 202:
        await update.message.reply_text(dedent("""
        شما قبلا ثبت نام کردید!
        از ربات میتونی استفاده کنی
        """))
        return ConversationHandler.END

    elif status_code == 200:
        context.user_data["user_id"] = user_id
        await update.message.reply_text(dedent("""
        سلام به ربات پردونگ خوش اومدی 👋
        برای ثبت یک نام کاربری وارد کن 
        """))
        return USERNAME_REGISTER_USER

    await update.message.reply_text("❌ خطای ناشناخته در ارتباط با سرور.")
    return ConversationHandler.END


@validate_english_username(USERNAME_REGISTER_USER)
async def get_username_register_user(update: Update, context: CallbackContext):
    context.user_data["username"] = update.message.text
    await update.message.reply_text("""
    ✅ نام کاربری دریافت شد
    لطفاً شماره تلفنت رو وارد کن:
    """)
    return PHONE_REGISTER_USER


@validate_numeric_input(PHONE_REGISTER_USER)
async def get_phone_register_user(update: Update, context: CallbackContext):
    phone_number = to_english_digits(update.message.text.strip())

    if not phone_number.isdigit() or len(phone_number) != 11:
        await update.message.reply_text("❌ شماره تلفن نامعتبر است! لطفاً شماره ۱۱ رقمی معتبر وارد کنید:")
        return PHONE_REGISTER_USER

    context.user_data["phone_number"] = phone_number

    await update.message.reply_text("""
    ✅ شماره تلفن دریافت شد
    حالا شماره کارت بانکیت رو وارد کن (۱۶ رقم):
    """)
    return CARD_REGISTER_USER


@validate_numeric_input(CARD_REGISTER_USER)
async def get_card_register_user(update: Update, context: CallbackContext):
    card_number = to_english_digits(update.message.text.strip())

    if not card_number.isdigit() or len(card_number) != 16:
        await update.message.reply_text("❌ شماره کارت نامعتبر است! لطفاً شماره کارت ۱۶ رقمی معتبر وارد کنید:")
        return CARD_REGISTER_USER

    context.user_data["card_number"] = card_number

    data = {
        "user_id": context.user_data["user_id"],
        "username": context.user_data["username"],
        "phone_number": context.user_data["phone_number"],
        "bank_card_number": context.user_data["card_number"]
    }

    result = await api_request("POST", API_REGISTER_USER, data=data)
    if result is None:
        await update.message.reply_text("❌ ارتباط با سرور برقرار نشد.")
        return ConversationHandler.END
    status_code, response = result

    if status_code == 201:
        create_cache_group_id = cache_group_id.create_dict(context.user_data["user_id"])
        if create_cache_group_id:
            await update.message.reply_text(dedent("""
                🎉 ثبت نام شما با موفقیت انجام شد
                حالا میتونی از ربات استفاده کنید
                برای هر کار یک کامند هست که کار مورد نظرت رو انجام بدی!
            """))
        else:
            await update.message.reply_text("خطا در ساخت دیکشنری ردیس")
    else:
        await update.message.reply_text(str(response.json()))

    return ConversationHandler.END


def register_user_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_register_user)],
        states={
            USERNAME_REGISTER_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username_register_user)],
            PHONE_REGISTER_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_register_user)],
            CARD_REGISTER_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_card_register_user)],
            # 👈 مرحله جدید
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
