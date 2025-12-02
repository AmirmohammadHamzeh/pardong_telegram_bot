from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext
import re


def validate_english_username(fallback_stage):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: CallbackContext):
            username = update.message.text.strip()
            if re.fullmatch(r"[A-Za-z]+", username):
                return await func(update, context)
            else:
                await update.message.reply_text(
                    "❌ ورودی فقط باید شامل حروف انگلیسی باشه (بدون عدد یا علامت). لطفاً دوباره وارد کن:"
                )
                return fallback_stage

        return wrapper

    return decorator


def validate_numeric_input(fallback_stage):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: CallbackContext):
            text = update.message.text.strip()
            if text.isdigit():
                return await func(update, context)
            else:
                await update.message.reply_text(
                    "❌ ورودی فقط باید شامل ارقام باشه. لطفاً یک عدد وارد کن:")
                return fallback_stage

        return wrapper

    return decorator


def validate_persian_text(fallback_stage):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: CallbackContext):
            text = update.message.text.strip()
            if re.fullmatch(r"[آ-ی\s]+", text):
                return await func(update, context)
            else:
                await update.message.reply_text(
                    "❌ ورودی فقط باید شامل حروف فارسی باشد. لطفاً دوباره وارد کنید:"
                )
                return fallback_stage

        return wrapper

    return decorator


def validate_english_alphanumeric(fallback_stage):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: CallbackContext):
            text = update.message.text.strip()
            if re.fullmatch(r"[A-Za-z0-9]+", text):
                return await func(update, context)
            else:
                await update.message.reply_text(
                    "❌ ورودی فقط باید شامل حروف انگلیسی و ارقام باشد (بدون فاصله یا علامت خاص). لطفاً دوباره وارد کنید:"
                )
                return fallback_stage

        return wrapper

    return decorator
