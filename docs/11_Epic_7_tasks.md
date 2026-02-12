# Epic 7 — Session Template & Configuration System

## Task Breakdown

**Epic Summary:** Build the session template system — the configuration blueprint that defines what happens when an end-user connects. A session template bundles together an agent set, modality profile, panel permissions, and behavioral settings (timeout, max duration). Session templates are scoped to an organization (multi-tenancy). This epic covers the data layer, service logic, and REST API — NOT the frontend dashboard (Epic 35), LiveKit token generation (Epic 8), or tool registry (Epic 10).

**Layer:** Platform API
**Dependencies:** Epic 6 (Agent Definition CRUD)

---

## Task Organization

Each task follows this format:

- **Task ID:** Unique identifier
- **Title:** Brief description
- **Status:** PENDING | RUNNING | COMPLETED | ERROR
- **Estimated Effort:** S (Small: 1-2h) | M (Medium: 3-5h) | L (Large: 6-8h)
- **Description:** What needs to be done
- **Acceptance Criteria:** How to verify completion
- **Dependencies:** Which tasks must be completed first

---

## Enum Definitions

The following Python enums will be added to `backend/app/models/enums.py` and reused across models and schemas:

### ModalityProfile

Defines the overall modality profile for a session — what media inputs are enabled for end-users during the session.

```python
@unique
class ModalityProfile(str, Enum):
    AUDIO_ONLY = "audio_only"                    # Voice conversation only
    AUDIO_CAMERA = "audio_camera"                # Voice + webcam
    AUDIO_SCREENSHARE = "audio_screenshare"      # Voice + screen share
    AUDIO_CAMERA_SCREENSHARE = "audio_camera_screenshare"  # Voice + webcam + screen share
```

> **Note:** `ModalityProfile` is a session-level setting that defines what the end-user's browser is allowed to publish. It is distinct from `AgentModality` (Epic 6) which defines what an individual agent needs. The session-level modality must be a superset of the modalities required by all agents in the template's agent set.

---

## Domain 1: Database Model & Migration

### Task 7.1 — Add ModalityProfile Enum & Create Session Template Database Model

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Add the `ModalityProfile` enum to `backend/app/models/enums.py` and create the SQLAlchemy ORM model for the `session_templates` table. This table stores session template configurations — name, description, agent set, modality profile, enabled panels, timeout settings, max duration, and the initial agent. Each session template belongs to an organization (multi-tenancy via `organization_id` foreign key).

**Tasks:**

- Add `ModalityProfile` enum to `backend/app/models/enums.py` (as defined in the Enum Definitions section above)
- Create `backend/app/models/session_template.py` with the `SessionTemplate` model:
  - `id: UUID` — primary key, auto-generated
  - `organization_id: UUID` — foreign key to `organizations.id`, required
  - `name: str` — display name (e.g., "Coding Interview Template"), required
  - `description: str | None` — optional description of the template's purpose
  - `agent_ids: ARRAY(UUID)` — PostgreSQL array of agent UUIDs that belong to this session's agent set, required
  - `initial_agent_id: UUID | None` — the UUID of the agent that greets the user first (must be one of `agent_ids`), nullable (defaults to first agent in set)
  - `modality_profile: ModalityProfile` — enum column, default `ModalityProfile.AUDIO_ONLY`
  - `enabled_panels: ARRAY(String)` — PostgreSQL array of panel type identifiers enabled for this session (values from `PanelType` enum), default `[]`
  - `max_duration_seconds: int | None` — hard limit on session duration in seconds, nullable (no limit)
  - `idle_timeout_seconds: int` — seconds of user silence before marking as "away", default `300` (5 minutes)
  - `is_active: bool` — soft-delete flag, default `True`
  - `created_at: datetime` — auto-set on creation
  - `updated_at: datetime` — auto-set on update
- Add `organization` relationship (back_populates)
- Update `Organization` model to add `session_templates` relationship
- Register the model in `backend/app/models/__init__.py`

**Acceptance Criteria:**

- [ ] `ModalityProfile` enum is added to `backend/app/models/enums.py`
- [ ] `backend/app/models/session_template.py` exists with the `SessionTemplate` class
- [ ] All columns defined as specified above
- [ ] Foreign key to `organizations.id` is set correctly
- [ ] `modality_profile` uses `ModalityProfile` enum (stored as string in PostgreSQL, same pattern as `Agent.modality`)
- [ ] `agent_ids` uses `ARRAY(UUID)` — PostgreSQL native array
- [ ] `enabled_panels` uses `ARRAY(String)` — PostgreSQL native array
- [ ] `Organization` model has `session_templates` relationship added
- [ ] Model is exported from `backend/app/models/__init__.py`
- [ ] `from app.models import SessionTemplate` works

