import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
)

from cancel_conversation import cancel
from config import DB_NUM_CACHE_EXPENSE_ID, DB_NUM_CACHE_GROUP_ID
from cache_data import RedisManager
from to_english_digits import to_english_digits
from make_request import api_request

API_GET_GROUP_INFO = "/group/get_group/"
API_REGISTER_EXPENSE_URL = "/expense/add_expense"

# استیت‌ها
GROUP_NAME_REGISTER_EXPENSE, DESCRIPTION_REGISTER_EXPENSE, AMOUNT_REGISTER_EXPENSE, SPLIT_METHOD_REGISTER_EXPENSE = range(
    4)

cache_expense_id = RedisManager(db=DB_NUM_CACHE_EXPENSE_ID)
cache_group_id = RedisManager(db=DB_NUM_CACHE_GROUP_ID)


async def start_register_expense(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    context.user_data["user_id"] = user_id
    get_cached_data = cache_group_id.get_dict(user_id)
    keyboard = [
        [InlineKeyboardButton(text=key, callback_data=value)]
        for key, value in get_cached_data.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        "برای گروهی که میخوای\nهزینه ثبت کنی رو انتخاب کن:",
        reply_markup=reply_markup
    )
    return GROUP_NAME_REGISTER_EXPENSE


async def get_groupid_register_expense(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.delete()

    group_id = query.data
    context.user_data["group_id"] = group_id

    result = await api_request("GET", f"{API_GET_GROUP_INFO}{group_id}")
    if result is None:
        await update.effective_message.reply_text("❌ ارتباط با سرور برقرار نشد.")
        return ConversationHandler.END

    status_code, response = result

    if status_code == 200:
        await update.effective_message.reply_text("✅ گروه تأیید شد.\nلطفاً توضیحی درمورد خرید وارد کن:")
        return DESCRIPTION_REGISTER_EXPENSE
    elif status_code == 404:
        await update.effective_message.reply_text("❌ گروهی با این شناسه پیدا نشد. لطفاً دوباره انتخاب کن:")
        return GROUP_NAME_REGISTER_EXPENSE
    else:
        await update.effective_message.reply_text("❌ خطای ناشناخته در ارتباط با سرور.")
        return ConversationHandler.END


async def get_description_register_expense(update: Update, context: CallbackContext):
    context.user_data["description"] = update.message.text
    await update.effective_message.reply_text("لطفاً مبلغ خرید رو به تومان وارد کن:")
    return AMOUNT_REGISTER_EXPENSE


async def get_amount_register_expense(update: Update, context: CallbackContext):
    amount_text = update.message.text

    if not amount_text.isdigit():
        await update.effective_message.reply_text("❌ مبلغ نامعتبر است! لطفاً یک عدد معتبر وارد کن:")
        return AMOUNT_REGISTER_EXPENSE

    context.user_data["amount"] = int(to_english_digits(amount_text))

    keyboard = [
        [
            InlineKeyboardButton("➗ تقسیم بین همه اعضای گروه", callback_data="split_auto"),
            InlineKeyboardButton("✍️ ثبت دستی سهم‌ها", callback_data="split_manual")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text("میخوای هزینه رو چطور تقسیم کنیم؟", reply_markup=reply_markup)

    return SPLIT_METHOD_REGISTER_EXPENSE


async def choose_split_method(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    choice = query.data

    user_id = context.user_data["user_id"]
    group_id = context.user_data["group_id"]

    if choice == "split_manual":
        data = {
            "group_id": group_id,
            "amount": context.user_data["amount"],
            "description": context.user_data["description"],
            "status": "pending",
            "participants": []
        }

        result = await api_request("POST", f"{API_REGISTER_EXPENSE_URL}/{group_id}", params={"user_id": user_id},
                                   data=data)
        if result is None:
            await update.message.reply_text("❌ ارتباط با سرور برقرار نشد.")
            return ConversationHandler.END

        status_code, response = result

        if status_code == 201:
            expense = response["data"]
            if cache_expense_id.create_dict(group_id):
                cache_expense_id.add_to_dict(
                    group_id,
                    context.user_data["description"],
                    expense["expense_id"]
                )
            await query.edit_message_text(
                f"✅ خرید ثبت شد! حالا می‌تونی سهم هر نفر رو با دستور مربوطه وارد کنی.\n"
                f"📌 شناسه خرید:\n<code>{expense['expense_id']}</code>",
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                "❌ خطا در ثبت خرید:"
            )
        return ConversationHandler.END

    elif choice == "split_auto":
        result = await api_request("GET", f"{API_GET_GROUP_INFO}{group_id}")
        if result is None:
            await update.effective_message.reply_text("❌ ارتباط با سرور برقرار نشد.")
            return ConversationHandler.END

        status_code, response = result

        if status_code != 200:
            await update.effective_message.reply_text("❌ خطای ناشناخته در ارتباط با سرور.")
            return ConversationHandler.END

        members = response["data"]["members"]
        other_members = [m for m in members if m.get("user_id") != user_id]

        # اگر هیچ عضو دیگری نیست، فقط خرید رو بدون participants ثبت کن
        if not other_members:
            data = {
                "group_id": group_id,
                "creator_id": user_id,
                "amount": context.user_data["amount"],
                "description": context.user_data["description"],
                "status": "pending",
                "participants": []
            }
            result2 = await api_request("POST", f"{API_REGISTER_EXPENSE_URL}/{group_id}", params={"user_id": user_id},
                                        data=data)
            if result2 is None:
                await update.message.reply_text("❌ ارتباط با سرور برقرار نشد.")
                return ConversationHandler.END

            status_code2, response2 = result2
            if status_code2 == 201:
                expense = response2["data"]
                if cache_expense_id.create_dict(group_id):
                    cache_expense_id.add_to_dict(
                        group_id,
                        context.user_data["description"],
                        expense["expense_id"]
                    )
                await query.edit_message_text(
                    "ℹ️ عضو دیگری در گروه نبود. خرید ثبت شد ولی تقسیم انجام نشد.\n"
                    f"📌 شناسه خرید:\n<code>{expense['expense_id']}</code>",
                    parse_mode="HTML"
                )
            else:
                await query.edit_message_text(
                    f"❌ خطا در ثبت خرید "
                )
            return ConversationHandler.END

        total_amount = context.user_data["amount"]
        n = len(other_members)
        per_person = total_amount // n
        remainder = total_amount % n  # باقیمانده تقسیم

        # ساخت participants با توزیع باقیمانده بین چند نفر اول
        participants = []
        for idx, m in enumerate(other_members):
            share = per_person + (1 if idx < remainder else 0)
            participants.append({
                "user_id": m["user_id"],
                "username": m.get("username", ""),
                "share": share,
                "paid": False
            })

        data = {
            "group_id": group_id,
            "creator_id": user_id,
            "amount": total_amount,
            "description": context.user_data["description"],
            "status": "pending",
            "participants": participants
        }

        result3 = await api_request("POST", f"{API_REGISTER_EXPENSE_URL}/{group_id}", params={"user_id": user_id},
                                    data=data)
        if result3 is None:
            await update.message.reply_text("❌ ارتباط با سرور برقرار نشد.")
            return ConversationHandler.END
        status_code3, response3 = result3

        if status_code3 == 201:
            expense = response3["data"]
            if cache_expense_id.create_dict(group_id):
                cache_expense_id.add_to_dict(
                    group_id,
                    context.user_data["description"],
                    expense["expense_id"]
                )
            await query.edit_message_text(
                f"✅ خرید ثبت شد و بین اعضا (به‌جز شما) تقسیم شد.\n"
                f"📌 شناسه خرید:\n<code>{expense['expense_id']}</code>",
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                f"❌ خطا در ثبت خرید"
            )

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
            SPLIT_METHOD_REGISTER_EXPENSE: [
                CallbackQueryHandler(choose_split_method)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
