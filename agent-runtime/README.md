# LiveKit Agent Runtime

This service runs the interactive AI agents that communicate with end-users via LiveKit. It is built on top of the LiveKit Agents SDK.

## Voice Pipeline Architecture

The agent uses a streaming voice pipeline to ensure low-latency interactions:

1.  **STT (Deepgram)**: Transcribes user audio in real-time.
2.  **VAD (Silero)**: Detects when the user starts and stops speaking.
3.  **Turn Detection (LiveKit Multilingual)**: Determines when the user has finished their turn using semantic analysis.
4.  **LLM (OpenAI)**: Generates intelligent responses based on the conversation context.
5.  **TTS (Cartesia)**: Synthesizes speech from the LLM response with ultra-low latency.

This pipeline is orchestrated by the `AgentSession`, which manages the state and flow of the conversation.

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
- `WORKER_NUM_IDLE_PROCESSES`: Number of idle processes to keep warm (default: 3)

### Voice Pipeline Configuration

The following variables configure the speech-to-text, LLM, and text-to-speech providers:

**STT (Deepgram)**

- `DEEPGRAM_API_KEY`: API Key for Deepgram
- `STT_MODEL`: Deepgram model (default: `nova-3`)

**LLM (OpenAI)**

- `OPENAI_API_KEY`: API Key for OpenAI
- `LLM_MODEL`: OpenAI model (default: `gpt-4o-mini`)

**TTS (Cartesia)**

- `CARTESIA_API_KEY`: API Key for Cartesia
- `TTS_MODEL`: Cartesia model (default: `sonic`)
- `TTS_VOICE_ID`: Cartesia Voice ID (see [Cartesia docs](https://docs.cartesia.ai/))

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

## Interruption Handling

The agent runtime supports robust interruption handling powered natively by the LiveKit Agents SDK.

- **SDK-Native Behavior:** When the user speaks while the agent is responding, the VAD detects voice activity and immediately signals the agent to stop speaking.
- **Mechanism:** The STT plugin streams user speech to the VAD. Upon detection of speech, the `Agent` cancels the current TTS stream and clears the audio buffer, ensuring the agent stops talking instantly.
- **Turn Logic:** The `TurnDetector` then waits for the user to finish their new utterance. Once the user stops speaking (end-of-turn), the full transcript is sent to the LLM to generate a new response, acknowledging the interruption.
- **Configuration:** No custom code is required for this behavior; it is enabled by default in the `AgentSession` configuration (`allow_interruptions=True` by default).

## Single Agent Architecture

The runtime implements a robust single-agent architecture designed for extensibility:

### BaseAgent

The `BaseAgent` class (`agents/base_agent.py`) extends the LiveKit SDK `Agent` to provide:

- **Lifecycle Hooks**: `on_enter` (greeting) and `on_user_turn_completed` (logging/bookkeeping).
- **Standardized Greeting**: Configurable greeting message sent when the agent joins.
- **Context Access**: Easy access to the `SessionContext`.

### SessionContext

The `SessionContext` (`core/context.py`) acts as the shared state repository for the session, passed as `userdata`. It stores:

- **User Profile**: `user_id`, `user_name`, `session_template_id`.
- **Observations**: List of insights gathered by the agent.
- **Session Flags**: Custom key-value pairs for session-specific logic.
- **Modality State**: Tracks active capabilities (camera, screenshare).

### Error Handling

The runtime includes a centralized error handler (`core/error_handler.py`) that:

- Listens for pipeline errors (STT, LLM, TTS failures).
- Classifies errors as **Transient** (network/timeouts - log warning) or **Permanent** (auth/config - log error).
- Logs interruptions (`agent_speech_interrupted`) for analytics.

## Configuration

New environment variables control the default agent behavior:

- `DEFAULT_AGENT_INSTRUCTIONS`: System prompt for the agent.
- `DEFAULT_AGENT_GREETING`: Initial greeting message.

## End-to-End Verification

To verify the single-agent implementation:

1.  **Start Services**: Ensure LiveKit Server, Redis, and Postgres are running (`docker compose up -d`).
2.  **Run Agent**: `poetry run python main.py dev`.
3.  **Connect Client**: Use the LiveKit CLI or a client SDK to join a room.
    ```bash
    livekit-cli join-room --url ws://localhost:7880 --api-key devkey --api-secret devsecret --identity user1 --room test-room
    ```
4.  **Verify Greeting**: The agent should join and speak the configured greeting ("Greet the user warmly...").
5.  **Speak**: Speak into the microphone. Verify the agent transcribes and responds.
6.  **Interrupt**: Speak while the agent is responding. The agent should stop immediately.
7.  **Check Logs**: Verify `[agents.base_agent] User turn completed` logs appear.

## Troubleshooting

- **Connection Refused**: Ensure LiveKit server is running and `LIVEKIT_URL` is correct.
- **Authentication Failed**: Check `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`.
- **Import Errors**: Run `poetry install` to ensure all dependencies are up to date.