**Dependencies:** Epic 3 (Database models), Epic 4 (Project structure)

---

### Task 7.2 — Generate & Run Alembic Migration for Session Templates Table

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Generate an Alembic migration for the new `session_templates` table and run it to create the table in the database. This follows the same migration workflow established in Epic 3.

**Tasks:**

- Run `alembic revision --autogenerate -m "add_session_templates_table"` to generate migration
- Review the generated migration file for correctness
- Run `alembic upgrade head` to apply the migration
- Verify the `session_templates` table exists in PostgreSQL with correct columns and constraints

**Acceptance Criteria:**

- [ ] Migration file exists in `backend/alembic/versions/`
- [ ] Migration creates the `session_templates` table with all columns from Task 7.1
- [ ] Foreign key constraint to `organizations` table is present
- [ ] `alembic upgrade head` runs without errors
- [ ] `alembic downgrade -1` can reverse the migration
- [ ] Table is visible in the database with `\dt session_templates` or equivalent

**Dependencies:** Task 7.1

---

## Domain 2: Pydantic Schemas

### Task 7.3 — Create Session Template Pydantic Schemas

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create the Pydantic request/response schemas for session template CRUD endpoints. These schemas define the shape of data for creating, updating, and returning session templates via the API.

**Tasks:**

- Create `backend/app/schemas/session_template.py` with:
  - `SessionTemplateCreate` — request schema for creating a session template:
    - `name: str` — required, min length 1, max length 255
    - `description: str | None` — optional
    - `agent_ids: list[UUID]` — required, at least one agent
    - `initial_agent_id: UUID | None` — optional, must be one of `agent_ids`
    - `modality_profile: ModalityProfile` — optional, defaults to `ModalityProfile.AUDIO_ONLY`
    - `enabled_panels: list[PanelType]` — optional, default `[]`
    - `max_duration_seconds: int | None` — optional, must be positive if provided
    - `idle_timeout_seconds: int` — optional, defaults to `300`, must be positive
  - `SessionTemplateUpdate` — request schema for updating (all fields optional):
    - Same fields as `SessionTemplateCreate` but all `Optional`
  - `SessionTemplateRead` — response schema for returning a session template:
    - All fields from the database model, extends `TimestampSchema` with `from_attributes=True`
    - `id: UUID`, `organization_id: UUID`, `name`, `description`, `agent_ids: list[UUID]`, `initial_agent_id: UUID | None`, `modality_profile: ModalityProfile`, `enabled_panels: list[str]`, `max_duration_seconds: int | None`, `idle_timeout_seconds: int`, `is_active`, `created_at`, `updated_at`
- Import `ModalityProfile` and `PanelType` from `app.models.enums` for reuse in schemas
- All schemas should extend `BaseSchema` or `TimestampSchema` from `app.schemas.base`
- Add a validator on `SessionTemplateCreate` to ensure `initial_agent_id` (if provided) is present in `agent_ids`
- Add a validator on `SessionTemplateCreate` to ensure `agent_ids` has at least one entry

**Acceptance Criteria:**

- [ ] `backend/app/schemas/session_template.py` exists with `SessionTemplateCreate`, `SessionTemplateUpdate`, `SessionTemplateRead`
- [ ] `name` has length validation (1-255 chars)
- [ ] `agent_ids` requires at least one UUID
- [ ] `initial_agent_id` is validated against `agent_ids` when provided
- [ ] `modality_profile` uses the `ModalityProfile` enum
- [ ] `enabled_panels` values are validated against the `PanelType` enum
- [ ] `max_duration_seconds` must be positive if provided
- [ ] `idle_timeout_seconds` must be positive
- [ ] `SessionTemplateUpdate` has all fields as optional (for partial updates)
- [ ] `SessionTemplateRead` can be constructed from an ORM `SessionTemplate` model instance
- [ ] All schemas are importable from `app.schemas.session_template`

**Dependencies:** Task 7.1, Epic 4 (Task 4.8 — base schemas)

---

## Domain 3: Service Layer

### Task 7.4 — Create Session Template Service Layer

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the session template service module containing the business logic for session template CRUD operations. This service layer sits between the API routes and the database, following the layered architecture pattern established in previous epics. All operations are scoped to the current user's organization for multi-tenancy.

**Tasks:**

