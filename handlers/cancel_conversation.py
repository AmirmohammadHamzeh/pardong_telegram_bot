from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("لغو شد حالا میتونی گزینه ی جدیدی رو انتخاب کنی")
    context.user_data.pop('state', None)
    context.user_data.pop('a', None)
    return ConversationHandler.END
