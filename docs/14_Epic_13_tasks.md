# Epic 13 — AgentSession & Voice Pipeline Setup

## Task Breakdown

**Epic Summary:** Implement the core `AgentSession` creation and voice pipeline configuration — the STT → LLM → TTS streaming pipeline that powers every conversation. This epic covers plugin configuration, VAD integration, turn detection, RoomIO setup, interruption handling, streaming audio output, and the session startup sequence. This is the heart of the agent runtime. This epic does NOT cover the `Agent` class implementation (Epic 14), multi-agent handoffs (Epic 15), dynamic configuration loading (Epic 16), function tools (Epic 17), or video/vision pipeline (Epic 19).

**Layer:** Agent Runtime
**Dependencies:** Epic 12 (Agent Runtime Foundation)

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

## Domain 1: API Key Configuration

### Task 13.1 — Add STT, TTS, and LLM Provider Settings

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Extend the `RuntimeSettings` in `agent-runtime/config/settings.py` to include the API keys, base URLs, and model identifiers required by the STT, TTS, and LLM plugins. Base URLs are included so that providers can be swapped to self-hosted instances, regional endpoints, or alternative API-compatible services without any code changes. These settings are consumed when instantiating the `AgentSession` voice pipeline. Follow the same `pydantic-settings` pattern already established in Epic 12.

**Tasks:**

- Update `agent-runtime/config/settings.py` `RuntimeSettings` class:
  - **Deepgram (STT):**
    - Add `DEEPGRAM_API_KEY: str` — API key for Deepgram STT
    - Add `DEEPGRAM_BASE_URL: str = "https://api.deepgram.com"` — Deepgram API base URL (changeable for self-hosted or EU endpoint `https://api.eu.deepgram.com`)
    - Add `STT_MODEL: str = "nova-3"` — Default Deepgram STT model
  - **OpenAI (LLM):**
    - Add `OPENAI_API_KEY: str` — API key for OpenAI LLM
    - Add `OPENAI_BASE_URL: str = "https://api.openai.com/v1"` — OpenAI API base URL (changeable for Azure OpenAI, local LLM servers, or other OpenAI-compatible providers)
    - Add `LLM_MODEL: str = "gpt-4.1-mini"` — Default OpenAI LLM model
  - **Cartesia (TTS):**
    - Add `CARTESIA_API_KEY: str` — API key for Cartesia TTS
    - Add `CARTESIA_BASE_URL: str = "https://api.cartesia.ai"` — Cartesia API base URL
    - Add `TTS_MODEL: str = "sonic"` — Default Cartesia TTS model
    - Add `TTS_VOICE_ID: str` — Default Cartesia voice ID
- Update `agent-runtime/.env.example`:
  - Add all new variables with placeholder values and comments
  - Include commented-out alternative base URLs as examples (e.g., `# DEEPGRAM_BASE_URL=https://api.eu.deepgram.com`)