- Create `backend/app/services/session_template.py` with:
  - `create_session_template(db: AsyncSession, organization_id: UUID, data: SessionTemplateCreate) -> SessionTemplate`:
    - Create a new session template record for the given organization
    - Return the created template
  - `get_session_template(db: AsyncSession, template_id: UUID, organization_id: UUID) -> SessionTemplate`:
    - Fetch template by ID, scoped to the organization
    - Raise `NotFoundException` if not found or belongs to a different org
  - `list_session_templates(db: AsyncSession, organization_id: UUID) -> list[SessionTemplate]`:
    - Return all active session templates for the given organization
    - Order by `created_at` descending (newest first)
  - `update_session_template(db: AsyncSession, template_id: UUID, organization_id: UUID, data: SessionTemplateUpdate) -> SessionTemplate`:
    - Fetch the template (scoped to org), update only the provided fields
    - Raise `NotFoundException` if not found
    - Return the updated template
  - `delete_session_template(db: AsyncSession, template_id: UUID, organization_id: UUID) -> None`:
    - Soft delete — set `is_active = False`
    - Raise `NotFoundException` if not found

**Acceptance Criteria:**

- [ ] `backend/app/services/session_template.py` exists with all five functions listed above
- [ ] `create_session_template()` creates a template scoped to the organization
- [ ] `get_session_template()` returns 404 if template doesn't exist or belongs to a different org
- [ ] `list_session_templates()` returns only active templates for the given organization
- [ ] `update_session_template()` supports partial updates (only updates fields that were provided)
- [ ] `delete_session_template()` soft-deletes by setting `is_active = False`
- [ ] All functions use `AsyncSession` for async database operations

**Dependencies:** Task 7.1, Task 7.3

---

## Domain 4: REST API Endpoints

### Task 7.5 — Create Session Template CRUD API Endpoints

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the REST API endpoints for Session Template CRUD operations. All endpoints require authentication and are scoped to the current user's organization. Create, update, and delete operations require `admin` role; read operations are available to all authenticated members.

**Tasks:**

- Create `backend/app/api/v1/session_templates.py` with:
  - `POST /api/v1/session-templates` — create a new session template (admin only)
    - Accepts `SessionTemplateCreate` request body
    - Uses `organization_id` from the current authenticated user
    - Returns `SessionTemplateRead` with 201 status
  - `GET /api/v1/session-templates` — list all session templates for the current org (any authenticated user)
    - Returns `list[SessionTemplateRead]`
  - `GET /api/v1/session-templates/{template_id}` — get a specific template by ID (any authenticated user)
    - Returns `SessionTemplateRead`
    - Returns 404 if not found or belongs to different org
  - `PUT /api/v1/session-templates/{template_id}` — update a session template (admin only)
    - Accepts `SessionTemplateUpdate` request body (partial update)
    - Returns `SessionTemplateRead`
  - `DELETE /api/v1/session-templates/{template_id}` — soft-delete a session template (admin only)
    - Returns 204 No Content
- Register the session templates router in `backend/app/api/v1/router.py` with prefix `/session-templates` and tag `"session-templates"`
- Use `get_current_user` dependency for authentication
- Use `require_admin` dependency for write operations

**Acceptance Criteria:**

- [ ] `POST /api/v1/session-templates` creates a template and returns 201
- [ ] `GET /api/v1/session-templates` returns a list of templates for the current org
- [ ] `GET /api/v1/session-templates/{template_id}` returns a single template or 404
- [ ] `PUT /api/v1/session-templates/{template_id}` updates a template with partial data
- [ ] `DELETE /api/v1/session-templates/{template_id}` soft-deletes and returns 204
- [ ] Create, update, and delete endpoints require `admin` role
- [ ] GET endpoints are accessible to any authenticated user (admin or member)
- [ ] All endpoints are scoped to the current user's organization (no cross-org access)
- [ ] Endpoints appear in Swagger UI under the `"session-templates"` tag
- [ ] Error responses follow the structured format from Epic 4

**Dependencies:** Task 7.4, Epic 5 (auth dependencies & RBAC)

---

## Domain 5: Template Validation

### Task 7.6 — Add Session Template Validation Logic

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Add validation logic to ensure that a session template's references are consistent and valid. This includes validating that all referenced agent IDs exist within the same organization, that the initial agent is part of the agent set, and that enabled panels are a subset of panels assigned to the referenced agents. Validation runs on create and update.

**Tasks:**

