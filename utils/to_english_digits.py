
def to_english_digits(text: str) -> str:
    farsi_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    translation_table = str.maketrans(farsi_digits, english_digits)
    return text.translate(translation_table)