- Update `agent-runtime/.env`:
  - Add local development values (actual API keys should be sourced from developer's accounts)

**Acceptance Criteria:**

- [ ] `config/settings.py` includes all API key, base URL, and model settings
- [ ] Each setting has a sensible default where applicable (model names, base URLs)
- [ ] API keys are required fields (no default — must be provided)
- [ ] Base URLs have production defaults but can be overridden via `.env`
- [ ] `.env.example` documents all new variables with descriptions
- [ ] `from config.settings import settings` loads without error when `.env` is properly configured

**Dependencies:** Task 12.3 (Runtime Configuration Module)

---

## Domain 2: STT Plugin Setup

### Task 13.2 — Configure Deepgram STT Plugin

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a factory function that instantiates the Deepgram STT plugin with the configured API key and model. Deepgram Nova is the default STT engine per the LLD. The factory function encapsulates plugin creation so it can be swapped or overridden later without modifying the session creation code.

**Tasks:**

- Create `agent-runtime/core/plugins.py`:
  - Function `create_stt(api_key: str, base_url: str, model: str) -> deepgram.STT`:
    - Instantiate `deepgram.STT` with the provided API key, base URL, and model
    - Return the configured STT instance
- Import and use settings values as defaults

**Acceptance Criteria:**

- [ ] `core/plugins.py` exists with `create_stt()` function
- [ ] Function returns a configured `deepgram.STT` instance
- [ ] API key, base URL, and model are parameterized (not hardcoded)
- [ ] `from core.plugins import create_stt` works without error
- [ ] Deepgram plugin initializes without runtime errors when a valid API key is provided

**Dependencies:** Task 13.1

---

## Domain 3: TTS Plugin Setup

### Task 13.3 — Configure Cartesia TTS Plugin

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a factory function that instantiates the Cartesia TTS plugin with the configured API key, model, and voice ID. Cartesia Sonic is the default TTS engine per the LLD. The voice ID determines the speaking voice used for agent responses.

**Tasks:**

- Update `agent-runtime/core/plugins.py`:
  - Function `create_tts(api_key: str, base_url: str, model: str, voice_id: str) -> cartesia.TTS`:
    - Instantiate `cartesia.TTS` with the provided API key, base URL, model, and voice
    - Return the configured TTS instance

**Acceptance Criteria:**

- [ ] `create_tts()` function exists in `core/plugins.py`
- [ ] Function returns a configured `cartesia.TTS` instance
- [ ] API key, base URL, model, and voice ID are parameterized
- [ ] `from core.plugins import create_tts` works without error
- [ ] Cartesia plugin initializes without runtime errors when a valid API key is provided

**Dependencies:** Task 13.1

---

## Domain 4: LLM Plugin Setup

### Task 13.4 — Configure OpenAI LLM Plugin

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a factory function that instantiates the OpenAI LLM plugin with the configured API key and model. GPT-4.1-mini is the default LLM per the LLD. This is the model that processes user speech transcripts and generates agent responses.

**Tasks:**

- Update `agent-runtime/core/plugins.py`:
  - Function `create_llm(api_key: str, base_url: str, model: str) -> openai.LLM`:
    - Instantiate `openai.LLM` with the provided API key, base URL, and model
    - Return the configured LLM instance

**Acceptance Criteria:**

- [ ] `create_llm()` function exists in `core/plugins.py`
- [ ] Function returns a configured `openai.LLM` instance
- [ ] API key, base URL, and model are parameterized
- [ ] `from core.plugins import create_llm` works without error
- [ ] OpenAI plugin initializes without runtime errors when a valid API key is provided

**Dependencies:** Task 13.1

---

## Domain 5: VAD & Turn Detection

### Task 13.5 — Configure Silero VAD and Turn Detection

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create factory functions for Voice Activity Detection (VAD) and turn detection. Silero VAD runs locally with zero API cost and detects when the user starts/stops speaking. The LiveKit multilingual turn detection model identifies end-of-turn boundaries to determine when the user has finished their utterance.

**Tasks:**

- Update `agent-runtime/core/plugins.py`:
  - Function `create_vad() -> silero.VAD`:
    - Load the Silero VAD model using `silero.VAD.load()`
    - Return the loaded VAD instance
  - Function `create_turn_detector()`:
    - Import and instantiate the LiveKit multilingual turn detector
    - Return the configured turn detector instance

**Acceptance Criteria:**

- [ ] `create_vad()` function exists in `core/plugins.py`
- [ ] Function returns a loaded `silero.VAD` instance
- [ ] `create_turn_detector()` function exists in `core/plugins.py`
- [ ] VAD model loads without errors
- [ ] Turn detector initializes without errors
- [ ] No external API key required for VAD (runs locally)

**Dependencies:** Task 12.1 (SDK Dependencies installed)

---

## Domain 6: AgentSession Creation

### Task 13.6 — Create AgentSession Factory

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create a factory function that assembles all plugins (STT, TTS, LLM, VAD, turn detection) into an `AgentSession` instance. The `AgentSession` is the main orchestrator — it owns the voice pipeline and manages the active agent. This factory centralizes session creation so the entrypoint function remains clean.

**Tasks:**

- Create `agent-runtime/core/session.py`:
  - Function `create_agent_session(settings) -> AgentSession`:
    - Call the plugin factory functions to create STT, TTS, LLM, VAD, and turn detector instances
    - Instantiate `AgentSession` with all configured plugins:
      ```python
      session = AgentSession(
          stt=create_stt(...),
          llm=create_llm(...),
          tts=create_tts(...),
          vad=create_vad(),
          turn_detection=create_turn_detector(),
      )
      ```
    - Return the session instance
    - Log the plugin configuration (model names, not API keys) for debugging

**Acceptance Criteria:**

- [ ] `core/session.py` exists with `create_agent_session()` function
- [ ] Function creates an `AgentSession` with all five plugins (STT, TTS, LLM, VAD, turn detection)
- [ ] Plugin configuration is logged (model names only, never API keys)
- [ ] `from core.session import create_agent_session` works without error
- [ ] Session instance is created without errors when all API keys are valid

**Dependencies:** Task 13.2, Task 13.3, Task 13.4, Task 13.5

---

## Domain 7: RoomIO & Audio Configuration

### Task 13.7 — Configure RoomIO and Audio Input Options

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Configure the `RoomIO` settings for the `AgentSession`, specifically the `RoomOptions` that control audio input processing. This includes configuring noise cancellation options for the incoming audio stream. Video input configuration is NOT in scope (Epic 19).

**Tasks:**

- Update `agent-runtime/core/session.py`:
  - Define a function `create_room_options() -> room_io.RoomOptions`:
    - Configure `audio_input` with `AudioInputOptions`
    - Set `noise_cancellation` using `noise_cancellation.BVC()` for WebRTC participants
    - Set `video_input` to `False` (default audio-only; video is Epic 19)
    - Return the configured `RoomOptions`
- Add `livekit-plugins-noise-cancellation` to `agent-runtime/pyproject.toml` if not already present
- Run `poetry lock && poetry install`

**Acceptance Criteria:**

- [ ] `create_room_options()` function exists in `core/session.py`
- [ ] Audio input configured with noise cancellation
- [ ] `video_input` explicitly set to `False` (audio-only by default)
- [ ] Noise cancellation plugin installed and importable
- [ ] Function returns a valid `RoomOptions` instance

**Dependencies:** Task 13.6

---

## Domain 8: Session Startup Integration

### Task 13.8 — Integrate AgentSession into Entrypoint

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Update the `main.py` entrypoint function (created in Task 12.5) to create and start an `AgentSession` using the factory functions. This replaces the `TODO: Epic 13` placeholder. The session startup sequence connects to the room, subscribes to tracks, and starts the voice pipeline. A minimal placeholder `Agent` is used here — the full `Agent` class implementation is Epic 14.

**Tasks:**

- Update `agent-runtime/main.py`:
  - Import `create_agent_session` from `core.session`
  - Import `create_room_options` from `core.session`
  - Import `Agent` from `livekit.agents`
  - In the `entrypoint` function, after `ctx.connect()`:
    - Create the `AgentSession` using the factory
    - Create a minimal placeholder `Agent` with basic instructions:
      ```python
      agent = Agent(instructions="You are a helpful voice assistant.")
      ```
    - Start the session:
      ```python
      await session.start(
          room=ctx.room,
          agent=agent,
          room_options=create_room_options(),
      )
      ```
    - Generate an initial greeting:
      ```python
      await session.generate_reply(
          instructions="Greet the user and offer your assistance."
      )
      ```
  - Remove the `shutdown_event` manual wait pattern (the session handles lifecycle)
  - Keep room event handlers for logging purposes

**Acceptance Criteria:**

- [ ] `main.py` creates an `AgentSession` and starts it in the entrypoint
- [ ] The `TODO: Epic 13` placeholder is replaced with actual session creation
- [ ] A minimal placeholder `Agent` is created with basic instructions
- [ ] Session starts with `room_options` configured from Task 13.7
- [ ] Initial greeting is generated on session start
- [ ] Agent server starts without errors: `poetry run python main.py dev`
- [ ] When a room is created, the agent connects and is ready for conversation

**Dependencies:** Task 13.6, Task 13.7, Task 12.5, Task 12.6

---

## Domain 9: Interruption Handling

### Task 13.9 — Verify and Document Interruption Handling

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
The LiveKit Agents SDK handles interruption natively — when the user speaks while the agent is talking, the SDK stops the TTS output. This task verifies that interruption handling works correctly with the configured voice pipeline and documents the behavior. No custom code is needed — this is built into the SDK.

**Tasks:**

- Verify interruption behavior by testing:
  - Start a session and let the agent speak
  - Speak while the agent is mid-response
  - Confirm the agent stops speaking immediately
  - Confirm the agent processes the new user input
- Document interruption behavior in `agent-runtime/README.md`:
  - How interruptions work (SDK-native)
  - How VAD detects voice activity to trigger interruption
  - How turn detection determines end-of-turn after interruption
  - Any configuration knobs (if applicable)
- Add a comment in `core/session.py` noting that interruption handling is SDK-native

**Acceptance Criteria:**

- [ ] Interruption handling verified with a live test
- [ ] Agent stops TTS output when user speaks mid-response
- [ ] New user speech is processed after interruption
- [ ] `README.md` documents interruption behavior
- [ ] Comment in `core/session.py` explains SDK-native interruption handling

**Dependencies:** Task 13.8

---

## Domain 10: Prewarm Optimization

### Task 13.10 — Optimize Prewarm for Plugin Preloading

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Update the `prewarm` function (created in Task 12.7) to pre-import and preload heavy plugin modules. This reduces cold-start latency for the first job by ensuring Silero VAD model weights and plugin modules are already in memory when a job is dispatched.

**Tasks:**

- Update the `prewarm` function in `agent-runtime/main.py`:
  - Pre-import plugin modules (`deepgram`, `openai`, `cartesia`, `silero`)
  - Preload the Silero VAD model using `silero.VAD.load(force_download=False)`
  - Pre-import the turn detector module
  - Log the completion of prewarming with timing information
- Ensure the prewarm function does not fail if network is unavailable (VAD loads from cache)

**Acceptance Criteria:**

- [ ] `prewarm` function pre-imports all plugin modules
- [ ] Silero VAD model is preloaded during prewarm
- [ ] Turn detector module is pre-imported
- [ ] Prewarm logs completion with timing
- [ ] First job startup is noticeably faster after prewarm
- [ ] Prewarm does not crash if models are already cached

**Dependencies:** Task 13.5, Task 12.7

---

## Domain 11: Configuration Documentation

### Task 13.11 — Update Documentation for Voice Pipeline

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Update the agent runtime documentation to cover the voice pipeline configuration, including all new environment variables, plugin descriptions, and the session startup sequence.

**Tasks:**

- Update `agent-runtime/README.md`:
  - **Voice Pipeline** section:
    - Overview of the STT → LLM → TTS pipeline
    - Description of each plugin (Deepgram STT, OpenAI LLM, Cartesia TTS, Silero VAD)
    - Turn detection explanation
  - **Configuration** section:
    - Document all new `.env` variables (API keys, base URLs, model names, voice ID)
    - Note which variables are required vs optional
    - Document how to override base URLs for self-hosted or alternative providers
  - **Running** section:
    - Prerequisites updated (API keys for Deepgram, OpenAI, Cartesia)
    - Verification steps (start agent, join room, speak, hear response)
  - **Troubleshooting** section:
    - Common issues: missing API keys, invalid model names, VAD download failures
- Update `agent-runtime/.env.example` comments to be comprehensive

**Acceptance Criteria:**

- [ ] `README.md` documents the voice pipeline architecture
- [ ] All new environment variables documented with descriptions
- [ ] Prerequisites updated with API key requirements
- [ ] Troubleshooting covers common pipeline issues
- [ ] A new developer can configure and run the voice pipeline by following the docs

**Dependencies:** Task 13.8

---

## Recommended Execution Order

1. **Task 13.1** — Add STT, TTS, and LLM API Key Settings
2. **Task 13.2** — Configure Deepgram STT Plugin
3. **Task 13.3** — Configure Cartesia TTS Plugin
4. **Task 13.4** — Configure OpenAI LLM Plugin
5. **Task 13.5** — Configure Silero VAD and Turn Detection
6. **Task 13.6** — Create AgentSession Factory
7. **Task 13.7** — Configure RoomIO and Audio Input Options
8. **Task 13.8** — Integrate AgentSession into Entrypoint
9. **Task 13.9** — Verify and Document Interruption Handling
10. **Task 13.10** — Optimize Prewarm for Plugin Preloading
11. **Task 13.11** — Update Documentation for Voice Pipeline

---

## Definition of Done

Epic 13 is complete when:

- [ ] All 11 tasks marked COMPLETED
- [ ] `AgentSession` is created with STT, LLM, TTS, VAD, and turn detection plugins
- [ ] Voice pipeline works end-to-end: user speaks → agent responds with voice
- [ ] Interruption handling works (agent stops when user speaks mid-response)
- [ ] Audio input has noise cancellation configured
- [ ] Plugin configuration is loaded from environment variables
- [ ] Documentation is comprehensive and accurate
- [ ] No regressions in Epics 1-8, 12
