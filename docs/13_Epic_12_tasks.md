# Epic 12 — Agent Runtime Foundation

## Task Breakdown

**Epic Summary:** Set up the LiveKit Agent Server — the Python process that registers with the LiveKit Server and handles room dispatch. This is the foundational runtime that all agent logic runs inside. This epic covers SDK installation, project structure, the agent server entrypoint, environment configuration, logging, room event boilerplate, graceful shutdown, and the local development workflow — NOT the voice pipeline (Epic 13), agent implementation (Epic 14), dynamic config loading (Epic 16), or session lifecycle management (Epic 21).

**Layer:** Agent Runtime
**Dependencies:** Epic 2 (LiveKit Server Infrastructure), Epic 4 (Platform API Foundation)

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

## Domain 1: SDK Dependencies & Project Structure

### Task 12.1 — Install LiveKit Agents SDK & Plugin Dependencies

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Update the `agent-runtime/pyproject.toml` to include the full set of `livekit-agents` SDK dependencies and essential plugins needed for the runtime foundation. The `livekit-agents` package is already listed but needs to be pinned properly. Add the plugin packages that the runtime will need (STT, TTS, LLM, VAD) so they are available for Epic 13. Also add `httpx` for async HTTP calls to the Platform API and `pydantic-settings` for configuration management.

**Tasks:**

- Update `agent-runtime/pyproject.toml` dependencies:
  - Pin `livekit-agents` to a stable version range (e.g., `^1.0.0` or `>=1.0.0`)
  - Add `livekit-plugins-deepgram` (STT)
  - Add `livekit-plugins-openai` (LLM)
  - Add `livekit-plugins-cartesia` (TTS)
  - Add `livekit-plugins-silero` (VAD)
  - Add `httpx` for async HTTP client
  - Add `pydantic-settings` for configuration management
- Run `poetry lock && poetry install` to install all dependencies
- Verify all packages import successfully

**Acceptance Criteria:**

- [ ] `pyproject.toml` includes all listed dependencies
- [ ] `poetry install` completes without errors
- [ ] `python -c "from livekit import agents; print('ok')"` succeeds
- [ ] `python -c "from livekit.plugins import deepgram, openai, cartesia, silero; print('ok')"` succeeds
- [ ] `python -c "import httpx, pydantic_settings; print('ok')"` succeeds

**Dependencies:** Epic 1 (Poetry configured for agent-runtime)

---

### Task 12.2 — Create Agent Runtime Project Structure

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create the directory structure for the agent runtime following Python package conventions. The structure should mirror the backend's organization where applicable (config, logging) while being tailored for the LiveKit agent server use case.

**Tasks:**

- Create the following directory structure under `agent-runtime/`:
  ```
  agent-runtime/
  ├── agents/                    # Agent definitions (Epic 14+)
  ├── config/
  │   ├── __init__.py
  │   └── settings.py            # Pydantic settings for runtime config
  ├── core/
  │   ├── __init__.py
  │   └── logging.py             # Structured logging setup
  ├── services/                  # Service modules (Epic 16+)
  │   └── __init__.py
  ├── utils/                     # Utility functions
  │   └── __init__.py
  ├── main.py                    # Agent server entrypoint
  └── __init__.py
  ```
- Create empty `__init__.py` files in each directory
- Ensure the structure is importable (no circular imports)

**Acceptance Criteria:**

- [ ] All directories and `__init__.py` files exist
- [ ] `config/`, `core/`, `services/`, `utils/` directories created
- [ ] `agents/` directory exists (empty, placeholder for Epic 14)
- [ ] `main.py` exists at the root of `agent-runtime/`
- [ ] No import errors when running `python -c "import config; import core; import utils"`

**Dependencies:** Task 12.1

---

## Domain 2: Configuration

### Task 12.3 — Create Runtime Configuration Module

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a Pydantic-based settings module for the agent runtime, following the same pattern as the backend's `app/core/config.py`. This centralizes all environment variable loading and provides type-safe access to configuration values.

**Tasks:**

