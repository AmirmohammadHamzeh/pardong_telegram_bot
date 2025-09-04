from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from make_request import api_request
from date_converter import iso_to_persian


def format_expense(expense: dict) -> str:
    try:
        date_str = iso_to_persian(expense["timestamp"])
    except Exception:
        date_str = "تاریخ نامشخص"

    participants_text = ""
    for p in expense.get("participants", []):
        paid_status = "✅" if p.get("paid") else "❌"
        participants_text += f"   - {p.get('username', 'ناشناس')} | سهم: {p.get('share', 0)} | {paid_status}\n"

    return (
        f"📌 {expense.get('description', 'بدون توضیح')}\n"
        f"💰 مبلغ: {expense.get('amount', 0)} تومان\n"
        f"🕒 تاریخ: {date_str}\n"
        f"👥 افراد:\n{participants_text}"
    )


async def expenses_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    paid_result = await api_request(
        "GET",
        "/expense/get_expenses_by_status/",
        params={"user_id": user_id, "status_expense": "paid"}
    )

    pending_result = await api_request(
        "GET",
        "/expense/get_expenses_by_status/",
        params={"user_id": user_id, "status_expense": "pending"}
    )

    if not paid_result:
        await update.message.reply_text("❌ خطا در دریافت خرج‌های پرداخت‌شده از سرور.")
        paid_data = []
    else:
        paid_status, paid_res = paid_result
        if paid_status == 200 and paid_res and paid_res.get("data", {}).get("data"):
            paid_data = paid_res["data"]["data"]
        else:
            paid_data = []

    if not pending_result:
        await update.message.reply_text("❌ خطا در دریافت خرج‌های پرداخت‌نشده از سرور.")
        pending_data = []
    else:
        pending_status, pending_res = pending_result
        if pending_status == 200 and pending_res and pending_res.get("data", {}).get("data"):
            pending_data = pending_res["data"]["data"]
        else:
            pending_data = []

    paid_text = "\n\n".join([format_expense(e) for e in paid_data]) if paid_data else "❌ خرج پرداخت‌شده‌ای پیدا نشد."
    pending_text = "\n\n".join(
        [format_expense(e) for e in pending_data]) if pending_data else "❌ خرج پرداخت‌نشده‌ای پیدا نشد."

    message = f"📊 *لیست خرج‌ها*\n\n✅ پرداخت‌شده‌ها:\n{paid_text}\n\n⌛ پرداخت‌نشده‌ها:\n{pending_text}"

    await update.message.reply_text(message, parse_mode="Markdown")


expenses_handler = CommandHandler("expenses", expenses_command)
