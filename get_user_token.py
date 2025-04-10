import redis.asyncio as aioredis

redis_client = aioredis.Redis(host="localhost", port=6379, decode_responses=True)


async def get_user_token(user_id: int) -> str:
    return await redis_client.get(f"user:{user_id}:token")
