from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin
from app.core.security import get_current_user
from app.db.session import get_db
from app.exceptions.base import NotFoundException
from app.models.user import User
from app.schemas.agent import (
    AgentCreate,
    AgentExport,
    AgentImportRequest,
    AgentImportResponse,
    AgentRead,
    AgentUpdate,
    AgentVersionRead,
)
from app.services.agent import (
    create_agent,
    delete_agent,
    duplicate_agent,
    export_agents,
    get_agent,
    get_agent_version,
    import_agents,
    list_agent_versions,
    list_agents,
    update_agent,
)

router = APIRouter()


@router.post("/", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent_endpoint(
    data: AgentCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new agent. Admin only.
    """
    try:
        return await create_agent(db, current_user.organization_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[AgentRead])
async def list_agents_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all agents for the current organization.
    """
    return await list_agents(db, current_user.organization_id)


@router.get("/export", response_model=list[AgentExport])
async def export_agents_endpoint(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Export all agents as JSON. Admin only.
    """
    return await export_agents(db, current_user.organization_id)


@router.post("/import", response_model=AgentImportResponse)
async def import_agents_endpoint(
    data: AgentImportRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Import agents from JSON. Skips duplicates. Admin only.
    """
    created, skipped, agents = await import_agents(
        db, current_user.organization_id, data.agents
    )
    return AgentImportResponse(created=created, skipped=skipped, agents=agents)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent_endpoint(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific agent by ID.
    """
    try:
        return await get_agent(db, agent_id, current_user.organization_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{agent_id}", response_model=AgentRead)
async def update_agent_endpoint(
    agent_id: UUID,
    data: AgentUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an agent. Admin only.
    """
    try:
        return await update_agent(db, agent_id, current_user.organization_id, data)
    except (NotFoundException, ValueError) as e:
        status_code = 404 if isinstance(e, NotFoundException) else 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_endpoint(
    agent_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-delete an agent. Admin only.
    """
    try:
        await delete_agent(db, agent_id, current_user.organization_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{agent_id}/versions", response_model=list[AgentVersionRead])
async def list_agent_versions_endpoint(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all versions for an agent.
    """
    try:
        return await list_agent_versions(db, agent_id, current_user.organization_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{agent_id}/versions/{version}", response_model=AgentVersionRead)
async def get_agent_version_endpoint(
    agent_id: UUID,
    version: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific version of an agent.
    """
    try:
        return await get_agent_version(
            db, agent_id, version, current_user.organization_id
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{agent_id}/duplicate",
    response_model=AgentRead,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_agent_endpoint(
    agent_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Duplicate an agent. Admin only.
    """
    try:
        return await duplicate_agent(db, agent_id, current_user.organization_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
