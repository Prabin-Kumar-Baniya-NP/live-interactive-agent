# LiveKit Agent Runtime

This service runs the interactive AI agents that communicate with end-users via LiveKit. It is built on top of the LiveKit Agents SDK.

## Prerequisites

- Python 3.10+
- Poetry
- Docker & Docker Compose (for LiveKit server and Redis)

## Installation

```bash
cd agent-runtime
poetry install
```

## Configuration

The agent runtime is configured via environment variables. See `.env.example` for all options.

Key variables:

- `LIVEKIT_URL`: WebSocket URL of your LiveKit server (default: `ws://localhost:7880`)
- `LIVEKIT_API_KEY`: API Key for LiveKit
- `LIVEKIT_API_SECRET`: API Secret for LiveKit
- `PLATFORM_API_URL`: URL of the Platform API (default: `http://localhost:8000`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

To set up local development configuration:

```bash
cp .env.example .env
```

## Running the Agent Server

### 1. Start Infrastructure

Ensure LiveKit Server, Redis, and Postgres are running:

```bash
# In the project root
docker compose up -d
```

### 2. Start Backend API

The agent runtime may depend on the backend API for configuration.

```bash
# In the project root or backend directory
cd backend
poetry run uvicorn app.main:app --reload
```

### 3. Start Agent Runtime

```bash
# In agent-runtime directory
poetry run python main.py dev
```

The `dev` command starts the worker in development mode with auto-reload enabled.

## Verification

To verify the agent is running:

1. Check the logs. You should see "Connected to LiveKit" or similar success messages.
2. Check the health endpoint:

```bash
curl http://localhost:8081/health
```

3. Connect a client to a LiveKit room. The agent should join automatically if configured.

## Troubleshooting

- **Connection Refused**: Ensure LiveKit server is running and `LIVEKIT_URL` is correct.
- **Authentication Failed**: Check `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`.
- **Import Errors**: Run `poetry install` to ensure all dependencies are up to date.
