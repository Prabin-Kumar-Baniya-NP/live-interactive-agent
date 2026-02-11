import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from redis.asyncio import Redis, from_url

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL")


async def get_redis_client() -> Redis:
    if not REDIS_URL:
        raise ValueError("REDIS_URL must be set")
    return from_url(REDIS_URL, encoding="utf-8", decode_responses=True)


async def get_redis() -> AsyncGenerator[Redis, None]:
    client = await get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()


async def ping() -> bool:
    client = await get_redis_client()
    try:
        await client.ping()
        return True
    except Exception as e:
        print(f"Redis Ping Error: {e}")
        return False
    finally:
        await client.aclose()
