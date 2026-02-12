# Epic 6 — Agent Definition CRUD

## Task Breakdown

**Epic Summary:** Build the API endpoints and database models for creating, reading, updating, and deleting AI agent definitions. This is the core of what platform customers configure — the agents' personalities, tools, and behaviors. Agent definitions are scoped to an organization (multi-tenancy). This epic covers the data layer, service logic, and REST API — NOT the frontend dashboard (Epic 34) or tool registry (Epic 10).

**Layer:** Platform API
**Dependencies:** Epic 4 (Platform API Foundation), Epic 5 (Authentication & Authorization)

---

## Task Organization

Each task follows this format:

- **Task ID:** Unique identifier
- **Title:** Brief description
- **Status:** COMPLETED | RUNNING | COMPLETED | ERROR
- **Estimated Effort:** S (Small: 1-2h) | M (Medium: 3-5h) | L (Large: 6-8h)
- **Description:** What needs to be done
- **Acceptance Criteria:** How to verify completion
- **Dependencies:** Which tasks must be completed first

---

## Enum Definitions

The following Python enums will be defined in `backend/app/models/enums.py` and reused across models and schemas:

### AgentModality

Defines what media inputs an agent requires from the end-user.

```python
import enum

class AgentModality(str, enum.Enum):
    AUDIO_ONLY = "audio_only"            # Voice conversation only, no video
    AUDIO_CAMERA = "audio_camera"        # Voice + user's webcam feed
    AUDIO_SCREENSHARE = "audio_screenshare"  # Voice + user's screen share
```

### PanelType

Defines the available Interactive Workspace Panel types that can be assigned to an agent.

```python
class PanelType(str, enum.Enum):
    SLIDE_PRESENTER = "slide_presenter"   # Agent presents slides to the user
    NOTEPAD = "notepad"                   # Free-form text input from user
    CODING_IDE = "coding_ide"             # Code editor for user
    WHITEBOARD = "whiteboard"             # Collaborative drawing canvas
    DOCUMENT_VIEWER = "document_viewer"   # PDF/document rendering
```

> **Note:** Both enums inherit from `str` so they serialize to plain strings in JSON responses and can be stored as PostgreSQL native enum types or as `String` values. The `PanelType` enum provides compile-time validation but the database column stores them as `ARRAY(String)` since new panel types may be added in the future.

---

## Domain 1: Database Model & Migration

### Task 6.1 — Create Agent Definition Database Model

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the SQLAlchemy ORM model for the `agents` table and the shared enum definitions. This table stores agent definitions — name, instructions (system prompt), model, voice, handoff targets, modality needs, and workspace panel assignments. Each agent belongs to an organization (multi-tenancy via `organization_id` foreign key). List fields use PostgreSQL native `ARRAY` types for efficient querying, and constrained fields use Python enums for type safety.

**Tasks:**

- Create `backend/app/models/enums.py` with the `AgentModality` and `PanelType` enums (as defined in the Enum Definitions section above)
- Create `backend/app/models/agent.py` with the `Agent` model:
  - `id: UUID` — primary key, auto-generated
  - `organization_id: UUID` — foreign key to `organizations.id`, required
  - `name: str` — display name (e.g., "Coding Expert"), required
  - `instructions: str` — system prompt text, required (use `Text` type for long content)
  - `model: str` — LLM model identifier (e.g., "gpt-4.1-mini"), required, with a sensible default
  - `voice: str | None` — TTS voice identifier (e.g., "cartesia:sonic"), nullable
  - `handoff_targets: ARRAY(UUID)` — PostgreSQL array of agent UUIDs this agent can hand off to, nullable, default `[]`
  - `tools: ARRAY(String)` — PostgreSQL array of tool identifiers assigned to this agent, nullable, default `[]`
  - `modality: AgentModality` — enum column using `AgentModality`, default `AgentModality.AUDIO_ONLY`
  - `panels: ARRAY(String)` — PostgreSQL array of workspace panel IDs (values from `PanelType` enum), nullable, default `[]`
  - `is_active: bool` — soft-delete flag, default `True`
  - `created_at: datetime` — auto-set on creation
  - `updated_at: datetime` — auto-set on update
- Add `organization` relationship (back_populates)
- Update `Organization` model to add `agents` relationship
- Register the model in `backend/app/models/__init__.py`

**Acceptance Criteria:**

