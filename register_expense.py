import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
)

from cancel_conversation import cancel
from get_user_token import get_user_token
from config import API_BASE_URL, DB_NUM_CACHE_EXPENSE_ID, DB_NUM_CACHE_GROUP_ID
from get_user_data import get_user_data
from auth_user import require_login
from cache_data import RedisManager
from to_english_digits import to_english_digits

API_GET_GROUP_INFO = f"{API_BASE_URL}/group/get_group"
API_REGISTER_EXPENSE_URL = f"{API_BASE_URL}/expense/add_expense"
GROUP_NAME_REGISTER_EXPENSE, DESCRIPTION_REGISTER_EXPENSE, AMOUNT_REGISTER_EXPENSE = range(3)
cache_expense_id = RedisManager(db=DB_NUM_CACHE_EXPENSE_ID)
cache_group_id = RedisManager(db=DB_NUM_CACHE_GROUP_ID)


@require_login
async def start_register_expense(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    context.user_data["user_id"] = user_id
    get_cached_data = cache_group_id.get_dict(user_id)
    keyboard = [
        [InlineKeyboardButton(text=key, callback_data=value)]
        for key, value in get_cached_data.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text("برای گروهی که میخوای\n "
                                              "هزینه ثبت کنی رو انتخاب کن", reply_markup=reply_markup)
    return GROUP_NAME_REGISTER_EXPENSE


async def get_groupid_register_expense(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    button_text = None
    for row in query.message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data == query.data:
                button_text = button.text
                break
    await query.message.delete()
    group_id = query.data
    context.user_data["group_id"] = group_id
    token = await get_user_token(context.user_data["user_id"])
    if not token:
        await update.effective_message.reply_text("❌ خطا در دریافت توکن. لطفاً دوباره لاگین کنید.")
        return ConversationHandler.END

    url = f"{API_GET_GROUP_INFO}/{group_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            await update.effective_message.reply_text("✅ گروه تأیید شد.\nلطفاً توضیحی درمورد خرید وارد کن:")
            return DESCRIPTION_REGISTER_EXPENSE
        elif response.status_code == 404:
            await update.effective_message.reply_text("❌ گروهی با این شناسه پیدا نشد. لطفاً دوباره شناسه گروه رو وارد "
                                                      "کنید:")
            return GROUP_NAME_REGISTER_EXPENSE
        else:
            await update.effective_message.reply_text("⚠️ خطا در ارتباط با سرور. لطفاً بعداً تلاش کنید.")
            return ConversationHandler.END
    except Exception as e:
        await update.effective_message.reply_text(f"⛔️ خطا در ارتباط:\n{e}")
        return ConversationHandler.END


async def get_description_register_expense(update: Update, context: CallbackContext):
    context.user_data["description"] = update.message.text
    await update.effective_message.reply_text("لطفاً مبلغ خرید رو یه تومن وارد کن")
    return AMOUNT_REGISTER_EXPENSE


async def get_amount_register_expense(update: Update, context: CallbackContext):
    amount_text = update.message.text

    # بررسی معتبر بودن مبلغ
    if not amount_text.isdigit():
        await update.effective_message.reply_text("❌ مبلغ نامعتبر است! لطفاً یک عدد معتبر وارد کن:")
        return AMOUNT_REGISTER_EXPENSE

    context.user_data["amount"] = int(to_english_digits(amount_text))
    user_id = context.user_data["user_id"]
    token = context.user_data["token"]

    user_data = get_user_data(token)
    if not user_data:
        await update.effective_message.reply_text("❌ خطا در دریافت اطلاعات کاربر.")
        return ConversationHandler.END

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "group_id": context.user_data["group_id"],
        "creator_id": user_id,
        "amount": context.user_data["amount"],
        "description": context.user_data["description"],
        "status": "pending",
        "participants": ["string"]
    }

    response = requests.post(
        f"{API_REGISTER_EXPENSE_URL}/{context.user_data['group_id']}",
        json=data,
        headers=headers
    )

    if response.status_code == 201:
        if cache_expense_id.create_dict(context.user_data["group_id"]):
            expense = response.json()
            if cache_expense_id.add_to_dict(
                    context.user_data["group_id"],
                    context.user_data["description"],
                    expense["data"]["expense_id"]
            ):
                await update.effective_message.reply_text(
                    f"✅ خرید با موفقیت ثبت شد.\n📌 شناسه خرید:\n<code>{expense['data']['expense_id']}</code>\nبرای "
                    f"کپی کردن روی شناسه کلیک کنید",
                    parse_mode="HTML"
                )
            else:
                await update.effective_message.reply_text("خطا در ذخیره شناسه خرید در کش.")
        else:
            await update.effective_message.reply_text("خطا در ساخت دیکشنری کش.")
    else:
        await update.effective_message.reply_text(f"❌ خطا در ثبت گروه: {response.json().get('detail', 'نامشخص')}")

    return ConversationHandler.END


def register_expense_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("register_expense", start_register_expense)
        ],
        states={
            GROUP_NAME_REGISTER_EXPENSE: [
                CallbackQueryHandler(get_groupid_register_expense)
            ],
            DESCRIPTION_REGISTER_EXPENSE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_description_register_expense)
            ],
            AMOUNT_REGISTER_EXPENSE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount_register_expense)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
