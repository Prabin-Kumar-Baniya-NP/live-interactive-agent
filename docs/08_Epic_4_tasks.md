# Epic 4 — Platform API Foundation (FastAPI)

## Task Breakdown

**Epic Summary:** Build the FastAPI application skeleton — the platform's central API that handles authentication, configuration management, and acts as the bridge between the dashboard and the agent runtime. This epic sets up the application structure, startup/shutdown lifecycle, middleware, error handling, logging, API versioning, and base schemas. It does NOT implement authentication (Epic 5), agent CRUD (Epic 6), or any business logic — only the foundational framework that those epics build on top of.

**Layer:** Platform API
**Dependencies:** Epic 1 (Development Environment & Monorepo Setup), Epic 3 (Database & Cache Layer Setup)

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

## Domain 1: Application Structure & Entrypoint

### Task 4.1 — Create FastAPI Project Directory Structure

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Organize the backend `app/` directory into a clean, layered structure that separates concerns: API routes, business logic, data schemas, middleware, and utilities. The `db/`, `models/`, and `cache/` directories already exist from Epic 3 — this task adds the remaining directories needed for a complete API application.

**Tasks:**

- Create the following directory structure inside `backend/app/`:
  ```
  backend/app/
  ├── __init__.py          # (exists)
  ├── api/
  │   ├── __init__.py
  │   └── v1/
  │       ├── __init__.py
  │       └── health.py        # Health check endpoint (Task 4.4)
  ├── core/
  │   ├── __init__.py
  │   ├── config.py            # App settings (Task 4.2)
  │   └── logging.py           # Logging setup (Task 4.6)
  ├── middleware/
  │   ├── __init__.py
  │   └── cors.py              # CORS middleware (Task 4.5)
  ├── schemas/
  │   ├── __init__.py
  │   └── base.py              # Base Pydantic schemas (Task 4.8)
  ├── exceptions/
  │   ├── __init__.py
  │   └── handlers.py          # Exception handlers (Task 4.5)
  ├── db/                      # (exists from Epic 3)
  ├── models/                  # (exists from Epic 3)
  └── cache/                   # (exists from Epic 3)
  ```
- Add `__init__.py` files to all new directories
- Do NOT create any business logic or endpoints yet (those come in later tasks)

**Acceptance Criteria:**

- [ ] All directories listed above exist with `__init__.py` files
- [ ] Existing `db/`, `models/`, `cache/` directories are untouched
- [ ] No import errors when running `python -c "import app.api; import app.api.v1; import app.core; import app.middleware; import app.schemas; import app.exceptions"`

**Dependencies:** Epic 3

---

### Task 4.2 — Create Application Settings Module (Pydantic Settings)

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a centralized settings module using Pydantic's `BaseSettings` that loads all configuration from environment variables. This replaces scattered `os.getenv()` calls with a single, validated, typed settings object. Add `pydantic-settings` as a dependency.

**Tasks:**

- Add `pydantic-settings` to `backend/pyproject.toml` via Poetry
- Create `backend/app/core/config.py` with a `Settings` class:
  - `PROJECT_NAME: str = "Live Interactive Agent"`
  - `API_V1_PREFIX: str = "/api/v1"`
  - `DEBUG: bool = False`
  - `DATABASE_URL: str` (loaded from env, required)
  - `REDIS_URL: str` (loaded from env, required)
  - `LIVEKIT_URL: str` (loaded from env, required)
  - `LIVEKIT_API_KEY: str` (loaded from env, required)
  - `LIVEKIT_API_SECRET: str` (loaded from env, required)
  - `CORS_ORIGINS: list[str] = ["http://localhost:3000"]`
- Create a module-level `settings = Settings()` instance for importing throughout the app
- Update `backend/.env.example` if any new variables are needed

**Acceptance Criteria:**

- [ ] `pydantic-settings` is in `backend/pyproject.toml`
- [ ] `backend/app/core/config.py` exists with `Settings` class
- [ ] Settings loads values from `.env` file using Pydantic's env loading
- [ ] Missing required env vars produce a clear validation error at startup
- [ ] `from app.core.config import settings` works and returns populated settings

**Dependencies:** Task 4.1

---

### Task 4.3 — Create FastAPI Application Factory & Entrypoint

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the main FastAPI application instance using an application factory pattern. This includes startup/shutdown lifecycle hooks that initialize and tear down the database connection pool and Redis connection. Create the `main.py` entrypoint that uvicorn uses to run the app.

**Tasks:**

- Create `backend/app/main.py` with:
  - A `create_app()` factory function that:
    - Creates the `FastAPI` instance with `title`, `version`, `docs_url`, `openapi_url` from settings
    - Registers `lifespan` context manager for startup/shutdown events
    - Includes API routers (v1 router)
    - Adds middleware (CORS, etc. — wired in Task 4.5)
    - Returns the `app` instance
  - A module-level `app = create_app()` for uvicorn
