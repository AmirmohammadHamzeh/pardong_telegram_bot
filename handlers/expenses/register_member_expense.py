from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters,
)
from config import DB_NUM_CACHE_GROUP_ID, DB_NUM_CACHE_EXPENSE_ID
from handlers.cancel_conversation import cancel
from services.cache_data import RedisManager
from services.make_request import api_request

GROUP_ID, SELECT_MEMBER, AMOUNT, EXPENSE_ID = range(4)
API_GET_GROUP_INFO = "/group/get_group/"
API_REGISTER_URL = "/expense/add_participants/"
cache_expense_id = RedisManager(db=DB_NUM_CACHE_EXPENSE_ID)
cache_group_id = RedisManager(db=DB_NUM_CACHE_GROUP_ID)


async def start_add_member_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    get_cached_data = cache_group_id.get_dict(user_id)
    keyboard = [
        [InlineKeyboardButton(text=key, callback_data=value)]
        for key, value in get_cached_data.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text("گروهی که میخوای توش دونگ ثبت کنی انتخاب کن: ", reply_markup=reply_markup)
    return GROUP_ID


async def get_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    result = await api_request("GET", f"{API_GET_GROUP_INFO}{group_id}")
    if result is None:
        await update.effective_message.reply_text("❌ ارتباط با سرور برقرار نشد.")
        return ConversationHandler.END

    status_code, response = result

    if status_code == 200:
        members = response["data"]["members"]
        if not members:
            await query.message.reply_text("⚠️ هیچ عضوی توی این گروه نیست. که بخوای براش دونگ ثبت کنی")
            return ConversationHandler.END

        keyboard = [
            [InlineKeyboardButton(m["username"], callback_data=m["username"])]
            for m in members if m["username"]
        ]
        context.user_data["members"] = {
            m["username"]: {"user_id": m["user_id"], "username": m["username"]}
            for m in members if m["username"]
        }

        await query.message.reply_text(f"""
        {button_text}
        👥 برای کی میخوای دونگ ثبت کنی؟
        """,
                                       reply_markup=InlineKeyboardMarkup(keyboard)
                                       )
        return SELECT_MEMBER

    else:
        await query.message.reply_text("❌ خطا در دریافت اعضای گروه.")
        return ConversationHandler.END


async def member_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    username = query.data
    member_info = context.user_data["members"].get(username)
    if not member_info:
        await query.message.reply_text("❌ عضو یافت نشد.")
        return ConversationHandler.END

    context.user_data["selected_member"] = member_info
    await query.message.edit_text(f"✅ عضو {username} انتخاب شد. حالا لطفاً مبلغ دونگ رو وارد کن:")
    return AMOUNT


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = update.message.text.strip()
    if not amount.isdigit():
        await update.effective_message.reply_text("❌ورودی نامعتبر لطفا مبلغ دونگ رو به صورت عددی وارد کن")
        return AMOUNT
    context.user_data["amount"] = amount
    get_cached_data = cache_expense_id.get_dict(context.user_data["group_id"])
    keyboard = [
        [InlineKeyboardButton(text=key, callback_data=value)]
        for key, value in get_cached_data.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text("برای کدوم خرید میخوای دونگ ثبت کنی؟", reply_markup=reply_markup)
    return EXPENSE_ID


async def get_expense_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    expense_id = query.data
    context.user_data["expense_id"] = expense_id

    selected = context.user_data["selected_member"]

    data = {
        "user_id": selected["user_id"],
        "username": selected["username"],
        "share": context.user_data["amount"],
    }
    result = await api_request("PATCH", f"{API_REGISTER_URL}{expense_id}",data=data)
    if result is None:
        await update.effective_message.reply_text("❌ ارتباط با سرور برقرار نشد.")
        return ConversationHandler.END

    status_code, response = result
    description_of_expense = response["data"]["description"]
    if status_code == 200:
        await update.effective_message.reply_text("✅ دونگ با موفقیت ثبت شد.")
        try:
            await context.bot.send_message(
                chat_id=selected["user_id"],
                text=f"🧾 دونگ شما به مبلغ {data['share']} تومان در خرید {description_of_expense} ثبت شد.",
            )
        except Exception as e:
            print(f"❌ ارسال پیام به کاربر ناموفق بود: {e}")
    else:
        await update.effective_message.reply_text("❌ خطا در ثبت دنگ.")

    return ConversationHandler.END


def get_add_member_expense_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("add_member_expense", start_add_member_expense)],
        states={
            GROUP_ID: [CallbackQueryHandler(get_group_id)],  # ← تغییر اینجا
            SELECT_MEMBER: [CallbackQueryHandler(member_selected)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            EXPENSE_ID: [CallbackQueryHandler(get_expense_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