- [ ] `backend/app/models/enums.py` exists with `AgentModality` and `PanelType` enums
- [ ] `backend/app/models/agent.py` exists with the `Agent` class
- [ ] All columns defined as specified above
- [ ] Foreign key to `organizations.id` is set correctly
- [ ] `modality` uses `AgentModality` enum (stored as string in PostgreSQL)
- [ ] `handoff_targets` uses `ARRAY(UUID)` — PostgreSQL native array, not JSON
- [ ] `tools` uses `ARRAY(String)` — PostgreSQL native array, not JSON
- [ ] `panels` uses `ARRAY(String)` — PostgreSQL native array, not JSON
- [ ] `Organization` model has `agents` relationship added
- [ ] Model is exported from `backend/app/models/__init__.py`
- [ ] `from app.models import Agent` works

**Dependencies:** Epic 3 (Database models), Epic 4 (Project structure)

---

### Task 6.2 — Generate & Run Alembic Migration for Agents Table

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Generate an Alembic migration for the new `agents` table and run it to create the table in the database. This follows the same migration workflow established in Epic 3.

**Tasks:**

- Run `alembic revision --autogenerate -m "add_agents_table"` to generate migration
- Review the generated migration file for correctness
- Run `alembic upgrade head` to apply the migration
- Verify the `agents` table exists in PostgreSQL with correct columns and constraints

**Acceptance Criteria:**

- [ ] Migration file exists in `backend/alembic/versions/`
- [ ] Migration creates the `agents` table with all columns from Task 6.1
- [ ] Foreign key constraint to `organizations` table is present
- [ ] `alembic upgrade head` runs without errors
- [ ] `alembic downgrade -1` can reverse the migration
- [ ] Table is visible in the database with `\dt agents` or equivalent

**Dependencies:** Task 6.1

---

## Domain 2: Pydantic Schemas

### Task 6.3 — Create Agent Pydantic Schemas

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create the Pydantic request/response schemas for agent CRUD endpoints. These schemas define the shape of data for creating, updating, and returning agent definitions via the API.

**Tasks:**

- Create `backend/app/schemas/agent.py` with:
  - `AgentCreate` — request schema for creating an agent:
    - `name: str` — required, min length 1, max length 255
    - `instructions: str` — required, min length 1
    - `model: str | None` — optional
    - `voice: str | None` — optional
    - `handoff_targets: list[UUID] | None` — optional list of agent UUIDs, default `[]`
    - `tools: list[str] | None` — optional list of tool identifiers, default `[]`
    - `modality: AgentModality` — optional, uses `AgentModality` enum, defaults to `AgentModality.AUDIO_ONLY`
    - `panels: list[PanelType] | None` — optional list of `PanelType` enum values, default `[]`
  - `AgentUpdate` — request schema for updating an agent (all fields optional):
    - Same fields as `AgentCreate` but all `Optional`
  - `AgentPublic` — response schema for returning an agent:
    - All fields from the database model, extends `BaseSchema` with `from_attributes=True`
    - `id: UUID`, `organization_id: UUID`, `name`, `instructions`, `model`, `voice`, `handoff_targets: list[UUID]`, `tools: list[str]`, `modality: AgentModality`, `panels: list[str]`, `is_active`, `created_at`, `updated_at`
- Import `AgentModality` and `PanelType` from `app.models.enums` for reuse in schemas
- All schemas should extend `BaseSchema` from `app.schemas.base`

**Acceptance Criteria:**

- [ ] `backend/app/schemas/agent.py` exists with `AgentCreate`, `AgentUpdate`, `AgentPublic`
- [ ] `name` has length validation (1-255 chars)
- [ ] `instructions` has minimum length validation (1 char)
- [ ] `modality` uses the `AgentModality` enum — only accepts `"audio_only"`, `"audio_camera"`, `"audio_screenshare"`
- [ ] `panels` values are validated against the `PanelType` enum
- [ ] `handoff_targets` and `tools` are typed as `list` (matching PostgreSQL ARRAY)
- [ ] `AgentUpdate` has all fields as optional (for partial updates)
- [ ] `AgentPublic` can be constructed from an ORM `Agent` model instance
- [ ] All schemas are importable from `app.schemas.agent`

**Dependencies:** Epic 4 (Task 4.8 — base schemas)

---

## Domain 3: Service Layer

