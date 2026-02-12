from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import NotFoundException
from app.models.agent import Agent
from app.models.agent_version import AgentVersion
from app.schemas.agent import AgentCreate, AgentExport, AgentUpdate


async def validate_handoff_targets(
    db: AsyncSession,
    organization_id: UUID,
    handoff_targets: list[UUID],
    current_agent_id: UUID | None = None,
) -> None:
    if not handoff_targets:
        return

    # Check self-reference
    if current_agent_id and current_agent_id in handoff_targets:
        raise ValueError("Agent cannot hand off to itself")

    # Check existence and organization ownership
    query = select(Agent.id).where(
        Agent.organization_id == organization_id, Agent.id.in_(handoff_targets)
    )
    result = await db.execute(query)
    found_ids = result.scalars().all()

    found_id_set = set(found_ids)
    requested_id_set = set(handoff_targets)

    missing = requested_id_set - found_id_set
    if missing:
        raise ValueError(
            f"""
            Invalid handoff targets: {missing}.
            Agents must exist in the same organization.
            """
        )


async def create_agent(
    db: AsyncSession, organization_id: UUID, data: AgentCreate
) -> Agent:
    if data.handoff_targets:
        await validate_handoff_targets(db, organization_id, data.handoff_targets)

    agent = Agent(
        organization_id=organization_id,
        name=data.name,
        instructions=data.instructions,
        model=data.model,
        voice=data.voice,
        handoff_targets=data.handoff_targets,
        tools=data.tools,
        modality=data.modality,
        panels=[
            p.value for p in data.panels
        ],  # Convert Enum list to string list for DB
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


async def get_agent(db: AsyncSession, agent_id: UUID, organization_id: UUID) -> Agent:
    query = select(Agent).where(
        Agent.id == agent_id,
        Agent.organization_id == organization_id,
        Agent.is_active == True,  # noqa: E712
    )
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundException(f"Agent {agent_id} not found in this organization")
    return agent


async def list_agents(db: AsyncSession, organization_id: UUID) -> list[Agent]:
    query = (
        select(Agent)
        .where(
            Agent.organization_id == organization_id,
            Agent.is_active == True,  # noqa: E712
        )
        .order_by(desc(Agent.created_at))
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_agent(
    db: AsyncSession, agent_id: UUID, organization_id: UUID, data: AgentUpdate
) -> Agent:
    agent = await get_agent(db, agent_id, organization_id)

    if data.handoff_targets is not None:
        await validate_handoff_targets(
            db, organization_id, data.handoff_targets, current_agent_id=agent.id
        )

    # Create snapshot of current state before update
    snapshot = {
        "name": agent.name,
        "instructions": agent.instructions,
        "model": agent.model,
        "voice": agent.voice,
        "handoff_targets": [str(uid) for uid in agent.handoff_targets]
        if agent.handoff_targets
        else [],
        "tools": agent.tools,
        "modality": agent.modality.value
        if hasattr(agent.modality, "value")
        else agent.modality,
        "panels": agent.panels,
        "is_active": agent.is_active,
    }

    # Save version
    agent_version = AgentVersion(
        agent_id=agent.id,
        version=agent.current_version,
        snapshot=snapshot,
    )
    db.add(agent_version)

    # Increment version
    agent.current_version += 1

    # Prepare update data dict, excluding None values
    update_data = data.model_dump(exclude_unset=True)

    # Handle 'panels' specifically if present (convert enum to string)
    if "panels" in update_data and update_data["panels"] is not None:
        agent.panels = [p.value for p in update_data["panels"]]
        del update_data[
            "panels"
        ]  # Removed from dict so setattr doesn't overwrite it with Enum list

    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.commit()
    await db.refresh(agent)
    return agent


async def delete_agent(db: AsyncSession, agent_id: UUID, organization_id: UUID) -> None:
    agent = await get_agent(db, agent_id, organization_id)
    agent.is_active = False
    await db.commit()


async def list_agent_versions(
    db: AsyncSession, agent_id: UUID, organization_id: UUID
) -> list[AgentVersion]:
    # Verify agent exists and belongs to organization
    await get_agent(db, agent_id, organization_id)

    query = (
        select(AgentVersion)
        .where(AgentVersion.agent_id == agent_id)
        .order_by(desc(AgentVersion.version))
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_agent_version(
    db: AsyncSession, agent_id: UUID, version: int, organization_id: UUID
) -> AgentVersion:
    # Verify agent exists
    await get_agent(db, agent_id, organization_id)

    query = select(AgentVersion).where(
        AgentVersion.agent_id == agent_id, AgentVersion.version == version
    )
    result = await db.execute(query)
    ver = result.scalar_one_or_none()
    if not ver:
        raise NotFoundException(f"Version {version} not found for agent {agent_id}")
    return ver


async def duplicate_agent(
    db: AsyncSession, agent_id: UUID, organization_id: UUID
) -> Agent:
    source = await get_agent(db, agent_id, organization_id)

    new_agent = Agent(
        organization_id=organization_id,
        name=f"{source.name} (Copy)",
        instructions=source.instructions,
        model=source.model,
        voice=source.voice,
        handoff_targets=source.handoff_targets,
        tools=source.tools,
        modality=source.modality,
        panels=source.panels,
    )
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)
    return new_agent


async def export_agents(db: AsyncSession, organization_id: UUID) -> list[Agent]:
    query = select(Agent).where(
        Agent.organization_id == organization_id,
        Agent.is_active == True,  # noqa: E712
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def import_agents(
    db: AsyncSession, organization_id: UUID, agents_data: list[AgentExport]
) -> tuple[int, int, list[Agent]]:
    # Get existing names to skip duplicates
    query = select(Agent.name).where(
        Agent.organization_id == organization_id,
        Agent.is_active == True,  # noqa: E712
    )
    result = await db.execute(query)
    existing_names = set(result.scalars().all())

    created_agents = []
    skipped_count = 0

    for agent_data in agents_data:
        if agent_data.name in existing_names:
            skipped_count += 1
            continue

        new_agent = Agent(
            organization_id=organization_id,
            name=agent_data.name,
            instructions=agent_data.instructions,
            model=agent_data.model,
            voice=agent_data.voice,
            modality=agent_data.modality,
            panels=[p.value for p in agent_data.panels],
            tools=agent_data.tools,
            handoff_targets=[],
        )
        db.add(new_agent)
        created_agents.append(new_agent)
        # Add to set to prevent duplicates within the same batch
        existing_names.add(new_agent.name)

    if created_agents:
        await db.commit()
        for agent in created_agents:
            await db.refresh(agent)

    return len(created_agents), skipped_count, created_agents
