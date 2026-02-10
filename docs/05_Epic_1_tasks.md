# Epic 1 — Development Environment & Monorepo Setup
## Task Breakdown

**Epic Summary:** Establish the foundational development environment, project structure, and monorepo configuration. This is the absolute minimum needed for any developer to clone, install, and start working on any layer of the platform.

**Layer:** Cross-Cutting
**Dependencies:** None (starting point)

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

## Domain 1: Project Structure & Configuration

### Task 1.1 — Initialize Monorepo Root Structure
**Status:** PENDING
**Estimated Effort:** S

**Description:**
Create the top-level monorepo directory structure with three main directories in the root: frontend, backend (Platform API), and agent-runtime. This flat structure reduces nesting complexity.

**Tasks:**
- Create root directory structure:
  ```
  /
  ├── frontend/          # Next.js application
  ├── backend/           # FastAPI Platform API
  ├── agent-runtime/     # LiveKit Agent Server
  ├── docs/                  # Project documentation
  ├── .github/               # GitHub workflows
  ├── docker/                # Docker configuration
  └── scripts/               # Utility scripts
  ```
- Create root `.gitignore` file with patterns for Node.js, Python, and Docker
- Create root `README.md` placeholder

**Acceptance Criteria:**
- [ ] Directory structure matches specification
- [ ] `.gitignore` properly configured
- [ ] Git repository initialized

**Dependencies:** None

---

### Task 1.2 — Configure Frontend Package Manager (pnpm)
**Status:** PENDING
**Estimated Effort:** S

**Description:**
Set up pnpm workspaces for the Next.js frontend to manage dependencies efficiently.

**Tasks:**
- Initialize `pnpm-workspace.yaml` at root
- Create `frontend/package.json`
- Configure `package.json` scripts for dev, build, lint
- Pin Node.js version using `.nvmrc` or `.node-version`

**Acceptance Criteria:**
- [ ] `pnpm install` works at root
- [ ] Frontend package is recognized as part of workspace
- [ ] Node version is pinned

**Dependencies:** Task 1.1

---

### Task 1.3 — Configure Python Package Manager (Poetry)
**Status:** PENDING
**Estimated Effort:** M

**Description:**
Set up Poetry for dependency management in the backend and agent-runtime packages.

**Tasks:**
- Initialize `pyproject.toml` in `backend`
- Initialize `pyproject.toml` in `agent-runtime`
- Configure virtual environment handling (in-project or centralized)
- Add essential dependencies:
  - Backend: `fastapi`, `uvicorn`, `python-dotenv`
  - Agent-Runtime: `livekit-agents`, `python-dotenv`

**Acceptance Criteria:**
- [ ] `poetry install` works in both Python packages
- [ ] Virtual environments created successfully
- [ ] Basic dependencies installed

**Dependencies:** Task 1.1

---

## Domain 2: Environment Variables

### Task 1.4 — Design Environment Variable Structure
**Status:** PENDING
**Estimated Effort:** S

**Description:**
Define the `.env` file structure and loading mechanism for all packages. This establishes the pattern for configuration management. Actual API keys and secrets will be added in later epics.

**Tasks:**
- Create `.env.example` files (root and/or per-package)
- Define placeholder structure with comments:
  ```
  # Database (Epic 3)
  # DATABASE_URL=postgresql://...
  # REDIS_URL=redis://...
  
  # LiveKit (Epic 2)
  # LIVEKIT_URL=ws://localhost:7880
  # LIVEKIT_API_KEY=your-key-here
  # LIVEKIT_API_SECRET=your-secret-here
  
  # AI Services (Epic 13+)
  # OPENAI_API_KEY=sk-...
  ```
- Configure `python-dotenv` loading in Python packages
- Verify Next.js auto-loads `.env.local` for frontend
- Add `.env`, `.env.local` to `.gitignore`

**Acceptance Criteria:**
- [ ] `.env.example` files present with clear structure and comments
- [ ] `python-dotenv` configured in both Python packages
- [ ] Test that env loading works (create dummy `.env.local` with `TEST_VAR=hello`, verify it loads)
- [ ] `.env*` files excluded from git (except `.env.example`)

**Dependencies:** Task 1.1

**Note:** This task sets up the infrastructure. Actual API keys will be added when needed in Epic 2 (LiveKit), Epic 3 (Database), and Epic 13 (Voice Pipeline).

---

## Domain 3: Code Quality & Standards

### Task 1.5 — Configure Linting & Formatting (Frontend)
**Status:** PENDING
**Estimated Effort:** M

**Description:**
Set up ESLint and Prettier for the frontend to enforce code style.

**Tasks:**
- Install `eslint`, `prettier`, and plugins in frontend package
- Configure `.eslintrc.json` and `.prettierrc`
- Add lint/format scripts to `package.json`

**Acceptance Criteria:**
- [ ] `pnpm lint` runs ESLint
- [ ] `pnpm format` runs Prettier
- [ ] VS Code formats on save (if configured)

**Dependencies:** Task 1.2

---

### Task 1.6 — Configure Linting & Formatting (Python)
**Status:** PENDING
**Estimated Effort:** M

**Description:**
Set up Ruff and Black for backend and agent-runtime code quality.

**Tasks:**
- Add `ruff` and `black` as dev dependencies in Poetry
- Configure `[tool.ruff]` and `[tool.black]` in `pyproject.toml`
- Add lint/format commands (via Makefile or scripts)

**Acceptance Criteria:**
- [ ] `ruff check .` runs successfully
- [ ] `black .` formats code
- [ ] Configuration is consistent across both Python packages