### Task 6.4 — Create Agent Service Layer

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the agent service module containing the business logic for agent CRUD operations. This service layer sits between the API routes and the database, following the layered architecture pattern established in previous epics. All operations are scoped to the current user's organization for multi-tenancy.

**Tasks:**

- Create `backend/app/services/agent.py` with:
  - `create_agent(db: AsyncSession, organization_id: UUID, data: AgentCreate) -> Agent`:
    - Create a new agent record for the given organization
    - Return the created agent
  - `get_agent(db: AsyncSession, agent_id: UUID, organization_id: UUID) -> Agent`:
    - Fetch agent by ID, scoped to the organization
    - Raise `NotFoundException` if not found or belongs to a different org
  - `list_agents(db: AsyncSession, organization_id: UUID) -> list[Agent]`:
    - Return all active agents for the given organization
    - Order by `created_at` descending (newest first)
  - `update_agent(db: AsyncSession, agent_id: UUID, organization_id: UUID, data: AgentUpdate) -> Agent`:
    - Fetch the agent (scoped to org), update only the provided fields
    - Raise `NotFoundException` if not found
    - Return the updated agent
  - `delete_agent(db: AsyncSession, agent_id: UUID, organization_id: UUID) -> None`:
    - Soft delete — set `is_active = False`
    - Raise `NotFoundException` if not found

**Acceptance Criteria:**

- [ ] `backend/app/services/agent.py` exists with all five functions listed above
- [ ] `create_agent()` creates an agent scoped to the organization
- [ ] `get_agent()` returns 404 if agent doesn't exist or belongs to a different org
- [ ] `list_agents()` returns only active agents for the given organization
- [ ] `update_agent()` supports partial updates (only updates fields that were provided)
- [ ] `delete_agent()` soft-deletes by setting `is_active = False`
- [ ] All functions use `AsyncSession` for async database operations

**Dependencies:** Task 6.1, Task 6.3

---

## Domain 4: REST API Endpoints

### Task 6.5 — Create Agent CRUD API Endpoints

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the REST API endpoints for Agent CRUD operations. All endpoints require authentication and are scoped to the current user's organization. Create and update operations require `admin` role; read operations are available to all authenticated members.

**Tasks:**

- Create `backend/app/api/v1/agents.py` with:
  - `POST /api/v1/agents` — create a new agent definition (admin only)
    - Accepts `AgentCreate` request body
    - Uses `organization_id` from the current authenticated user
    - Returns `AgentPublic` with 201 status
  - `GET /api/v1/agents` — list all agents for the current org (any authenticated user)
    - Returns `list[AgentPublic]`
  - `GET /api/v1/agents/{agent_id}` — get a specific agent by ID (any authenticated user)
    - Returns `AgentPublic`
    - Returns 404 if not found or belongs to different org
  - `PUT /api/v1/agents/{agent_id}` — update an agent definition (admin only)
    - Accepts `AgentUpdate` request body (partial update)
    - Returns `AgentPublic`
  - `DELETE /api/v1/agents/{agent_id}` — soft-delete an agent (admin only)
    - Returns 204 No Content
- Register the agents router in `backend/app/api/v1/router.py` with tag `"agents"`
- Use `get_current_user` dependency for authentication
- Use `require_role("admin")` dependency for write operations

**Acceptance Criteria:**

- [ ] `POST /api/v1/agents` creates an agent and returns 201
- [ ] `GET /api/v1/agents` returns a list of agents for the current org
- [ ] `GET /api/v1/agents/{agent_id}` returns a single agent or 404
- [ ] `PUT /api/v1/agents/{agent_id}` updates an agent with partial data
- [ ] `DELETE /api/v1/agents/{agent_id}` soft-deletes and returns 204
- [ ] Create, update, and delete endpoints require `admin` role
- [ ] GET endpoints are accessible to any authenticated user (admin or member)
- [ ] All endpoints are scoped to the current user's organization (no cross-org access)
- [ ] Endpoints appear in Swagger UI under the `"agents"` tag
- [ ] Error responses follow the structured format from Epic 4

**Dependencies:** Task 6.4, Epic 5 (auth dependencies & RBAC)

---

## Domain 5: Agent Versioning

### Task 6.6 — Create Agent Version History Model & Logic

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Implement agent versioning — whenever an agent definition is updated, save a snapshot of the previous configuration to an `agent_versions` table. This allows platform customers to view previous versions and potentially rollback. The version is a simple integer that auto-increments per agent.

