# Epic 3 — Database & Cache Layer Setup

## Task Breakdown

**Epic Summary:** Set up PostgreSQL as the primary relational data store and Redis as the ephemeral cache/session store. Define the foundational schema, migration tooling, and connection pooling. PostgreSQL and Redis are running locally on the machine (PostgreSQL on port `5432`, Redis on port `6379`). This epic focuses on the application-level database layer — ORM setup, migration framework, initial schema, connection utilities, and development tooling.

**Local Database Credentials (already created):**

- **PostgreSQL:** `localhost:5432` — User: `liveinteractiveagent`, Password: `vibecoding123`, Database: `liveinteractiveagentdb`
- **Redis:** `localhost:6379` (default, no auth)

**Layer:** Infrastructure
**Dependencies:** Epic 1 (Development Environment & Monorepo Setup)

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

## Domain 1: ORM & Migration Tooling

### Task 3.1 — Install SQLAlchemy & Alembic in Backend

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Install SQLAlchemy (async version) and Alembic in the backend package. These are the ORM and migration tools that the Platform API will use to interact with PostgreSQL. This task sets up the packages only — no models or migrations yet.

**Tasks:**

- Add dependencies to `backend/pyproject.toml` via Poetry:
  - `sqlalchemy[asyncio]` — async ORM
  - `asyncpg` — async PostgreSQL driver
  - `alembic` — database migration tool
- Run `poetry install` to install dependencies
- Verify imports work: `import sqlalchemy`, `import alembic`, `import asyncpg`

**Acceptance Criteria:**

- [ ] `sqlalchemy`, `asyncpg`, and `alembic` are listed in `backend/pyproject.toml`
- [ ] `poetry install` completes without errors
- [ ] `python -c "import sqlalchemy; import alembic; import asyncpg"` runs successfully in the backend venv

**Dependencies:** Epic 1 (Task 1.3)

---

### Task 3.2 — Initialize Alembic Migration Environment

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Initialize Alembic inside the backend package and configure it to work with SQLAlchemy's async engine and the project's environment variable structure. This creates the migration framework that all future schema changes will use.

**Tasks:**

- Run `alembic init` inside the `backend/` directory to generate the Alembic folder structure:
  ```
  backend/
  ├── alembic/
  │   ├── versions/       # Migration scripts go here
  │   ├── env.py          # Migration runtime config
  │   └── script.py.mako  # Migration template
  └── alembic.ini         # Alembic configuration
  ```
- Update `alembic.ini`:
  - Remove the hardcoded `sqlalchemy.url` (we load from env vars instead)
- Update `alembic/env.py`:
  - Load `DATABASE_URL` from environment variables using `python-dotenv`
  - Configure async engine support (use `run_async_migrations` pattern)
  - Import the SQLAlchemy `Base` metadata for autogeneration support
- Add `DATABASE_URL` to `backend/.env.example`:
  ```
  DATABASE_URL=postgresql+asyncpg://liveinteractiveagent:vibecoding123@localhost:5432/liveinteractiveagentdb
  ```
- Add `DATABASE_URL` to `backend/.env` (gitignored) with the same local dev value

**Acceptance Criteria:**

- [ ] `backend/alembic/` directory exists with `env.py`, `script.py.mako`, and `versions/`
- [ ] `alembic.ini` exists in `backend/`
- [ ] `env.py` loads `DATABASE_URL` from environment variables
- [ ] `env.py` is configured for async SQLAlchemy engine
- [ ] `DATABASE_URL` is in `backend/.env.example`
- [ ] Running `alembic current` from `backend/` connects to the local PostgreSQL database successfully (shows no migrations applied)

**Dependencies:** Task 3.1

---

### Task 3.3 — Create SQLAlchemy Base & Database Engine Module

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the database module in the backend that defines the SQLAlchemy async engine, session factory, and base model class. This module is the single source of truth for all database connectivity in the Platform API.

**Tasks:**

- Create `backend/app/` directory structure (if not already present):
  ```
  backend/app/
  ├── __init__.py
  └── db/
      ├── __init__.py
      ├── base.py       # Base model class
      └── session.py    # Engine & session factory
  ```
