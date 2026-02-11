# Interactive Live Agent

Monorepo for a real-time interactive AI agent platform.

## 🚀 Quick Start

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-org/live-interactive-agent.git
    cd live-interactive-agent
    ```

2.  **Run the setup script:**

    ```bash
    ./scripts/setup.sh
    ```

    This script will install dependencies, create `.env` files from examples, and start the local Docker services (Postgres, Redis, LiveKit).

3.  **Start Development Servers:**

    - **Frontend:**
      ```bash
      pnpm dev
      ```
    - **Backend:**
      ```bash
      cd backend && poetry run uvicorn main:app --reload
      ```
    - **Agent Runtime:**
      ```bash
      cd agent-runtime && poetry run python agent.py
      ```

## 🏗️ Architecture

- `frontend/`: Next.js application (Port 3000)
- `backend/`: FastAPI Platform API (Port 8000)
- `agent-runtime/`: LiveKit Agent Server
- `docker-compose.yml`: Local infrastructure (Postgres: 5432, Redis: 6379, LiveKit: 7880)

## 🛠️ Prerequisites

- Node.js (v20+)
- Python (v3.10+)
- Docker & Docker Compose
- pnpm (`npm install -g pnpm`)
- Poetry (`pip install poetry`)

## 📦 Monorepo Command

We use `pnpm` workspaces for the frontend and `poetry` for Python packages.

- **Linting:** `make lint`
- **Formatting:** `make format`

## 🐳 Docker Services

The `docker-compose.yml` provides:

- PostgreSQL (`postgres:password@localhost:5432/live_agent`)
- Redis (`localhost:6379`)
- LiveKit Server (`ws://localhost:7880`)

**Note:** Ensure ports 5432, 6379, and 7880 are free before starting.

For detailed setup and compatibility information, see [LiveKit Server Setup](docs/livekit-setup.md).

## 🎥 LiveKit CLI (Optional but Recommended)

For debugging and generating tokens, install the `lk` CLI:

- **macOS:** `brew install livekit-cli`
- **Linux:** `curl -sSL https://get.livekit.io/cli | bash`
- **Windows:** `choco install livekit-cli`

For more details, see [LiveKit CLI Docs](https://docs.livekit.io/server/cli/).

## 🔄 CI/CD

The repository includes a GitHub Actions workflow `.github/workflows/ci.yml` that validates the project structure on every push. In future epics, this pipeline will be extended to include:

- Frontend Linting & Testing (Epic 22)
- Backend Linting & Testing (Epic 4)
- Agent Runtime Verification (Epic 36)

## Database & Caching

The project uses PostgreSQL for persistent storage and Redis for caching/session state.

### Credentials (Local)

- **PostgreSQL**: `localhost:5432`
  - User: `liveinteractiveagent`
  - Pass: `vibecoding123`
  - DB: `liveinteractiveagentdb`
- **Redis**: `localhost:6379`

### Common Commands

**Migrations (Alembic)**

- Run migrations: `cd backend && poetry run alembic upgrade head`
- Create migration: `cd backend && poetry run alembic revision --autogenerate -m "description"`
- Rollback: `cd backend && poetry run alembic downgrade -1`

**Seeding**

- Seed initial data: `make seed` (Creates Test Organization and Admin User)

**Direct Access**

- PostgreSQL: `psql -h localhost -p 5432 -U liveinteractiveagent -d liveinteractiveagentdb`
- Redis: `redis-cli`

### Backup & Restore

**Backup**

```bash
pg_dump -h localhost -p 5432 -U liveinteractiveagent liveinteractiveagentdb > backup.sql
```

**Restore**

```bash
psql -h localhost -p 5432 -U liveinteractiveagent liveinteractiveagentdb < backup.sql
```

### Initial Schema

- `users`: Platform users (admins, members).
- `organizations`: Multi-tenancy grouping.
- `sessions`: LiveKit session tracking.
