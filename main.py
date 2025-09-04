from config import TOKEN
from expenses import expenses_handler
from register_expense import register_expense_handler
from register_group import register_group_handler
from register_user import register_user_handler
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from get_user_data import get_user_information
from register_member_group import get_add_member_group_handler
from register_member_expense import get_add_member_expense_handler
from get_unpaid_expense import unpaid_expense_handler, handle_payment_review
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("user_info", get_user_information))
    app.add_handler(CallbackQueryHandler(handle_payment_review, pattern=r"^(approve_payment|reject_payment):"))
    app.add_handler(unpaid_expense_handler())
    app.add_handler(register_expense_handler())
    app.add_handler(register_user_handler())
    app.add_handler(register_group_handler())
    app.add_handler(get_add_member_group_handler())
    app.add_handler(get_add_member_expense_handler())
    app.add_handler(expenses_handler)
    print("🤖 ربات در حال اجراست...")
    app.run_polling()


if __name__ == '__main__':
    main()
