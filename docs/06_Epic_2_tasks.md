# Epic 2 — LiveKit Server Infrastructure

## Task Breakdown

**Epic Summary:** Set up the LiveKit Server — the WebRTC SFU backbone that routes all media and data between the frontend and agent runtime. This includes proper configuration with API keys, CLI tooling for debugging, webhook registration, health checks, and documentation for both local development and production readiness.

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

## Domain 1: LiveKit Server Configuration

### Task 2.1 — Create LiveKit Server Configuration File

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a proper `livekit.yaml` configuration file for the LiveKit Server with API key/secret pairs, port settings, and logging configuration. Currently, the LiveKit container in `docker-compose.yml` runs with `--dev` mode, which auto-generates ephemeral keys. This task replaces that with an explicit, reproducible configuration.

**Tasks:**

- Create `docker/livekit.yaml` configuration file with:
  - API key and secret pair (for local development, use a fixed known pair e.g., `devkey` / `devsecret`)
  - Port configuration (7880 WebSocket, 7881 HTTP API)
  - Logging level (info for dev)
  - Room configuration defaults (empty room timeout, max participants)
- Add `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` to the root `.env.example` file
- Create a `.env` file (gitignored) with the same development values

**Acceptance Criteria:**

- [ ] `docker/livekit.yaml` exists with valid LiveKit config syntax
- [ ] API key and secret are defined and not auto-generated
- [ ] `.env.example` contains `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` placeholders
- [ ] Configuration values are documented with inline comments

**Dependencies:** Epic 1 (Task 1.1, Task 1.4, Task 1.8)

---

### Task 2.2 — Update Docker Compose with LiveKit Config

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Update the existing `livekit` service in `docker-compose.yml` to use the configuration file from Task 2.1 instead of the `--dev` flag. Mount the config file as a volume and pass it as the server config.

**Tasks:**

