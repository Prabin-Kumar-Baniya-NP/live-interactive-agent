# Epic 8 — LiveKit Token Generation & Session Initiation

## Task Breakdown

**Epic Summary:** Implement the endpoint that end-users call to start a session. This generates a LiveKit JWT access token with embedded metadata and creates a LiveKit room, triggering the agent runtime dispatch.

**Layer:** Platform API
**Dependencies:** Epic 2 (LiveKit Server Infrastructure), Epic 7 (Session Template & Configuration System)

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

## Domain 1: Database Models & Schema

### Task 8.1 — Extend Session Model for Token Metadata

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Extend the existing `Session` model (created in Epic 3) to include fields needed for session initiation. This includes session template linkage, user identification, and modality configuration.

**Tasks:**

- Update `backend/app/models/session.py`:
  - Add `session_template_id` field (UUID, ForeignKey to session_templates table)
  - Add `user_id` field (String, nullable — for identifying end-users)
  - Add `modality_profile` field (String, nullable — e.g., "audio", "audio+camera")
  - Add `enabled_panels` field (ARRAY(String), nullable — list of panel IDs)
  - Add `token_expiry` field (DateTime, nullable — when LiveKit JWT expires)
  - Ensure existing `room_name`, `status`, `started_at`, `ended_at` fields are present (from Epic 3)
- Create Alembic migration for schema changes
- Run migration locally to verify

**Acceptance Criteria:**

- [x] `Session` model includes all new fields
- [x] `enabled_panels` uses PostgreSQL ARRAY type, not JSONB
- [x] Alembic migration generated and runs successfully
- [x] Database schema updated (verify with `\d sessions` in psql)
- [x] Foreign key constraint exists for session_template_id

**Dependencies:** Epic 3 (Database Setup), Epic 7 (Session Templates)

**Note:** Use SQLAlchemy `ARRAY(String)` type for `enabled_panels` to follow PostgreSQL conventions.

---

## Domain 2: Pydantic Schemas

### Task 8.2 — Create Session Start Request/Response Schemas

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Define Pydantic schemas for session start endpoint following existing FastAPI patterns.

**Tasks:**

- Create `backend/app/schemas/session.py`:
  - `SessionStartRequest`:
    - `session_template_id: UUID`
    - `user_id: Optional[str] = None`
  - `SessionStartResponse`:
    - `session_id: UUID`
    - `room_name: str`
    - `access_token: str`
    - `livekit_url: str`
    - `token_expiry: datetime`
  - `SessionStatusResponse`:
    - `id: UUID` (mapped from session.id)
    - `room_name: str`
    - `status: str`
    - `started_at: Optional[datetime]`
    - `ended_at: Optional[datetime]`

**Acceptance Criteria:**

- [x] All schemas defined with proper Pydantic v2 syntax
- [x] Type hints are correct
- [x] Schemas follow existing project conventions
- [x] Importable from `app.schemas.session`

**Dependencies:** Task 8.1

---

## Domain 3: Room Name Generation

### Task 8.3 — Implement Room Name Generator

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create utility to generate unique LiveKit room names.

**Tasks:**

- Create `backend/app/services/room_name_generator.py`:
  - Function `generate_room_name() -> str`:
    - Format: `session_{timestamp}_{random_suffix}`
    - Example: `session_20260212_143022_a7b3c9`
    - Timestamp: UTC `YYYYMMDD_HHMMSS`
    - Random suffix: 6-char hex (using `secrets.token_hex(3)`)
    - Max 64 characters
    - URL-safe characters only

**Acceptance Criteria:**

- [x] Function generates unique room names
- [x] Format is URL-safe
- [x] Names under 64 characters
- [x] No collisions in 1000 iterations (test)

**Dependencies:** None

---

## Domain 4: Token Generation

### Task 8.4 — Create LiveKit Token Service

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Implement LiveKit JWT token generation using `livekit-api` SDK.

**Tasks:**

- Create `backend/app/services/livekit_token_service.py`:
  - Function `generate_access_token(room_name: str, identity: str, metadata: dict) -> str`:
    - Use `livekit.api.AccessToken`
    - Load `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` from env
    - Set room join permissions
    - Embed metadata: `session_template_id`, `user_id`, `modality_profile`, `enabled_panels`
    - Default TTL: 1 hour (3600 seconds)
    - Return signed JWT

**Acceptance Criteria:**

- [x] Tokens generated successfully
- [x] Metadata embedded correctly
- [x] TTL set to 1 hour
- [x] Tokens can be decoded and verified

**Dependencies:** Epic 2 (LiveKit API keys configured)

---

## Domain 5: Session Service

### Task 8.5 — Implement Session Creation Service

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create service layer orchestrating session creation.

**Tasks:**

- Create `backend/app/services/session_service.py`:
  - `async def create_session(session_template_id: UUID, user_id: Optional[str], organization_id: UUID) -> SessionStartResponse`:
    - Validate template exists and belongs to organization
    - Extract config from template (modality_profile, enabled_panels)
    - Generate room name
    - Create session record in database
    - Generate LiveKit token
    - Return SessionStartResponse
  - `async def get_session_status(session_id: UUID, organization_id: UUID) -> SessionStatusResponse`:
    - Query session, verify ownership, return status
  - `async def list_sessions(organization_id: UUID, limit: int = 50, offset: int = 0) -> List[SessionStatusResponse]`:
    - List organization sessions with pagination