**Dependencies:** Task 1.3

---

### Task 1.7 — Configure Git Hooks
**Status:** PENDING
**Estimated Effort:** S

**Description:**
Install pre-commit hooks to ensure code quality before commit. This prevents broken or poorly formatted code from being committed.

**Tasks:**
- Install `pre-commit` framework
- Configure `.pre-commit-config.yaml` to run:
  - Prettier (frontend)
  - Black/Ruff (backend/agent)
  - Trailing whitespace fixer
  - End-of-file fixer
- Run `pre-commit install` to activate hooks

**Acceptance Criteria:**
- [ ] `pre-commit install` works
- [ ] Hooks run automatically on `git commit`
- [ ] Commits are blocked if linting/formatting fails
- [ ] Developers can bypass with `--no-verify` if needed (for emergencies)

**Dependencies:** Task 1.5, Task 1.6

**Note:** Commit message linting is intentionally excluded to keep Epic 1 simple. Can be added later if needed.

---

## Domain 4: Local Infrastructure

### Task 1.8 — Create Docker Compose for Local Services
**Status:** PENDING
**Estimated Effort:** M

**Description:**
Create `docker-compose.yml` to spin up necessary local services: PostgreSQL, Redis, and LiveKit (basic setup only).

**Important:** This task only sets up the containers with minimal configuration. Detailed configuration (database schema, LiveKit API keys, TURN/STUN, webhooks) happens in Epic 2 (LiveKit) and Epic 3 (Database).

**Tasks:**
- Create `docker-compose.yml` at project root
- Define `postgres` service:
  - Use official PostgreSQL image (latest or pinned version)
  - Map port 5432
  - Set basic environment variables (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)
  - Create volume for data persistence
- Define `redis` service:
  - Use official Redis image
  - Map port 6379
  - Create volume for data persistence (optional for dev)
- Define `livekit` service:
  - Use official LiveKit server image
  - Map port 7880 (WebSocket) and 7881 (HTTP)
  - **Note:** No API keys or TURN/STUN config yet (Epic 2)
- Add `docker-compose.override.yml` to `.gitignore` for local customization

**Acceptance Criteria:**
- [ ] `docker-compose up` starts all three containers without errors
- [ ] PostgreSQL is accessible on `localhost:5432`
- [ ] Redis is accessible on `localhost:6379`
- [ ] LiveKit server starts (may not be fully functional until Epic 2)
- [ ] Containers persist data via volumes
- [ ] `docker-compose down` stops all services cleanly
- [ ] README documents how to start/stop services

**Dependencies:** Task 1.1

**Note:** LiveKit will require additional configuration in Epic 2 (API key generation, webhook setup, TURN/STUN). For Epic 1, it just needs to start successfully.

---

## Domain 5: Documentation & CI

### Task 1.9 — Create Setup Documentation & Script
**Status:** PENDING
**Estimated Effort:** M

**Description:**
Create a comprehensive README and a setup script to onboard new developers quickly.

**Tasks:**
- Write root `README.md` with:
  - Prerequisites
  - Installation steps
  - Running development servers
- Create `scripts/setup.sh` to automate:
  - installing dependencies
  - copying .env examples
  - creating docker containers

**Acceptance Criteria:**
- [ ] README is accurate
- [ ] `scripts/setup.sh` runs without error on a fresh clone

**Dependencies:** Task 1.8

---

### Task 1.10 — Create CI Pipeline Skeleton
**Status:** PENDING
**Estimated Effort:** S

**Description:**
Set up the CI/CD file structure and triggers. This establishes the foundation for automated testing and deployment, which will be expanded in later epics.

**Important:** This task creates the infrastructure only. Actual linting and testing jobs will be added in Epic 4 (Platform API), Epic 22 (Frontend), and Epic 36 (Testing).

**Tasks:**
- Create `.github/workflows/ci.yml` (or equivalent for your CI platform)
- Define triggers:
  - On push to `main` and `develop` branches
  - On pull requests to `main`
- Add a single validation job that checks monorepo structure exists:
  ```yaml
  jobs:
    structure-check:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - name: Verify monorepo structure
          run: |
            echo "Checking monorepo structure..."
            test -d frontend && echo "✓ Frontend directory exists"
            test -d backend && echo "✓ Backend directory exists"
            test -d agent-runtime && echo "✓ Agent runtime directory exists"
            echo "Monorepo structure verified!"
  ```
- Add comments in the file indicating where future jobs will be added
- Document in README how to extend CI in future epics

**Acceptance Criteria:**
- [ ] `.github/workflows/ci.yml` exists and is valid YAML
- [ ] CI triggers on push to `main` branch
- [ ] CI triggers on pull requests to `main`
- [ ] Structure validation job runs and passes
- [ ] File includes comments explaining where to add future jobs
- [ ] README documents the CI setup and how to extend it

**Dependencies:** Task 1.1

**Note:** This is intentionally minimal. Real linting jobs will be added in Epic 4 when there's backend code. Real testing jobs will be added in Epic 36. This prevents false confidence from "passing" CI when there's nothing to test yet.

---

## Recommended Execution Order

1. **Task 1.1** Monorepo Structure
2. **Task 1.2** Frontend Config
3. **Task 1.3** Python Config
4. **Task 1.4** Environment Variables
5. **Task 1.5** Frontend Linting
6. **Task 1.6** Python Linting
7. **Task 1.7** Git Hooks
8. **Task 1.8** Docker Compose
9. **Task 1.9** Documentation & Script
10. **Task 1.10** CI Skeleton