- In `base.py`:
  - Define `Base = declarative_base()` (SQLAlchemy's declarative base)
  - This is what all models will inherit from
- In `session.py`:
  - Create async engine using `create_async_engine()` with `DATABASE_URL` from env
  - Create `async_sessionmaker` for producing async sessions
  - Create a `get_db()` async generator (FastAPI dependency pattern) that yields a session and handles commit/rollback
- Update `alembic/env.py` to import `Base.metadata` from `app.db.base` for autogeneration

**Acceptance Criteria:**

- [ ] `backend/app/db/base.py` exists with `Base` declarative base
- [ ] `backend/app/db/session.py` exists with async engine and session factory
- [ ] `get_db()` dependency function is defined and yields an async session
- [ ] Alembic's `env.py` imports `Base.metadata` for migration autogeneration
- [ ] A simple test script can create an engine and connect to PostgreSQL using the async driver

**Dependencies:** Task 3.2

---

## Domain 2: Initial Schema & Migrations

### Task 3.4 — Define Initial Database Models (Users, Organizations, Sessions)

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Define the foundational SQLAlchemy ORM models for `users`, `organizations`, and `sessions`. These are the core tables that the Platform API needs from Epic 4 onwards. Keep the schema minimal — include only what's needed for the foundation. Additional columns and tables will be added in later epics.

**Tasks:**

- Create `backend/app/models/` directory:
  ```
  backend/app/models/
  ├── __init__.py
  ├── user.py
  ├── organization.py
  └── session.py
  ```
- Define `Organization` model (`organizations` table):
  - `id` — UUID, primary key
  - `name` — String, not null
  - `created_at` — DateTime, default now
  - `updated_at` — DateTime, on update now
- Define `User` model (`users` table):
  - `id` — UUID, primary key
  - `email` — String, unique, not null
  - `hashed_password` — String, not null
  - `full_name` — String, nullable
  - `organization_id` — FK to `organizations.id`
  - `role` — String, default "member" (values: admin, member, viewer)
  - `is_active` — Boolean, default True
  - `created_at` — DateTime, default now
  - `updated_at` — DateTime, on update now
- Define `Session` model (`sessions` table):
  - `id` — UUID, primary key
  - `organization_id` — FK to `organizations.id`
  - `room_name` — String, unique, not null
  - `status` — String, default "pending" (values: pending, active, completed, error)
  - `started_at` — DateTime, nullable
  - `ended_at` — DateTime, nullable
  - `created_at` — DateTime, default now
- Import all models in `backend/app/models/__init__.py` to ensure they are registered with `Base.metadata`

**Acceptance Criteria:**

- [ ] `Organization`, `User`, and `Session` models are defined with the columns listed above
- [ ] All models inherit from `Base`
- [ ] Foreign key relationships are defined (User → Organization, Session → Organization)
- [ ] Models are importable from `backend/app/models`
- [ ] `python -c "from app.models import User, Organization, Session"` works in backend venv

**Dependencies:** Task 3.3

---

### Task 3.5 — Generate & Run Initial Alembic Migration

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Use Alembic's autogeneration feature to create the first migration from the models defined in Task 3.4, and run it against the local PostgreSQL database. This creates the actual tables in the database.

**Tasks:**

- Generate the initial migration:
  ```bash
  cd backend
  alembic revision --autogenerate -m "initial_schema_users_orgs_sessions"
  ```
- Review the generated migration file in `alembic/versions/` to verify it creates the correct tables
- Run the migration:
  ```bash
  alembic upgrade head
  ```
- Verify the tables exist in the database using `psql` or a simple Python script:
  ```bash
  psql -h localhost -p 5432 -U liveinteractiveagent -d liveinteractiveagentdb -c "\dt"
  ```
- Verify downgrade works:
  ```bash
  alembic downgrade base
  alembic upgrade head
  ```

**Acceptance Criteria:**

- [ ] Migration file exists in `backend/alembic/versions/`
- [ ] `alembic upgrade head` runs without errors
- [ ] Tables `users`, `organizations`, `sessions`, and `alembic_version` exist in the database
- [ ] `alembic downgrade base` drops the tables successfully
- [ ] `alembic upgrade head` re-creates them successfully (reversible)

**Dependencies:** Task 3.4

---

## Domain 3: Redis Connection Utilities

### Task 3.6 — Create Redis Connection Module

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the Redis connection module in the backend that provides an async Redis client for caching and session state. This uses the `redis` Python library (async mode) to connect to the Redis instance running in Docker.

**Tasks:**

- Add `redis[hiredis]` as a dependency in `backend/pyproject.toml` via Poetry (`hiredis` is the C parser for better performance)
- Create `backend/app/cache/` directory:
  ```
  backend/app/cache/
  ├── __init__.py
  └── redis.py
  ```
- In `redis.py`:
  - Create a function to initialize the async Redis client using `REDIS_URL` from env
  - Create a `get_redis()` async dependency for FastAPI (similar pattern to `get_db()`)
  - Include a health check utility function (`ping()` to verify connection)
- Add `REDIS_URL` to `backend/.env.example`:
  ```
  REDIS_URL=redis://localhost:6379/0
  ```
- Add `REDIS_URL` to `backend/.env` (gitignored) with the same local dev value
- Create a simple test script to verify Redis connectivity:
  ```bash
  python -c "import asyncio; from app.cache.redis import get_redis_client; ..."
  ```

**Acceptance Criteria:**

- [ ] `redis[hiredis]` is in `backend/pyproject.toml`
- [ ] `backend/app/cache/redis.py` exists with async Redis client setup
- [ ] `get_redis()` dependency function is defined
- [ ] `REDIS_URL` is in `backend/.env.example`
- [ ] A test script can connect to Redis and run `PING` successfully
- [ ] Connection errors produce a clear error message

**Dependencies:** Epic 1 (Task 1.3, Task 1.8)

---

## Domain 4: Development Tooling & Documentation

### Task 3.7 — Create Database Seeding Script

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create a seed script that populates the database with sample development data — a test organization and test user. This makes it easy for any developer to have working data immediately after setting up the project.

**Tasks:**

- Create `backend/scripts/seed.py`:
  - Insert a default organization (e.g., name: "Test Organization")
  - Insert a default user (e.g., email: "admin@test.com", password: hashed "password123", role: "admin", linked to the test org)
  - Script should be idempotent (skip if data already exists, don't duplicate)
- Add `bcrypt` as a dependency in `backend/pyproject.toml` for password hashing (will be needed in Epic 5 anyway)
- The script should:
  - Load env vars and connect to the database
  - Check if seed data already exists before inserting
  - Print clear output of what was created or skipped
- Add a Makefile target: `make seed` that runs the seed script

**Acceptance Criteria:**

- [ ] `backend/scripts/seed.py` exists and runs without errors
- [ ] Running the script creates a test organization and test user in the database
- [ ] Running the script a second time does not create duplicates (idempotent)
- [ ] `make seed` runs the seed script
- [ ] Seeded user has a properly hashed password (not plaintext)

**Dependencies:** Task 3.5

---

### Task 3.8 — Database Documentation & Backup Strategy

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Document the database setup, schema, common Alembic commands, and backup/restore strategy for development. This ensures any developer can work with the database layer without guesswork.

**Tasks:**

- Update `README.md` (root or backend) with a database section covering:
  - Database credentials and connection info (local PostgreSQL on port 5432, Redis on port 6379)
  - How to run migrations (`alembic upgrade head`)
  - How to create new migrations (`alembic revision --autogenerate -m "description"`)
  - How to rollback migrations (`alembic downgrade -1`)
  - How to seed the database (`make seed`)
  - How to connect to the database directly (`psql -h localhost -p 5432 -U liveinteractiveagent -d liveinteractiveagentdb`)
  - How to connect to Redis directly (`redis-cli` — default port 6379)
- Document backup/restore for local development:
  - Backup: `pg_dump -h localhost -p 5432 -U liveinteractiveagent liveinteractiveagentdb > backup.sql`
  - Restore: `psql -h localhost -p 5432 -U liveinteractiveagent liveinteractiveagentdb < backup.sql`
- Document the initial schema (table names, columns, relationships) in a brief summary

**Acceptance Criteria:**

- [ ] README contains database setup and migration commands
- [ ] Common Alembic commands are documented
- [ ] Backup and restore commands are documented
- [ ] Schema summary is documented (tables and their purpose)
- [ ] Redis connection instructions are documented
- [ ] A new developer can follow the README to set up the database from scratch

**Dependencies:** Task 3.7

---

## Recommended Execution Order

1. **Task 3.1** Install SQLAlchemy & Alembic
2. **Task 3.2** Initialize Alembic Migration Environment
3. **Task 3.3** Create SQLAlchemy Base & Database Engine Module
4. **Task 3.4** Define Initial Database Models
5. **Task 3.5** Generate & Run Initial Migration
6. **Task 3.6** Create Redis Connection Module
7. **Task 3.7** Create Database Seeding Script
8. **Task 3.8** Database Documentation & Backup Strategy