**Acceptance Criteria:**

- [x] All three functions implemented as async
- [x] Template ownership validated
- [x] Database records created correctly
- [x] Token included in response
- [x] Error handling for template not found

**Dependencies:** Task 8.1, Task 8.2, Task 8.3, Task 8.4, Epic 7

---

## Domain 6: API Endpoints

### Task 8.6 — Create Session Start Endpoint

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Build `POST /api/v1/sessions/start` endpoint.

**Tasks:**

- Create `backend/app/routers/sessions.py`:
  - `POST /api/v1/sessions/start`:
    - Request: `SessionStartRequest`
    - Response: `SessionStartResponse` (201)
    - Auth required (dependency from Epic 5)
    - Extract organization_id from auth
    - Call `session_service.create_session()`
    - Handle errors (400, 403, 404, 500)
- Register router in `backend/app/main.py`
- Add OpenAPI documentation

**Acceptance Criteria:**

- [x] Endpoint exists and registered
- [x] Authentication applied
- [x] Returns 201 with valid response
- [x] Proper error responses
- [x] OpenAPI docs generated

**Dependencies:** Task 8.2, Task 8.5, Epic 5 (or stub)

---

### Task 8.7 — Create Session Query Endpoints

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Add endpoints for session status and listing.

**Tasks:**

- Add to `backend/app/routers/sessions.py`:
  - `GET /api/v1/sessions/{session_id}`:
    - Response: `SessionStatusResponse`
    - Verify ownership, return 404 if not found
  - `GET /api/v1/sessions`:
    - Query params: `limit`, `offset`, `status`, `user_id`
    - Response: `List[SessionStatusResponse]`
    - Pagination support

**Acceptance Criteria:**

- [x] Both endpoints functional
- [x] Ownership validation works
- [x] Pagination works
- [x] Filters apply correctly

**Dependencies:** Task 8.5, Task 8.6

---

## Domain 7: Access Control

### Task 8.8 — Implement Session Access Control

**Status:** PENDING
**Estimated Effort:** S

**Description:**
Add organization-level access control.

**Tasks:**

- Create/extend `backend/app/dependencies/auth.py`:
  - `get_current_organization() -> UUID`:
    - Extract org ID from JWT
    - Raise 401 if invalid
  - `verify_session_template_access(session_template_id: UUID, organization_id: UUID)`:
    - Verify template belongs to org
    - Raise 404 if not found, 403 if wrong org
- Apply to all session endpoints

**Acceptance Criteria:**

- [ ] Dependency extracts org ID correctly
- [ ] Template ownership verified
- [ ] Proper error codes (401, 403, 404)
- [ ] Tests cover cross-org access attempts

**Dependencies:** Task 8.6, Epic 5

---

## Domain 8: Configuration

### Task 8.9 — Add Token Expiry Configuration

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Make token TTL configurable.

**Tasks:**

- Add to `backend/app/core/config.py`:
  - `LIVEKIT_TOKEN_TTL_SECONDS: int = 3600`
  - Load from env var
- Add to `.env.example`:
  - `LIVEKIT_TOKEN_TTL_SECONDS=3600`
- Update token service to use config value

**Acceptance Criteria:**

- [ ] Config variable exists
- [ ] Defaults to 1 hour
- [ ] Loaded from environment
- [ ] Token service uses config

**Dependencies:** Task 8.4

**Note:** Token refresh will be implemented in Epic 9 (Webhooks & Lifecycle).

---

## Domain 9: Documentation

### Task 8.10 — Create API Documentation

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Document session initiation API.

**Tasks:**

- Create `docs/api/session-initiation.md`:
  - Overview & architecture
  - API reference with examples
  - Integration guide for frontend
  - Troubleshooting section
- Add examples:
  - `docs/examples/session-start-curl.sh`
  - `docs/examples/session-start-python.py`
- Update main README with link

**Acceptance Criteria:**

- [ ] Documentation complete
- [ ] Examples provided (curl, Python)
- [ ] Troubleshooting guide exists
- [ ] README updated

**Dependencies:** Task 8.6

---

## Recommended Execution Order

1. **Task 8.1** — Extend Session Model
2. **Task 8.2** — Create Pydantic Schemas
3. **Task 8.3** — Room Name Generator
4. **Task 8.4** — Token Service
5. **Task 8.5** — Session Service
6. **Task 8.6** — Session Start Endpoint
7. **Task 8.7** — Query Endpoints
8. **Task 8.8** — Access Control
9. **Task 8.9** — Token Config
10. **Task 8.10** — Documentation

---

## Definition of Done

Epic 8 is complete when:

- [ ] All 10 tasks marked COMPLETED
- [ ] `POST /api/v1/sessions/start` functional
- [ ] Tokens generated with correct metadata
- [ ] Documentation complete
- [ ] No regressions in Epics 1-7