- Remove `--dev` flag from the livekit service command
- Mount `docker/livekit.yaml` into the container
- Update command to: `--config /etc/livekit.yaml --bind 0.0.0.0`
- Add UDP port range for WebRTC media (7882/udp already mapped, verify it's sufficient for local dev)
- Add `depends_on` or startup order if needed
- Add a healthcheck to the livekit service (HTTP check on port 7881)

**Acceptance Criteria:**

- [ ] `docker-compose up livekit` starts LiveKit with the config file (not `--dev` mode)
- [ ] LiveKit logs show it loaded the API key from config (not auto-generated)
- [ ] LiveKit HTTP API is accessible on `http://localhost:7881`
- [ ] LiveKit WebSocket is accessible on `ws://localhost:7880`
- [ ] Healthcheck passes for the livekit service

**Dependencies:** Task 2.1

---

### Task 2.3 — Add LiveKit Environment Variables to Backend & Agent Runtime

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Add LiveKit connection environment variables (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`) to the backend and agent-runtime packages so they can connect to the LiveKit server. Verify that `python-dotenv` (already configured in Epic 1) loads these values correctly.

**Tasks:**

- Add LiveKit env vars to `backend/.env.example`:
  ```
  LIVEKIT_URL=ws://localhost:7880
  LIVEKIT_API_KEY=devkey
  LIVEKIT_API_SECRET=devsecret
  ```
- Add LiveKit env vars to `agent-runtime/.env.example`:
  ```
  LIVEKIT_URL=ws://localhost:7880
  LIVEKIT_API_KEY=devkey
  LIVEKIT_API_SECRET=devsecret
  ```
- Add `NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880` to `frontend/.env.example` (or `.env.local.example`)
- Create a simple validation script or config module in backend that reads and validates these vars are set (fail-fast if missing)

**Acceptance Criteria:**

- [ ] `.env.example` files in backend, agent-runtime, and frontend contain LiveKit variables
- [ ] Backend can load `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` via `python-dotenv`
- [ ] Agent-runtime can load the same variables
- [ ] Frontend can access `NEXT_PUBLIC_LIVEKIT_URL`
- [ ] Missing env vars produce a clear error message at startup

**Dependencies:** Task 2.1, Epic 1 (Task 1.4)

---

## Domain 2: Tooling & Verification

### Task 2.4 — Install & Configure LiveKit CLI

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Install the LiveKit CLI (`lk`) tool for local development and debugging. The CLI allows creating rooms, generating tokens, listing participants, and inspecting server state — essential for development without needing a full frontend or agent running.

**Tasks:**

- Document the installation steps for LiveKit CLI in the README:
  - macOS: `brew install livekit-cli`
  - Linux: download binary from GitHub releases or use the install script
- Create a `scripts/livekit-token.sh` helper script that generates a test access token using the CLI:
  ```bash
  lk token create \
    --api-key $LIVEKIT_API_KEY \
    --api-secret $LIVEKIT_API_SECRET \
    --join --room test-room --identity test-user \
    --valid-for 24h
  ```
- Verify the CLI can connect to the local LiveKit server
- Document common CLI commands for debugging (list rooms, list participants, create room)

**Acceptance Criteria:**

- [ ] README contains LiveKit CLI installation instructions for macOS and Linux
- [ ] `scripts/livekit-token.sh` generates a valid access token
- [ ] `lk room list --url http://localhost:7881 --api-key devkey --api-secret devsecret` works
- [ ] Common CLI commands are documented

**Dependencies:** Task 2.2

---

### Task 2.5 — Verify LiveKit Token Generation with Python SDK

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create a simple Python script in the backend that generates a LiveKit access token using the `livekit-api` Python SDK. This validates that the backend can create tokens programmatically — which is the foundation for Epic 8 (Session Initiation). This is NOT the final session endpoint, just a verification that the SDK + server + keys all work together.

**Tasks:**

- Install `livekit-api` package in the backend (`poetry add livekit-api`)
- Create `backend/scripts/test_token.py` script that:
  - Reads `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` from env
  - Generates a JWT access token with room join permissions
  - Prints the token to stdout
- Run the script and verify the generated token works:
  - Use `lk room join` or a LiveKit test page to validate the token connects
- Install `livekit-agents` package in agent-runtime if not already present (`poetry add livekit-agents`)
- Verify `livekit-agents` can import and connect (just import check, no full agent yet)

**Acceptance Criteria:**

- [ ] `livekit-api` is installed in backend's `pyproject.toml`
- [ ] `backend/scripts/test_token.py` generates a valid token
- [ ] Generated token can be used to join a LiveKit room (verified via CLI or Meet page)
- [ ] `livekit-agents` is installed in agent-runtime's `pyproject.toml`
- [ ] `from livekit import agents` imports successfully

**Dependencies:** Task 2.3

---

### Task 2.6 — LiveKit Server Health Check & Status Endpoint

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Set up a mechanism to verify the LiveKit server is running and healthy. This includes using the LiveKit HTTP API to check server status and creating a simple script or Makefile target to validate the entire local infrastructure is up.

**Tasks:**

- Create a `scripts/health-check.sh` script that checks all services are running:
  - PostgreSQL: `pg_isready` or TCP check on port 5433
  - Redis: `redis-cli ping` on port 6380
  - LiveKit: HTTP GET to `http://localhost:7881` (returns server info)
- Add a `make health` target to the Makefile that runs the health check script
- Document the expected output when all services are healthy

**Acceptance Criteria:**

- [ ] `scripts/health-check.sh` checks all three services (postgres, redis, livekit)
- [ ] Script exits with code 0 when all services are healthy, non-zero otherwise
- [ ] `make health` runs the health check
- [ ] Output clearly shows which services are up/down

**Dependencies:** Task 2.2

---

## Domain 3: Webhook & Documentation

### Task 2.7 — Configure LiveKit Webhook Endpoint

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Configure the LiveKit server to send webhook events (e.g., `room_started`, `room_finished`, `participant_joined`, `participant_left`) to the Platform API. For now, this is configuration only — the actual webhook handler endpoint will be built in Epic 9. We just need to register the webhook URL in the LiveKit config.

**Tasks:**

- Update `docker/livekit.yaml` to include webhook configuration:
  ```yaml
  webhook:
    urls:
      - http://host.docker.internal:8000/api/webhooks/livekit
    api_key: devkey
  ```
- Document that the webhook URL assumes the backend (FastAPI) will run on port 8000
- Add a note in the config explaining that `host.docker.internal` is used because LiveKit runs in Docker but the backend runs on the host during development
- Document the webhook event types that LiveKit sends (`room_started`, `room_finished`, `participant_joined`, `participant_left`, `track_published`, `track_unpublished`)

**Acceptance Criteria:**

- [ ] `docker/livekit.yaml` has webhook section configured
- [ ] Webhook URL points to the backend's expected webhook endpoint
- [ ] Configuration includes comments explaining the `host.docker.internal` usage
- [ ] Webhook event types are documented

**Dependencies:** Task 2.1

**Note:** The actual webhook handler endpoint (`POST /api/webhooks/livekit`) will be implemented in Epic 9. This task only configures the LiveKit server to know WHERE to send events.

---

### Task 2.8 — LiveKit Documentation & Compatibility Matrix

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create comprehensive documentation for the LiveKit setup, including SDK version compatibility, architecture decisions (self-hosted vs Cloud), and a developer guide for working with LiveKit locally.

**Tasks:**

- Add a `docs/livekit-setup.md` document covering:
  - Local development setup (docker-compose based)
  - LiveKit Server version pinned in docker-compose (replace `latest` with a specific version tag)
  - SDK version compatibility matrix:
    - `livekit-server` version
    - `livekit-api` Python SDK version (backend)
    - `livekit-agents` Python SDK version (agent-runtime)
    - `livekit-client` JS SDK version (frontend — to be installed in Epic 23, record expected version)
  - LiveKit Cloud vs Self-Hosted: brief evaluation noting that Cloud can be used as an alternative for production
  - Network considerations for production (TURN/STUN setup, firewall rules) — notes only, implementation deferred
  - Common troubleshooting steps (port conflicts, container not starting, token errors)
- Pin the LiveKit server image version in `docker-compose.yml` (e.g., `livekit/livekit-server:v1.8.3` instead of `latest`)
- Update root `README.md` to reference the new LiveKit docs

**Acceptance Criteria:**

- [ ] `docs/livekit-setup.md` exists with all sections listed above
- [ ] LiveKit server image is pinned to a specific version (not `latest`)
- [ ] SDK compatibility matrix lists all four SDK packages with versions
- [ ] LiveKit Cloud evaluation section exists (brief, decision-making reference)
- [ ] Root README links to the LiveKit setup document
- [ ] Troubleshooting section covers at least 3 common issues

**Dependencies:** Task 2.5

---

## Recommended Execution Order

1. **Task 2.1** Create LiveKit Config File
2. **Task 2.2** Update Docker Compose
3. **Task 2.7** Configure Webhook Endpoint (config-only)
4. **Task 2.3** Add Env Vars to Backend & Agent Runtime
5. **Task 2.4** Install & Configure LiveKit CLI
6. **Task 2.5** Verify Token Generation with Python SDK
7. **Task 2.6** Health Check & Status Endpoint
8. **Task 2.8** Documentation & Compatibility Matrix
