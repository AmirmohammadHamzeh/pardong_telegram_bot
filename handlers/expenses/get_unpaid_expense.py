from utils.date_converter import iso_to_persian
from handlers.cancel_conversation import cancel
from services.make_request import api_request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
UNPAID_STATE = 1


async def fetch_unpaid_expenses(user_id: int, status_expense: bool = False) -> list:
    result = await api_request(
        "GET",
        "/expense/get_expense_by_status_participants/",
        params={"user_id": user_id, "status_expense": status_expense}
    )
    if result is None:
        print("[fetch_unpaid_expenses] ❌ Request failed")
        return []
    status_code, response = result
    if status_code == 200 and isinstance(response, dict):
        data_container = response.get("data")
        if isinstance(data_container, dict):
            expenses_list = data_container.get("data")
            if isinstance(expenses_list, list):
                return expenses_list
        return []
    return []


async def mark_expense_as_paid(user_id: int, expense_id: str) -> bool:
    result = await api_request(
        "PATCH",
        f"/expense/change_paid_true/{expense_id}",
        params={"user_id": user_id}
    )
    if result is None:
        print("[mark_expense_as_paid] ❌ Request failed")
        return False
    status_code, _ = result
    return status_code == 200 or status_code == 204


async def fetch_user_info(user_id: str) -> dict:
    result = await api_request(
        "GET",
        "/auth/get_user_data/",
        params={"user_id": user_id}
    )
    if result is None:
        print("[fetch_user_info] ❌ Request failed")
        return {}
    status_code, response = result
    if status_code == 200 and isinstance(response, dict):
        return response.get("data", {})
    return {}


async def unpaid_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    expenses = await fetch_unpaid_expenses(user_id, status_expense=False)

    if not expenses:
        await update.message.reply_text("✅ همه هزینه‌های شما پرداخت شده‌اند.")
        return ConversationHandler.END

    context.user_data["unpaid_message_ids"] = []

    for expense in expenses:
        expense_id = expense["expense_id"]
        title = expense.get("description")
        amount = expense.get("amount", 0)
        time = expense.get('timestamp')

        persian_time = iso_to_persian(time) if time else "-"
        text = (
            f"🧾 <b>{title}</b>\n"
            f"💵 مبلغ: {amount}\n"
            f"تاریخ ثبت: {persian_time}\n"
            f"🆔 <code>{expense_id}</code>\n"
        )
        keyboard = [
            [InlineKeyboardButton("💸 پرداخت این هزینه", callback_data=f"confirm_payment:{expense_id}")]
        ]
        sent_message = await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        context.user_data["unpaid_message_ids"].append(sent_message.message_id)

    return UNPAID_STATE


async def confirm_payment_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirm_payment:"):
        expense_id = data.split(":")[1]

        # پیدا کردن هزینه انتخاب شده
        expenses = await fetch_unpaid_expenses(user_id, status_expense=False)
        expense = next((e for e in expenses if e["expense_id"] == expense_id), None)

        if not expense:
            await query.edit_message_text("❌ هزینه پیدا نشد.")
            return ConversationHandler.END

        creator_id = expense["creator_id"]
        user_info = await fetch_user_info(int(creator_id))
        username = user_info.get("username", "نامشخص")
        card_number = user_info.get("bank_card_number", "نامشخص")

        text = (
            f"👤 صاحب گروه: {username}\n"
            f"💳 شماره کارت: {card_number}\n\n"
            f"لطفاً بعد از واریز وجه، عکس رسید پرداخت خود را ارسال کنید 📸"
        )

        await query.edit_message_text(text, parse_mode="HTML")
        context.user_data["waiting_for_receipt"] = {
            "expense_id": expense_id,
            "creator_id": creator_id
        }

    return UNPAID_STATE


async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    receipt_info = context.user_data.get("waiting_for_receipt")
    if not receipt_info:
        await update.message.reply_text("❌ مشکلی پیش آمد. دوباره تلاش کنید.")
        return ConversationHandler.END

    expense_id = receipt_info["expense_id"]
    creator_id = receipt_info["creator_id"]

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_id = file.file_id

    keyboard = [
        [
            InlineKeyboardButton("✅ پرداخت تایید شد",
                                 callback_data=f"approve_payment:{expense_id}:{update.effective_user.id}"),
            InlineKeyboardButton("❌ پرداخت رد شد",
                                 callback_data=f"reject_payment:{expense_id}:{update.effective_user.id}")
        ]
    ]
    user = update.effective_user
    username = f"@{user.username}" if user.username else f"{user.first_name} (ID: {user.id})"

    await context.bot.send_photo(
        chat_id=creator_id,
        photo=file_id,
        caption=f"📥 یک رسید جدید دریافت شد برای هزینه {expense_id}\n\nاز طرف: {username}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ رسید شما ارسال شد و منتظر تایید مدیر هزینه است.")
    return ConversationHandler.END


async def handle_payment_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    action = data[0]  # approve_payment یا reject_payment
    expense_id = data[1]
    payer_id = data[2]

    if action == "approve_payment":
        success = await mark_expense_as_paid(payer_id, expense_id)
        if success:
            await query.edit_message_caption("✅ پرداخت تایید شد.")
            await context.bot.send_message(chat_id=payer_id, text="✅ پرداخت شما توسط مدیر هزینه تایید شد.")
    elif action == "reject_payment":
        await query.edit_message_caption("❌ پرداخت رد شد. لطفاً دوباره رسید معتبر ارسال کنید.")
        await context.bot.send_message(chat_id=payer_id,
                                       text="❌ پرداخت شما توسط مدیر هزینه رد شد. لطفاً دوباره رسید بفرستید.")


def unpaid_expense_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("unpaid", unpaid_start)],
        states={
            UNPAID_STATE: [
                CallbackQueryHandler(confirm_payment_button, pattern=r"^confirm_payment:"),
                MessageHandler(filters.PHOTO, receive_receipt),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
