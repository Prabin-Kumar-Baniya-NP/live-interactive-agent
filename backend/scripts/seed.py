import asyncio
import os
import sys

# Add backend directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models import Organization, User  # noqa: E402


async def seed_data():
    print("Starting database seed...")
    async with AsyncSessionLocal() as session:
        try:
            # Check if organization exists
            result = await session.execute(
                select(Organization).where(Organization.name == "Test Organization")
            )
            org = result.scalar_one_or_none()

            if not org:
                print("Creating Test Organization...")
                org = Organization(name="Test Organization")
                session.add(org)
                await session.flush()  # flush to get ID
            else:
                print("Test Organization already exists.")

            # --- Check if Admin exists ---
            result = await session.execute(
                select(User).where(User.email == "admin@test.com")
            )
            admin = result.scalar_one_or_none()

            if not admin:
                print("Creating Admin User...")
                hashed = hash_password("password123")

                admin = User(
                    email="admin@test.com",
                    hashed_password=hashed,
                    full_name="Admin User",
                    role="admin",
                    organization_id=org.id,
                )
                session.add(admin)
                print("Created user: admin@test.com / password123")
            else:
                print("Admin User already exists.")

            # --- Check if Member exists ---
            result = await session.execute(
                select(User).where(User.email == "member@test.com")
            )
            member = result.scalar_one_or_none()

            if not member:
                print("Creating Member User...")
                hashed = hash_password("password123")

                member = User(
                    email="member@test.com",
                    hashed_password=hashed,
                    full_name="Member User",
                    role="member",
                    organization_id=org.id,
                )
                session.add(member)
                print("Created user: member@test.com / password123")
            else:
                print("Member User already exists.")

            await session.commit()
            print("Seeding completed successfully.")

        except Exception as e:
            print(f"Error seeding data: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(seed_data())