- Create `agent-runtime/config/settings.py`:
  - Define `RuntimeSettings(BaseSettings)` class with:
    - `LIVEKIT_URL: str` — LiveKit server WebSocket URL (e.g., `ws://localhost:7880`)
    - `LIVEKIT_API_KEY: str` — LiveKit API key
    - `LIVEKIT_API_SECRET: str` — LiveKit API secret
    - `PLATFORM_API_URL: str` — Platform API base URL (default: `http://localhost:8000`)
    - `LOG_LEVEL: str` — Logging level (default: `INFO`)
    - `WORKER_NUM_IDLE_PROCESSES: int` — Number of idle worker processes (default: `3`)
  - Use `SettingsConfigDict` with `env_file=".env"` and `case_sensitive=True`
  - Instantiate a module-level `settings` object
- Update `agent-runtime/.env.example`:
  - Add all configuration variables with sensible defaults and comments
- Update `agent-runtime/.env`:
  - Add local development values matching docker-compose

**Acceptance Criteria:**

- [ ] `config/settings.py` exists with `RuntimeSettings` class
- [ ] All LiveKit connection settings are defined (URL, API key, API secret)
- [ ] `PLATFORM_API_URL` defaults to `http://localhost:8000`
- [ ] `LOG_LEVEL` defaults to `INFO`
- [ ] `settings` object loads from `.env` file
- [ ] `.env.example` documents all configuration variables
- [ ] `from config.settings import settings` works without error

**Dependencies:** Task 12.2

---

## Domain 3: Logging

### Task 12.4 — Set Up Structured Logging for Agent Runtime

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Set up structured logging for the agent runtime, compatible with the platform's logging approach. The LiveKit agents SDK has its own logging integration, so this task configures Python's standard `logging` module to work alongside it with structured JSON output and appropriate log levels.

**Tasks:**

- Create `agent-runtime/core/logging.py`:
  - Function `setup_logging(log_level: str = "INFO") -> None`:
    - Configure root logger with the specified level
    - Set up a `logging.StreamHandler` with structured output format
    - Format: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`
    - Suppress noisy third-party loggers (e.g., `httpx`, `httpcore`) to `WARNING`
    - Configure the `livekit` logger to respect the configured level
  - Module-level helper `get_logger(name: str) -> logging.Logger` for convenience
- Call `setup_logging()` from the entrypoint before starting the agent server

**Acceptance Criteria:**

- [ ] `core/logging.py` exists with `setup_logging()` and `get_logger()` functions
- [ ] Log output includes timestamp, level, logger name, and message
- [ ] Noisy third-party loggers are suppressed to `WARNING`
- [ ] `LOG_LEVEL` from settings is respected
- [ ] `from core.logging import setup_logging, get_logger` works

**Dependencies:** Task 12.3

---

## Domain 4: Agent Server Entrypoint

### Task 12.5 — Create Agent Server Entrypoint

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the main entrypoint (`main.py`) for the LiveKit Agent Server. This is the script that registers the agent server with the LiveKit server and defines the entrypoint function that runs when a room is dispatched. The entrypoint function will be a minimal skeleton — it receives a `JobContext`, logs the room assignment, and connects to the room. The actual agent session creation and voice pipeline setup will be implemented in Epic 13.

**Tasks:**

- Create `agent-runtime/main.py`:
  - Import and call `setup_logging()` from `core.logging`
  - Import `settings` from `config.settings`
  - Define the entrypoint function:
    ```python
    async def entrypoint(ctx: agents.JobContext):
        logger.info(f"Job received for room: {ctx.room.name}")
        await ctx.connect()
        logger.info(f"Connected to room: {ctx.room.name}")
        # Agent session creation will be added in Epic 13
    ```
  - Define the `main` block:
    ```python
    if __name__ == "__main__":
        agents.cli.run_app(
            agents.WorkerOptions(
                entrypoint_fnc=entrypoint,
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET,
                ws_url=settings.LIVEKIT_URL,
                num_idle_processes=settings.WORKER_NUM_IDLE_PROCESSES,
            ),
        )
    ```
  - Add a clear `# TODO: Epic 13` comment where the AgentSession will be created

**Acceptance Criteria:**

- [ ] `main.py` exists with the entrypoint function and worker options
- [ ] Entrypoint function accepts `JobContext` and connects to the room
- [ ] Worker options load LiveKit credentials from settings
- [ ] Running `python main.py dev` starts the agent server without errors (when LiveKit is running)
- [ ] Logs show "Job received for room" when a room is created
- [ ] Clear TODO comment marks where Epic 13 implementation will go

