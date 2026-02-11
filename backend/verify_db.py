import asyncio

from sqlalchemy import text

from app.db.session import engine


async def main():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"DB Check: {result.scalar()}")
    except Exception as e:
        print(f"DB Check Failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