- Add validation functions to `backend/app/services/session_template.py`:
  - `validate_agent_ids(db: AsyncSession, organization_id: UUID, agent_ids: list[UUID]) -> None`:
    - Query the database for all referenced agent IDs within the organization
    - If any agent ID doesn't exist or belongs to a different org, raise `BadRequestException` with a clear message listing the invalid IDs
  - `validate_initial_agent(agent_ids: list[UUID], initial_agent_id: UUID | None) -> None`:
    - If `initial_agent_id` is provided and not present in `agent_ids`, raise `BadRequestException`
  - `validate_enabled_panels(db: AsyncSession, organization_id: UUID, agent_ids: list[UUID], enabled_panels: list[str]) -> None`:
    - Fetch the panels assigned to the referenced agents
    - If any panel in `enabled_panels` is not assigned to at least one agent in the agent set, raise `BadRequestException` with a clear message
- Call the validation functions in `create_session_template()` and `update_session_template()` when relevant fields are provided

**Acceptance Criteria:**

- [ ] Creating a template with invalid `agent_ids` (non-existent or cross-org) returns 400 with a clear error message
- [ ] Updating a template with invalid `agent_ids` returns 400
- [ ] `initial_agent_id` not present in `agent_ids` returns 400
- [ ] `enabled_panels` referencing panels not assigned to any agent in the set returns 400
- [ ] Valid references pass validation without error
- [ ] Empty `agent_ids` is rejected (at least one agent required)
- [ ] `null` or empty `enabled_panels` pass without error

**Dependencies:** Task 7.5

---

## Domain 6: Template Cloning & Seed Data

### Task 7.7 — Create Session Template Clone Endpoint

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create an endpoint to clone an existing session template. This copies all the configuration from an existing template to create a new one with a modified name (e.g., "Coding Interview Template (Copy)"). This is useful for creating variants of templates without starting from scratch.

**Tasks:**

- Add clone service function to `backend/app/services/session_template.py`:
  - `clone_session_template(db: AsyncSession, template_id: UUID, organization_id: UUID) -> SessionTemplate`:
    - Fetch the source template (scoped to org)
    - Create a new template with the same configuration but name appended with " (Copy)"
    - Return the new template
- Add endpoint to `backend/app/api/v1/session_templates.py`:
  - `POST /api/v1/session-templates/{template_id}/clone` — clone a template (admin only)
  - Returns `SessionTemplateRead` with 201 status

**Acceptance Criteria:**

- [ ] `POST /api/v1/session-templates/{template_id}/clone` creates a copy of the template
- [ ] Cloned template has " (Copy)" appended to the name
- [ ] Cloned template has a new UUID (not the same as source)
- [ ] All configuration fields are copied (description, agent_ids, initial_agent_id, modality_profile, enabled_panels, max_duration_seconds, idle_timeout_seconds)
- [ ] Returns 404 if source template not found
- [ ] Requires admin role
- [ ] Endpoint is scoped to the current user's organization

**Dependencies:** Task 7.5

---

### Task 7.8 — Update Seed Data with Sample Session Templates

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Update the seed script with sample session template data for development. The templates should reference the existing seeded agents (Triage Agent, Coding Expert) and provide realistic configuration examples.

**Tasks:**

- Update `backend/scripts/seed.py`:
  - Add a sample session template (e.g., "Default Coding Interview") that:
    - References the Triage Agent and Coding Expert agent IDs
    - Sets initial agent to Triage Agent
    - Uses `ModalityProfile.AUDIO_SCREENSHARE`
    - Enables `coding_ide` panel
    - Sets `max_duration_seconds` to `3600` (1 hour)
    - Sets `idle_timeout_seconds` to `300` (5 minutes)
  - Ensure the template is linked to the test organization
  - Seed script should remain idempotent (no duplicates on re-run)

**Acceptance Criteria:**

- [ ] Seed script creates a sample session template
- [ ] Template references existing seeded agents
- [ ] Template has realistic configuration values
- [ ] Seed script remains idempotent (no duplicates on re-run)
- [ ] `python backend/scripts/seed.py` runs without errors

**Dependencies:** Task 7.5

---

## Recommended Execution Order

1. **Task 7.1** Add ModalityProfile Enum & Create Session Template Database Model
2. **Task 7.2** Generate & Run Alembic Migration for Session Templates Table
3. **Task 7.3** Create Session Template Pydantic Schemas
4. **Task 7.4** Create Session Template Service Layer
5. **Task 7.5** Create Session Template CRUD API Endpoints
6. **Task 7.6** Add Session Template Validation Logic
7. **Task 7.7** Create Session Template Clone Endpoint
8. **Task 7.8** Update Seed Data with Sample Session Templates