- In the lifespan context manager:
  - **Startup:** Initialize the database engine/pool (using the existing `session.py` from Epic 3), initialize Redis connection
  - **Shutdown:** Dispose the database engine, close Redis connection
- Update `backend/pyproject.toml` scripts or document in README how to run:
  ```bash
  cd backend
  uvicorn app.main:app --reload --port 8000
  ```

**Acceptance Criteria:**

- [ ] `backend/app/main.py` exists with `create_app()` function
- [ ] `uvicorn app.main:app --reload --port 8000` starts the server without errors
- [ ] Server starts up and logs "startup" events (DB connection, Redis connection)
- [ ] Server shutdown cleanly disposes connections
- [ ] Visiting `http://localhost:8000/docs` shows the Swagger UI (empty, but working)

**Dependencies:** Task 4.2

---

## Domain 2: Health Check & Core Endpoints

### Task 4.4 — Create Health Check & Status Endpoints

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create health check endpoints that verify the API server and its dependencies (database, Redis) are working. These are essential for monitoring and load balancer integration.

**Tasks:**

- Create `backend/app/api/v1/health.py` with two endpoints:
  - `GET /api/v1/health` — Basic liveness check. Returns `{"status": "ok"}`. No dependency checks.
  - `GET /api/v1/health/ready` — Readiness check. Verifies database and Redis connectivity. Returns:
    ```json
    {
      "status": "ok",
      "database": "connected",
      "redis": "connected"
    }
    ```
    If any dependency is down, returns HTTP 503 with the failed dependency status.
- Create `backend/app/api/v1/router.py` — the v1 API router that includes all v1 endpoint routers
- Wire the v1 router into the main app in `main.py` with the prefix from settings (`/api/v1`)

**Acceptance Criteria:**

- [ ] `GET /api/v1/health` returns `200 {"status": "ok"}`
- [ ] `GET /api/v1/health/ready` returns `200` with database and redis status when all services are up
- [ ] `GET /api/v1/health/ready` returns `503` when database or Redis is down
- [ ] Endpoints are visible in Swagger UI at `/docs`

**Dependencies:** Task 4.3

---

## Domain 3: Middleware & Error Handling

### Task 4.5 — Configure CORS & Request Middleware

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Add CORS middleware to allow the frontend (running on `localhost:3000`) to make API calls to the backend (running on `localhost:8000`). Configure additional request middleware as needed.

**Tasks:**

- Create `backend/app/middleware/cors.py` with a function to configure CORS:
  - `allow_origins` from `settings.CORS_ORIGINS`
  - `allow_methods` — `["*"]`
  - `allow_headers` — `["*"]`
  - `allow_credentials` — `True`
- Wire the CORS middleware into the app factory in `main.py`
- Add `request_id` middleware — generate a unique UUID for each request and include it in logs and response headers (`X-Request-ID`). This aids debugging.

**Acceptance Criteria:**

- [ ] Frontend on `localhost:3000` can make API calls to backend on `localhost:8000` without CORS errors
- [ ] `OPTIONS` preflight requests return correct CORS headers
- [ ] Every response includes an `X-Request-ID` header
- [ ] CORS origins are configurable via environment variables

**Dependencies:** Task 4.3

---

### Task 4.6 — Set Up Structured JSON Logging

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Configure structured JSON logging for the backend API. All log output should be machine-parseable JSON with consistent fields (timestamp, level, message, request_id). This replaces the default uvicorn text logging.

**Tasks:**

- Create `backend/app/core/logging.py` with a function to configure logging:
  - Use Python's `logging` module with a JSON formatter
  - Log format should include: `timestamp`, `level`, `message`, `module`, `request_id` (when available)
  - Configure log level based on `settings.DEBUG` (DEBUG in dev, INFO in production)
- Add a logging dependency (either `python-json-logger` or a simple custom JSON formatter — keep it minimal)
- Call the logging setup function during app startup (in the lifespan)
- Replace any `print()` statements in existing code with proper `logger` calls

**Acceptance Criteria:**

- [ ] All log output is structured JSON (one JSON object per line)
- [ ] Logs include `timestamp`, `level`, `message` fields
- [ ] Log level is DEBUG when `DEBUG=True`, INFO otherwise
- [ ] `from app.core.logging import setup_logging` works
- [ ] No `print()` statements used for logging in the backend

**Dependencies:** Task 4.2

---

### Task 4.7 — Create Error Handling Framework

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Build a consistent error handling framework with custom exception classes and FastAPI exception handlers. All API errors should return a structured JSON response with a consistent format.

**Tasks:**

- Create custom exception classes in `backend/app/exceptions/`:
  - `AppException` — base exception with `status_code`, `detail`, `error_code` fields
  - `NotFoundException` — 404 errors (e.g., resource not found)
  - `BadRequestException` — 400 errors (e.g., validation failed)
  - `ForbiddenException` — 403 errors (e.g., insufficient permissions)
  - `InternalServerException` — 500 errors