**Tasks:**

- Create `backend/app/models/agent_version.py` with the `AgentVersion` model:
  - `id: UUID` — primary key
  - `agent_id: UUID` — foreign key to `agents.id`
  - `version: int` — auto-incrementing version number per agent (starts at 1)
  - `snapshot: JSON` — full snapshot of the agent's configuration at that version (name, instructions, model, voice, etc.)
  - `created_at: datetime` — when this version was saved
- Update `Agent` model to add `current_version: int` column (default 1)
- Update `Agent` model to add `versions` relationship
- Generate and run Alembic migration for the `agent_versions` table and `agents.current_version` column
- Update `backend/app/services/agent.py`:
  - In `update_agent()`: before applying updates, save the current state as a new `AgentVersion` record and increment `current_version`
- Register `AgentVersion` model in `backend/app/models/__init__.py`

**Acceptance Criteria:**

- [ ] `backend/app/models/agent_version.py` exists with `AgentVersion` class
- [ ] `Agent` model has `current_version` column
- [ ] Migration creates `agent_versions` table and adds `current_version` to `agents`
- [ ] Updating an agent automatically saves a version snapshot before applying changes
- [ ] Version number increments on each update
- [ ] `AgentVersion.snapshot` contains the complete previous configuration as JSON

**Dependencies:** Task 6.5

---

### Task 6.7 — Create Agent Version API Endpoints

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create API endpoints to list version history for an agent and view a specific version. These are read-only endpoints.

**Tasks:**

- Create `AgentVersionPublic` schema in `backend/app/schemas/agent.py`:
  - `id: UUID`, `agent_id: UUID`, `version: int`, `snapshot: dict`, `created_at: datetime`
- Add version service functions to `backend/app/services/agent.py`:
  - `list_agent_versions(db: AsyncSession, agent_id: UUID, organization_id: UUID) -> list[AgentVersion]` — returns all versions for an agent, ordered by version descending
  - `get_agent_version(db: AsyncSession, agent_id: UUID, version: int, organization_id: UUID) -> AgentVersion` — returns a specific version
- Add endpoints to `backend/app/api/v1/agents.py`:
  - `GET /api/v1/agents/{agent_id}/versions` — list all versions (any authenticated user)
  - `GET /api/v1/agents/{agent_id}/versions/{version}` — get a specific version (any authenticated user)

**Acceptance Criteria:**

- [ ] `AgentVersionPublic` schema exists
- [ ] `GET /api/v1/agents/{agent_id}/versions` returns version history
- [ ] `GET /api/v1/agents/{agent_id}/versions/{version}` returns a specific version snapshot
- [ ] Versions are ordered by version number descending (newest first)
- [ ] Returns 404 if agent or version not found
- [ ] Endpoints are scoped to the current user's organization

**Dependencies:** Task 6.6

---

## Domain 6: Agent Duplication & Validation

### Task 6.8 — Create Agent Duplication Endpoint

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create an endpoint to duplicate an existing agent. This copies all the configuration from an existing agent to create a new one with a modified name (e.g., "Coding Expert (Copy)"). This is useful for creating variants of agents without starting from scratch.

**Tasks:**

- Add duplicate service function to `backend/app/services/agent.py`:
  - `duplicate_agent(db: AsyncSession, agent_id: UUID, organization_id: UUID) -> Agent`:
    - Fetch the source agent (scoped to org)
    - Create a new agent with the same configuration but name appended with " (Copy)"
    - Reset `current_version` to 1, do not copy version history
    - Return the new agent
- Add endpoint to `backend/app/api/v1/agents.py`:
  - `POST /api/v1/agents/{agent_id}/duplicate` — duplicate an agent (admin only)
  - Returns `AgentPublic` with 201 status

**Acceptance Criteria:**

- [ ] `POST /api/v1/agents/{agent_id}/duplicate` creates a copy of the agent
- [ ] Duplicated agent has " (Copy)" appended to the name
- [ ] Duplicated agent has a new UUID (not the same as source)
- [ ] All configuration fields are copied (instructions, model, voice, tools, handoff_targets, modality, panels)
- [ ] Version history is NOT copied (new agent starts at version 1)
- [ ] Returns 404 if source agent not found
- [ ] Requires admin role
- [ ] Endpoint is scoped to the current user's organization