**Dependencies:** Task 12.3, Task 12.4

---

## Domain 5: Room Event Handling

### Task 12.6 — Add Room Event Handling Boilerplate

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Add event handler boilerplate to the entrypoint function for key room events. These handlers log when participants join/leave and when tracks are published/unpublished. This provides observability and serves as the foundation for Epic 13 (track subscription) and Epic 21 (session lifecycle).

**Tasks:**

- Update `agent-runtime/main.py` entrypoint function to register event handlers after `ctx.connect()`:
  - `@ctx.room.on("participant_connected")` — log participant identity and metadata
  - `@ctx.room.on("participant_disconnected")` — log participant identity, reason
  - `@ctx.room.on("track_published")` — log track source (microphone, camera, screen_share) and participant
  - `@ctx.room.on("track_unpublished")` — log track source and participant
  - `@ctx.room.on("disconnected")` — log room disconnection reason
- Each handler should:
  - Use structured logging with the `get_logger` helper
  - Include the room name in log context
  - Be concise — just logging, no business logic (that's Epic 13/21)

**Acceptance Criteria:**

- [ ] Event handlers registered for `participant_connected`, `participant_disconnected`, `track_published`, `track_unpublished`, `disconnected`
- [ ] Each handler logs relevant information (participant identity, track source, reason)
- [ ] Room name is included in log messages for traceability
- [ ] No business logic in handlers — only logging (business logic is Epic 13/21)
- [ ] Agent server starts without errors after adding handlers

**Dependencies:** Task 12.5

---

## Domain 6: Graceful Shutdown

### Task 12.7 — Implement Graceful Shutdown & Signal Handling

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Configure the agent server for graceful shutdown. The `livekit-agents` SDK handles most shutdown behavior internally (draining active jobs, closing connections), but we need to ensure our application layer cleans up properly and logs shutdown events. This includes handling `SIGTERM` and `SIGINT` signals.

**Tasks:**

- Update `agent-runtime/main.py`:
  - Add a `shutdown_event` handler using `@ctx.room.on("disconnected")`:
    - Log "Room disconnected, cleaning up..."
    - Perform any cleanup logic needed (close HTTP clients, flush logs)
  - Add a `prewarm` function (optional, for startup optimization):
    ```python
    async def prewarm(proc: agents.JobProcess):
        logger.info("Agent process prewarming...")
        # Pre-import heavy modules here for faster job startup
    ```
  - Register `prewarm_fnc` in `WorkerOptions` if defined
- Add comments explaining that the SDK handles:
  - `SIGTERM`/`SIGINT` signal handling
  - Draining active sessions before exit
  - Process lifecycle management

**Acceptance Criteria:**

- [ ] Room disconnection handler logs cleanup message
- [ ] `prewarm` function exists for process startup optimization
- [ ] `WorkerOptions` includes `prewarm_fnc` reference
- [ ] Comments explain SDK-provided shutdown behavior
- [ ] `Ctrl+C` on the running agent server logs graceful shutdown messages
- [ ] No orphaned processes after shutdown

**Dependencies:** Task 12.6

---

## Domain 7: Health Check

### Task 12.8 — Add Health Check Mechanism

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Add a health check mechanism to the agent runtime. The `livekit-agents` SDK exposes an HTTP health endpoint when running. This task documents how to use it and adds a simple health check utility script that can be called by Docker or monitoring tools.

**Tasks:**

- Create `agent-runtime/utils/health.py`:
  - Function `check_health(url: str = "http://localhost:8081/health") -> bool`:
    - Make an HTTP GET request to the agent server's health endpoint
    - Return `True` if status is 200, `False` otherwise
    - Handle connection errors gracefully
  - CLI entrypoint when run directly:
    - Print health status and exit with code 0 (healthy) or 1 (unhealthy)
- Document in `agent-runtime/README.md`:
  - The default health check port (8081, configured by the SDK)
  - How to check health: `curl http://localhost:8081/health`
  - How to customize the port via environment variable if needed

**Acceptance Criteria:**

- [ ] `utils/health.py` exists with `check_health()` function
- [ ] Running `python utils/health.py` reports health status when the agent server is running
- [ ] Returns exit code 0 when healthy, 1 when unhealthy
- [ ] Handles connection errors gracefully (doesn't crash if server is down)
- [ ] `agent-runtime/README.md` documents the health check endpoint

**Dependencies:** Task 12.5

---

## Domain 8: Documentation & Development Workflow

### Task 12.9 — Create Agent Runtime Development Documentation

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Write comprehensive documentation for the agent runtime development workflow. This covers how to install dependencies, configure the environment, start the agent server, and verify it's running correctly alongside the LiveKit server and the backend API.

**Tasks:**

- Update `agent-runtime/README.md` with:
  - **Overview** — what the agent runtime does and its role in the platform
  - **Prerequisites** — Python 3.10+, Poetry, Docker (for LiveKit server)
  - **Installation** — `poetry install` instructions
  - **Configuration** — description of each `.env` variable
  - **Running the Agent Server**:
    - Step 1: Start infrastructure: `docker compose up -d` (LiveKit, Postgres, Redis)
    - Step 2: Start backend API: `cd backend && poetry run uvicorn app.main:app`
    - Step 3: Start agent runtime: `cd agent-runtime && poetry run python main.py dev`
  - **Verification** — how to verify the agent server registered with LiveKit
  - **Development Notes**:
    - The `dev` subcommand enables auto-reload on file changes
    - Logs are printed to stdout
    - Each room dispatch spawns a separate subprocess
  - **Troubleshooting** — common issues and solutions

**Acceptance Criteria:**

- [ ] `agent-runtime/README.md` is comprehensive and accurate
- [ ] Prerequisites are clearly listed
- [ ] Step-by-step instructions for running the agent server
- [ ] Configuration variables documented with descriptions and defaults
- [ ] Troubleshooting section covers common issues
- [ ] A new developer can follow the README and get the agent server running

**Dependencies:** Task 12.5

---

### Task 12.10 — Add Makefile Commands for Agent Runtime

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Add convenience commands to the root `Makefile` for common agent runtime operations. This follows the same pattern used for the backend and provides a quick way to start, lint, and format the agent runtime code.

**Tasks:**

- Update root `Makefile` with agent runtime targets:
  - `agent-dev` — start the agent runtime in development mode: `cd agent-runtime && poetry run python main.py dev`
  - `agent-lint` — run Ruff linter: `cd agent-runtime && poetry run ruff check .`
  - `agent-format` — run Black formatter: `cd agent-runtime && poetry run black .`
  - `agent-install` — install dependencies: `cd agent-runtime && poetry install`
- Ensure commands are documented with comments in the Makefile

**Acceptance Criteria:**

- [ ] `make agent-dev` starts the agent runtime
- [ ] `make agent-lint` runs Ruff on agent-runtime code
- [ ] `make agent-format` runs Black on agent-runtime code
- [ ] `make agent-install` installs agent-runtime dependencies
- [ ] Each target has a descriptive comment
- [ ] All targets work from the project root directory

**Dependencies:** Task 12.5

---

## Recommended Execution Order

1. **Task 12.1** — Install LiveKit Agents SDK & Plugin Dependencies
2. **Task 12.2** — Create Agent Runtime Project Structure
3. **Task 12.3** — Create Runtime Configuration Module
4. **Task 12.4** — Set Up Structured Logging for Agent Runtime
5. **Task 12.5** — Create Agent Server Entrypoint
6. **Task 12.6** — Add Room Event Handling Boilerplate
7. **Task 12.7** — Implement Graceful Shutdown & Signal Handling
8. **Task 12.8** — Add Health Check Mechanism
9. **Task 12.9** — Create Agent Runtime Development Documentation
10. **Task 12.10** — Add Makefile Commands for Agent Runtime

---

## Definition of Done

Epic 12 is complete when:

- [ ] All 10 tasks marked COMPLETED
- [ ] `poetry run python main.py dev` starts the agent server and registers with LiveKit
- [ ] Room events are logged when a room is created (via LiveKit dashboard or API)
- [ ] Graceful shutdown works on `Ctrl+C`
- [ ] Health check endpoint responds
- [ ] Documentation is comprehensive
- [ ] No regressions in Epics 1-8
