from datetime import datetime
import pytz
import jdatetime
from to_english_digits import to_english_digits


def iso_to_persian(iso_datetime: str) -> str:
    dt = datetime.fromisoformat(iso_datetime)
    iran_tz = pytz.timezone("Asia/Tehran")
    dt_iran = dt.astimezone(iran_tz)
    jdate = jdatetime.datetime.fromgregorian(datetime=dt_iran)
    formatted_date = jdate.strftime("%Y/%m/%d - %H:%M")

    return to_english_digits(formatted_date)
