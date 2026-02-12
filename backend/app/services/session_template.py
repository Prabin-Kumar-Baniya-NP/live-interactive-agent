from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import NotFoundException
from app.models.agent import Agent
from app.models.session_template import SessionTemplate
from app.schemas.session_template import SessionTemplateCreate, SessionTemplateUpdate


async def validate_agent_ids(
    db: AsyncSession, organization_id: UUID, agent_ids: list[UUID]
) -> None:
    if not agent_ids:
        # Schema validation catches empty list, but good to have here too
        raise ValueError("agent_ids must contain at least one agent ID")

    query = select(Agent.id).where(
        Agent.organization_id == organization_id,
        Agent.id.in_(agent_ids),
        Agent.is_active == True,  # noqa: E712
    )
    result = await db.execute(query)
    found_ids = set(result.scalars().all())
    requested_ids = set(agent_ids)

    missing = requested_ids - found_ids
    if missing:
        raise ValueError(
            f"Invalid agent IDs: {missing}. Agents must exist in the same organization."
        )


def validate_initial_agent(
    agent_ids: list[UUID], initial_agent_id: UUID | None
) -> None:
    if initial_agent_id and initial_agent_id not in agent_ids:
        raise ValueError("initial_agent_id must be one of the agent_ids")


async def validate_enabled_panels(
    db: AsyncSession,
    organization_id: UUID,
    agent_ids: list[UUID],
    enabled_panels: list[str],
) -> None:
    if not enabled_panels:
        return

    # Fetch agents and their panels
    query = select(Agent.panels).where(
        Agent.organization_id == organization_id,
        Agent.id.in_(agent_ids),
        Agent.is_active == True,  # noqa: E712
    )
    result = await db.execute(query)
    agent_panels_lists = result.scalars().all()

    # Flatten set of all available panels from the agents
    available_panels = set()
    for panels in agent_panels_lists:
        available_panels.update(panels)

    # Check if requested panels are supported by the agents
    requested_panels = set(enabled_panels)
    unsupported = requested_panels - available_panels

    if unsupported:
        raise ValueError(
            f"""
            Invalid panels: {unsupported}.
            Enabled panels must be supported by at least one agent in the set.
            """
        )


async def create_session_template(
    db: AsyncSession, organization_id: UUID, data: SessionTemplateCreate
) -> SessionTemplate:
    # Validate agents existence
    await validate_agent_ids(db, organization_id, data.agent_ids)

    # Validate initial agent
    validate_initial_agent(data.agent_ids, data.initial_agent_id)

    # Validate panels
    await validate_enabled_panels(
        db, organization_id, data.agent_ids, data.enabled_panels
    )

    session_template = SessionTemplate(
        organization_id=organization_id,
        name=data.name,
        description=data.description,
        agent_ids=data.agent_ids,
        initial_agent_id=data.initial_agent_id,
        modality_profile=data.modality_profile,
        enabled_panels=data.enabled_panels,
        max_duration_seconds=data.max_duration_seconds,
        idle_timeout_seconds=data.idle_timeout_seconds,
    )
    db.add(session_template)
    await db.commit()
    await db.refresh(session_template)
    return session_template


async def get_session_template(
    db: AsyncSession, template_id: UUID, organization_id: UUID
) -> SessionTemplate:
    query = select(SessionTemplate).where(
        SessionTemplate.id == template_id,
        SessionTemplate.organization_id == organization_id,
        SessionTemplate.is_active == True,  # noqa: E712
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    if not template:
        raise NotFoundException(
            f"Session Template {template_id} not found in this organization"
        )
    return template


async def list_session_templates(
    db: AsyncSession, organization_id: UUID
) -> list[SessionTemplate]:
    query = (
        select(SessionTemplate)
        .where(
            SessionTemplate.organization_id == organization_id,
            SessionTemplate.is_active == True,  # noqa: E712
        )
        .order_by(desc(SessionTemplate.created_at))
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_session_template(
    db: AsyncSession,
    template_id: UUID,
    organization_id: UUID,
    data: SessionTemplateUpdate,
) -> SessionTemplate:
    template = await get_session_template(db, template_id, organization_id)

    # Determine validation context
    # If agent_ids is updated, use new list. Else use existing from DB.
    target_agent_ids = (
        data.agent_ids if data.agent_ids is not None else template.agent_ids
    )

    # If initial_agent_id is updated, use new. Else use existing.
    target_initial_agent_id = (
        data.initial_agent_id
        if data.initial_agent_id is not None
        else template.initial_agent_id
    )

    # If enabled_panels is updated, use new. Else use existing.
    target_enabled_panels = (
        data.enabled_panels
        if data.enabled_panels is not None
        else template.enabled_panels
    )

    # Validations
    if data.agent_ids is not None:
        await validate_agent_ids(db, organization_id, target_agent_ids)

    # Validate initial agent (check against the comprehensive target list)
    if data.initial_agent_id is not None or data.agent_ids is not None:
        validate_initial_agent(target_agent_ids, target_initial_agent_id)

    # Validate panels (check against the comprehensive target list)
    if data.enabled_panels is not None or data.agent_ids is not None:
        await validate_enabled_panels(
            db, organization_id, target_agent_ids, target_enabled_panels
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)
    return template


async def delete_session_template(
    db: AsyncSession, template_id: UUID, organization_id: UUID
) -> None:
    template = await get_session_template(db, template_id, organization_id)
    template.is_active = False
    await db.commit()


async def clone_session_template(
    db: AsyncSession, template_id: UUID, organization_id: UUID
) -> SessionTemplate:
    source = await get_session_template(db, template_id, organization_id)

    new_template = SessionTemplate(
        organization_id=organization_id,
        name=f"{source.name} (Copy)",
        description=source.description,
        agent_ids=source.agent_ids,
        initial_agent_id=source.initial_agent_id,
        modality_profile=source.modality_profile,
        enabled_panels=source.enabled_panels,
        max_duration_seconds=source.max_duration_seconds,
        idle_timeout_seconds=source.idle_timeout_seconds,
    )
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)
    return new_template