**Dependencies:** Task 6.5

---

### Task 6.9 — Add Agent Handoff Target Validation

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Add validation logic to ensure that `handoff_targets` references in an agent's configuration point to existing agents within the same organization. This prevents invalid handoff configurations (e.g., referencing an agent that doesn't exist or belongs to a different org). Validation runs on create and update.

**Tasks:**

- Add validation functions to `backend/app/services/agent.py`:
  - `validate_handoff_targets(db: AsyncSession, organization_id: UUID, handoff_targets: list[UUID]) -> None`:
    - Query the database for all referenced agent IDs within the organization
    - If any target ID doesn't exist or belongs to a different org, raise `BadRequestException` with a clear message listing the invalid IDs
- Call `validate_handoff_targets()` in `create_agent()` and `update_agent()` when `handoff_targets` is provided
- Self-referencing handoff targets should be rejected (agent cannot hand off to itself)

**Acceptance Criteria:**

- [ ] Creating an agent with invalid `handoff_targets` returns 400 with a clear error message
- [ ] Updating an agent with invalid `handoff_targets` returns 400
- [ ] `handoff_targets` referencing agents from a different organization are rejected
- [ ] Self-referencing handoff targets are rejected (cannot hand off to itself)
- [ ] Valid `handoff_targets` (existing agents in same org) pass validation
- [ ] `null` or empty `handoff_targets` pass without error

**Dependencies:** Task 6.5

---

## Domain 7: Bulk Operations & Documentation

### Task 6.10 — Create Bulk Export/Import Endpoints & Update Seed Data

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create endpoints for bulk exporting and importing agent configurations as JSON. This allows platform customers to backup agent configurations, transfer them between environments, or share agent templates. Also update the seed script with sample agent data for development.

**Tasks:**

- Add bulk service functions to `backend/app/services/agent.py`:
  - `export_agents(db: AsyncSession, organization_id: UUID) -> list[dict]` — returns all active agents as a list of JSON-serializable dicts (excluding `id`, `organization_id`, `created_at`, `updated_at` — only portable fields)
  - `import_agents(db: AsyncSession, organization_id: UUID, agents_data: list[dict]) -> list[Agent]` — creates multiple agents from a list of JSON configs, validates each one, skips duplicates by name
- Create schemas in `backend/app/schemas/agent.py`:
  - `AgentExport` — export format (portable fields only: name, instructions, model, voice, modality, panels, tools)
  - `AgentImportRequest` — `agents: list[AgentExport]`
  - `AgentImportResponse` — `created: int`, `skipped: int`, `agents: list[AgentPublic]`
- Add endpoints to `backend/app/api/v1/agents.py`:
  - `GET /api/v1/agents/export` — export all agents as JSON (admin only)
  - `POST /api/v1/agents/import` — import agents from JSON (admin only)
- Update `backend/scripts/seed.py`:
  - Add sample agent definitions (e.g., a "Triage Agent" and a "Coding Expert" agent) to the seed script
  - Agents should be linked to the test organization
- Update `backend/.env.example` if any new env vars are needed (unlikely for this task)

**Acceptance Criteria:**

- [ ] `GET /api/v1/agents/export` returns a JSON array of agent configurations
- [ ] Exported JSON does not include `id`, `organization_id`, or timestamps (portable format)
- [ ] `POST /api/v1/agents/import` creates agents from a JSON array
- [ ] Import skips agents whose names already exist in the org (no duplicates)
- [ ] Import returns a summary of how many agents were created vs skipped
- [ ] Both endpoints require admin role
- [ ] Seed script creates sample agent definitions
- [ ] Seed script remains idempotent (no duplicates on re-run)

**Dependencies:** Task 6.5

---

## Recommended Execution Order

1. **Task 6.1** Create Agent Definition Database Model
2. **Task 6.2** Generate & Run Alembic Migration for Agents Table
3. **Task 6.3** Create Agent Pydantic Schemas
4. **Task 6.4** Create Agent Service Layer
5. **Task 6.5** Create Agent CRUD API Endpoints
6. **Task 6.6** Create Agent Version History Model & Logic
7. **Task 6.7** Create Agent Version API Endpoints
8. **Task 6.8** Create Agent Duplication Endpoint
9. **Task 6.9** Add Agent Handoff Target Validation
10. **Task 6.10** Create Bulk Export/Import Endpoints & Update Seed Data
