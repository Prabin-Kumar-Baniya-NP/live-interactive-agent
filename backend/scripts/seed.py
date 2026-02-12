import asyncio
import os
import sys

# Add backend directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models import Agent, Organization, SessionTemplate, User  # noqa: E402
from app.models.enums import (  # noqa: E402
    AgentModality,
    ModalityProfile,
    PanelType,
)


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

            # --- Check if Triage Agent exists ---
            result = await session.execute(
                select(Agent).where(
                    Agent.organization_id == org.id, Agent.name == "Triage Agent"
                )
            )
            triage = result.scalar_one_or_none()

            if not triage:
                print("Creating Triage Agent...")
                triage = Agent(
                    organization_id=org.id,
                    name="Triage Agent",
                    instructions="""
                    You are a helpful triage agent.
                    Your job is to route the user to the right specialist.
                    """,
                    model="gpt-4.1-mini",
                    modality=AgentModality.AUDIO_ONLY,
                    tools=[],
                    panels=[],
                )
                session.add(triage)
                print("Created Triage Agent")
            else:
                print("Triage Agent already exists.")

            # --- Check if Coding Expert exists ---
            result = await session.execute(
                select(Agent).where(
                    Agent.organization_id == org.id, Agent.name == "Coding Expert"
                )
            )
            coder = result.scalar_one_or_none()

            if not coder:
                print("Creating Coding Expert Agent...")
                coder = Agent(
                    organization_id=org.id,
                    name="Coding Expert",
                    instructions="""
                    You are an expert software engineer.
                    Help the user with coding tasks.
                    """,
                    model="gpt-4.1",
                    modality=AgentModality.AUDIO_SCREENSHARE,
                    tools=[],
                    panels=["coding_ide"],
                )
                session.add(coder)
                print("Created Coding Expert Agent")
            else:
                print("Coding Expert Agent already exists.")

            # --- Refresh agents to get IDs ---
            await session.flush()
            # If we just created them or they existed,
            # we need to ensure we have their IDs.
            # If they existed, verify we have the object bound to
            # session or fetch again if cleaner.

            # Re-fetch both to be safe and ensure they are attached
            # to current session transaction
            triage = (
                await session.execute(
                    select(Agent).where(
                        Agent.name == "Triage Agent", Agent.organization_id == org.id
                    )
                )
            ).scalar_one()
            coder = (
                await session.execute(
                    select(Agent).where(
                        Agent.name == "Coding Expert", Agent.organization_id == org.id
                    )
                )
            ).scalar_one()

            # --- Check if Session Template exists ---
            result = await session.execute(
                select(SessionTemplate).where(
                    SessionTemplate.organization_id == org.id,
                    SessionTemplate.name == "Default Coding Interview",
                )
            )
            template = result.scalar_one_or_none()

            if not template:
                print("Creating Default Session Template...")
                template = SessionTemplate(
                    organization_id=org.id,
                    name="Default Coding Interview",
                    description="""
                    Standard coding interview setup with triage and expert agents.
                    """,
                    agent_ids=[triage.id, coder.id],
                    initial_agent_id=triage.id,
                    modality_profile=ModalityProfile.AUDIO_SCREENSHARE,
                    enabled_panels=[PanelType.CODING_IDE.value],
                    max_duration_seconds=3600,
                    idle_timeout_seconds=300,
                )
                session.add(template)
                print("Created Default Session Template")
            else:
                print("Default Session Template already exists.")

            await session.commit()
            print("Seeding completed successfully.")

        except Exception as e:
            print(f"Error seeding data: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(seed_data())
