import redis
from config import REDIS_HOST, REDIS_PORT


class RedisManager:
    def __init__(self, db: int):
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=db,
            decode_responses=True
        )

    def create_dict(self, dict_id: str) -> bool:
        try:
            self.client.delete(dict_id)
            return True
        except Exception as e:
            print(f"[Error] در ساخت دیکشنری برای {dict_id}: {e}")
            return False

    def add_to_dict(self, dict_id: str, key: str, value: str) -> bool:
        try:
            result = self.client.hset(dict_id, key, value)
            if result in (0, 1):
                return True
            else:
                print(f"[Warning] نتیجه غیرمنتظره در افزودن مقدار: {result}")
                return False
        except Exception as e:
            print(f"[Error] در افزودن مقدار به دیکشنری {dict_id}: {e}")
            return False

    def get_dict(self, dict_id: str) -> dict:
        try:
            data = self.client.hgetall(dict_id)
            if data:
                return data
            else:
                print(f"[Info] داده‌ای برای {dict_id} یافت نشد.")
                return {}
        except Exception as e:
            print(f"[Error] در خواندن دیکشنری {dict_id}: {e}")
            return {}