- Create exception handlers in `backend/app/exceptions/handlers.py`:
  - Handler for `AppException` — returns structured JSON: `{"error": {"code": "...", "message": "...", "details": ...}}`
  - Handler for `RequestValidationError` (Pydantic validation fails) — returns 422 with structured field errors
  - Handler for unhandled exceptions (catch-all) — returns 500 with generic message, logs the full traceback
- Register all exception handlers in the app factory

**Acceptance Criteria:**

- [ ] Custom exception classes exist and are importable
- [ ] Raising `NotFoundException("User not found")` in an endpoint returns `404 {"error": {"code": "not_found", "message": "User not found"}}`
- [ ] Pydantic validation errors return a structured 422 response
- [ ] Unhandled exceptions return a generic 500 response (no stack trace leaked to client)
- [ ] Unhandled exceptions are logged with full traceback on the server

**Dependencies:** Task 4.3

---

## Domain 4: Schemas & API Documentation

### Task 4.8 — Define Base Pydantic Schemas

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create base Pydantic models (schemas) that other epics will extend. These provide consistent patterns for request/response serialization across all endpoints.

**Tasks:**

- Create `backend/app/schemas/base.py` with:
  - `BaseSchema` — base class with `model_config` for ORM mode (`from_attributes = True`)
  - `TimestampSchema` — mixin adding `created_at` and `updated_at` fields
  - `PaginatedResponse` — generic paginated response schema with `items`, `total`, `page`, `page_size`
  - `ErrorResponse` — schema matching the error format from Task 4.7
- Create `backend/app/schemas/health.py`:
  - `HealthResponse` — schema for the health check response
  - `ReadinessResponse` — schema for the readiness check response
- Apply health schemas to the health check endpoints from Task 4.4 (as `response_model`)

**Acceptance Criteria:**

- [ ] `BaseSchema`, `TimestampSchema`, `PaginatedResponse`, `ErrorResponse` are defined and importable
- [ ] Health check endpoints use `response_model` for Swagger documentation
- [ ] Swagger UI at `/docs` shows typed request/response schemas for health endpoints
- [ ] `PaginatedResponse` is generic and can be used with any item type

**Dependencies:** Task 4.4, Task 4.7

---

### Task 4.9 — Verify OpenAPI/Swagger Documentation

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Verify that the auto-generated OpenAPI documentation is properly configured, accessible, and includes all endpoints with correct schemas. Customize the Swagger UI metadata.

**Tasks:**

- Ensure the FastAPI app is configured with:
  - `title` — "Live Interactive Agent API"
  - `description` — Brief API description
  - `version` — "0.1.0"
  - `docs_url` — `/docs` (Swagger UI)
  - `redoc_url` — `/redoc` (ReDoc alternative)
  - `openapi_url` — `/openapi.json`
- Verify that all registered endpoints appear in the Swagger UI
- Verify that all response schemas are correctly documented
- Add API tags for organizing endpoints in Swagger (e.g., `health` tag for health endpoints)

**Acceptance Criteria:**

- [ ] `http://localhost:8000/docs` shows Swagger UI with correct title and description
- [ ] `http://localhost:8000/redoc` shows ReDoc documentation
- [ ] `http://localhost:8000/openapi.json` returns the OpenAPI spec JSON
- [ ] Health check endpoints are grouped under a "health" tag
- [ ] Response schemas are visible for all endpoints

**Dependencies:** Task 4.8

---

### Task 4.10 — Add Development Run Script & Update Documentation

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Add convenience scripts and update documentation so developers can easily run the backend API during development.

**Tasks:**

- Add a Makefile target: `make api` that runs:
  ```bash
  cd backend && poetry run uvicorn app.main:app --reload --port 8000
  ```
- Update the root `README.md` with:
  - How to start the backend API (`make api` or manual uvicorn command)
  - Available API endpoints (health check)
  - Link to Swagger UI (`http://localhost:8000/docs`)
- Update `backend/README.md` with:
  - Backend-specific development instructions
  - Project structure overview (explaining each directory's purpose)
  - How to add new endpoints (brief guide for future epics)

**Acceptance Criteria:**

- [ ] `make api` starts the backend server on port 8000
- [ ] Root README documents how to start the backend
- [ ] Backend README documents the project structure
- [ ] A developer can follow the README to start the API from a fresh clone

**Dependencies:** Task 4.9

---

## Recommended Execution Order

1. **Task 4.1** Create Project Directory Structure
2. **Task 4.2** Create Application Settings Module
3. **Task 4.6** Set Up Structured JSON Logging
4. **Task 4.3** Create Application Factory & Entrypoint
5. **Task 4.5** Configure CORS & Request Middleware
6. **Task 4.7** Create Error Handling Framework
7. **Task 4.4** Create Health Check & Status Endpoints
8. **Task 4.8** Define Base Pydantic Schemas
9. **Task 4.9** Verify OpenAPI/Swagger Documentation
10. **Task 4.10** Add Development Run Script & Update Documentation
