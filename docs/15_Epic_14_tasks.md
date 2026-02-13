# Epic 14 — Single Agent Implementation

## Task Breakdown

**Epic Summary:** Implement a complete single-agent experience — one agent that can listen, think, and respond. This validates the entire voice pipeline end-to-end before adding multi-agent complexity. This epic covers the `Agent` class implementation with system prompt, `ChatContext` management, agent lifecycle hooks, `SessionContext` (userdata) initialization, configurable greeting, and basic error handling. This epic does NOT cover multi-agent handoffs (Epic 15), dynamic configuration loading from Platform API (Epic 16), function tools (Epic 17), RPC communication (Epic 18), or video/vision pipeline (Epic 19).

**Layer:** Agent Runtime
**Dependencies:** Epic 13 (AgentSession & Voice Pipeline Setup)

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

## Domain 1: SessionContext (Userdata)

### Task 14.1 — Create SessionContext Dataclass

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a `SessionContext` dataclass that serves as the shared state for a session. This is passed as `userdata` to the `AgentSession` and is accessible by the agent throughout the session. Per the LLD (Section 4.4), the `SessionContext` stores user profile information, accumulated observations, modality state, panel state, and custom session flags. For this epic (single agent, no panels, no vision), we initialize the foundational fields — user profile, observations, and session flags. Panel state and modality state fields are defined but left as empty defaults (populated in later epics).

**Tasks:**

- Create `agent-runtime/core/context.py`:
  - Define `SessionContext` as a Python `dataclass`:
    - `user_id: str | None = None` — end-user identifier from access token metadata
    - `user_name: str | None = None` — end-user display name, if available
    - `session_template_id: str | None = None` — the template this session was created from
    - `observations: list[str] = field(default_factory=list)` — things any agent has learned during the session (e.g., "user is confused about topic X")
    - `session_flags: dict[str, Any] = field(default_factory=dict)` — custom per-use-case data (e.g., interview score, items ordered)
    - `modality_state: dict[str, bool] = field(default_factory=lambda: {"camera": False, "screenshare": False})` — current active tracks (placeholder for Epic 19)
    - `panel_state: dict[str, Any] = field(default_factory=dict)` — workspace panel state (placeholder for Epic 28)
  - Add a helper method `add_observation(self, observation: str) -> None` that appends to the `observations` list
  - Add a helper method `set_flag(self, key: str, value: Any) -> None` that sets a session flag
  - Add a helper method `get_flag(self, key: str, default: Any = None) -> Any` that gets a session flag

**Acceptance Criteria:**

- [ ] `core/context.py` exists with `SessionContext` dataclass
- [ ] All fields defined as specified above with sensible defaults
- [ ] `add_observation()` appends a string to the observations list
- [ ] `set_flag()` and `get_flag()` work correctly for session flags
- [ ] `from core.context import SessionContext` works without error
- [ ] `SessionContext()` can be instantiated with no arguments (all fields have defaults)

**Dependencies:** None

---

## Domain 2: Agent Class

### Task 14.2 — Create BaseAgent Class with System Prompt

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create a `BaseAgent` class in the `agents/` directory that extends the LiveKit SDK `Agent` class. This class provides a standard foundation for all agents in the platform. It accepts a system prompt (instructions), an optional greeting message, and wraps the SDK's `Agent` with project-specific defaults. For this epic, only a single agent is needed — the `BaseAgent` itself serves as the single conversational agent.

**Tasks:**

- Create `agent-runtime/agents/base_agent.py`:
  - Class `BaseAgent` extends `livekit.agents.Agent`:
    - `__init__(self, *, instructions: str, greeting: str | None = None, chat_ctx: ChatContext | None = None)`:
      - Call `super().__init__(instructions=instructions, chat_ctx=chat_ctx)`
      - Store `self._greeting = greeting`
    - Property `greeting -> str | None` — returns the stored greeting message
  - The `BaseAgent` delegates all core behavior (LLM interaction, streaming, turn handling) to the SDK's `Agent` parent class — no custom pipeline logic needed

**Acceptance Criteria:**

- [ ] `agents/base_agent.py` exists with `BaseAgent` class
- [ ] `BaseAgent` extends `livekit.agents.Agent`
- [ ] `instructions` parameter passed to parent `Agent.__init__`
- [ ] `greeting` property returns the stored greeting message
- [ ] Optional `chat_ctx` parameter forwarded to parent
- [ ] `from agents.base_agent import BaseAgent` works without error
- [ ] `BaseAgent(instructions="You are a helpful assistant.")` instantiates without error

**Dependencies:** None

---

### Task 14.3 — Implement Agent Lifecycle Hooks

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Implement the agent lifecycle hooks — `on_enter` and `on_user_turn_completed` — on the `BaseAgent` class. Per the LLD (Section 2.2), `on_enter` fires when the agent takes control of the session and is used to generate a transition/greeting message. `on_user_turn_completed` fires after the user finishes speaking and can be used for bookkeeping (e.g., logging observations). These hooks are SDK-native override methods.

**Tasks:**

- Update `agent-runtime/agents/base_agent.py`:
  - Override `async def on_enter(self)`:
    - Log that the agent has entered/taken control
    - If `self._greeting` is set, generate a greeting reply using `self.session.generate_reply(instructions=self._greeting)`
  - Override `async def on_user_turn_completed(self, turn_ctx)`:
    - Log a summary of the completed user turn (e.g., user transcript length)
    - Access `self.session.userdata` (the `SessionContext`) for any bookkeeping if needed
    - This hook is intentionally lightweight for now — extended in Epic 15 (multi-agent) and Epic 17 (tools)

**Acceptance Criteria:**

- [ ] `on_enter` is overridden and logs agent entry
- [ ] `on_enter` generates a greeting reply if `self._greeting` is set
- [ ] `on_enter` does nothing extra if `self._greeting` is `None`
- [ ] `on_user_turn_completed` is overridden and logs turn completion
- [ ] Both hooks use the project's structured logger (`core.logging.get_logger`)
- [ ] No errors when hooks are triggered during a live session

**Dependencies:** Task 14.2

---

## Domain 3: Session Integration

### Task 14.4 — Wire Agent and SessionContext into Entrypoint

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Update `main.py` to replace the inline placeholder `Agent` (from Task 13.8) with the new `BaseAgent` class and initialize `SessionContext` as the session's `userdata`. This wires together the agent, session context, and the voice pipeline for a complete single-agent conversation flow. Room participant metadata (from the LiveKit JWT) is parsed to populate `SessionContext` fields.

**Tasks:**

- Update `agent-runtime/main.py`:
  - Import `BaseAgent` from `agents.base_agent`
  - Import `SessionContext` from `core.context`
  - In the `entrypoint` function:
    - Parse room participant metadata to extract `user_id`, `session_template_id` (if present in JWT metadata)
    - Create `SessionContext` instance with extracted metadata:
      ```python
      session_ctx = SessionContext(
          user_id=metadata.get("user_id"),
          session_template_id=metadata.get("session_template_id"),
      )
      ```
    - Create a `BaseAgent` instance with configurable instructions and greeting:
      ```python
      agent = BaseAgent(
          instructions="You are a helpful voice assistant. Be concise and friendly.",
          greeting="Greet the user warmly and offer your assistance.",
      )
      ```
    - Pass `userdata=session_ctx` to `session.start()`:
      ```python
      await session.start(
          room=ctx.room,
          agent=agent,
          room_options=create_room_options(),
          userdata=session_ctx,
      )
      ```
    - Remove the old inline `Agent(instructions=...)` and `session.generate_reply()` calls (greeting is now handled by `BaseAgent.on_enter`)

**Acceptance Criteria:**

- [ ] `main.py` uses `BaseAgent` instead of inline `Agent`
- [ ] `SessionContext` is created and passed as `userdata`
- [ ] Room participant metadata is parsed for user context (graceful if metadata is missing/empty)
- [ ] Greeting is handled by `BaseAgent.on_enter`, not by a separate `generate_reply` call
- [ ] Agent server starts without errors: `poetry run python main.py dev`
- [ ] When a room is created, the agent connects, greets the user, and responds to speech

**Dependencies:** Task 14.2, Task 14.3, Task 14.1, Task 13.8

---

## Domain 4: ChatContext Management

### Task 14.5 — Create ChatContext Helper Utilities

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a utility module with helper functions for working with `ChatContext`. The LiveKit SDK manages `ChatContext` internally within the `AgentSession`, but we need helpers for common operations such as building an initial chat context with a system prompt or logging the current context for debugging. These helpers are used by the agent and session code.

**Tasks:**

- Create `agent-runtime/core/chat.py`:
  - Function `create_initial_chat_ctx(system_prompt: str) -> ChatContext`:
    - Create a new `ChatContext` instance
    - Append a system message with the provided system prompt
    - Return the context
  - Function `log_chat_ctx_summary(chat_ctx: ChatContext, logger: logging.Logger) -> None`:
    - Log a summary of the current chat context: total message count, roles present, approximate token count (character-based estimate)
    - Useful for debugging and monitoring context growth
  - Function `get_chat_ctx_message_count(chat_ctx: ChatContext) -> int`:
    - Return the total number of messages in the chat context

**Acceptance Criteria:**

- [ ] `core/chat.py` exists with all three utility functions
- [ ] `create_initial_chat_ctx()` returns a `ChatContext` with a system message
- [ ] `log_chat_ctx_summary()` logs message count and role breakdown
- [ ] `get_chat_ctx_message_count()` returns correct count
- [ ] `from core.chat import create_initial_chat_ctx` works without error
- [ ] Functions handle empty `ChatContext` gracefully

**Dependencies:** None

---

## Domain 5: Error Handling

### Task 14.6 — Add Voice Pipeline Error Handling

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Add error handling for common voice pipeline failures — LLM errors, STT failures, and TTS failures. The LiveKit SDK emits events for pipeline errors, and we need to listen for these events, log them, and handle them gracefully (e.g., retrying or notifying the user). This ensures the session doesn't crash silently when a provider has an outage or rate limits are hit.

**Tasks:**

- Create `agent-runtime/core/error_handler.py`:
  - Function `register_error_handlers(session: AgentSession) -> None`:
    - Register event handlers on the `AgentSession` for error events:
      - `@session.on("agent_speech_interrupted")` — log when speech is interrupted (informational, not an error)
      - `@session.on("error")` — log and handle general session errors
    - Each handler logs the error with full context (error type, message, traceback if available)
  - Function `handle_pipeline_error(error: Exception, component: str) -> None`:
    - Log the error with the component name (e.g., "STT", "LLM", "TTS")
    - Classify error type: transient (network, rate limit) vs permanent (auth, bad config)
    - For transient errors, log a warning
    - For permanent errors (e.g., invalid API key), log an error
- Update `agent-runtime/main.py`:
  - Import and call `register_error_handlers(session)` after creating the `AgentSession`

**Acceptance Criteria:**

- [ ] `core/error_handler.py` exists with `register_error_handlers()` and `handle_pipeline_error()`
- [ ] Error handlers registered on the `AgentSession` for error events
- [ ] Errors are logged with component name and classification (transient vs permanent)
- [ ] Pipeline errors don't crash the session process silently
- [ ] `main.py` calls `register_error_handlers()` after session creation
- [ ] Error handler gracefully handles unknown/unexpected error types

**Dependencies:** Task 13.8, Task 14.4

---

## Domain 6: Agent Configuration

### Task 14.7 — Add Default Agent Settings to Configuration

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Add configuration settings for the default agent to `RuntimeSettings`. This allows the single agent's system prompt and greeting message to be configured via environment variables instead of being hardcoded in `main.py`. This is a stepping stone — in Epic 16, these will be replaced by dynamic configuration loaded from the Platform API.

**Tasks:**

- Update `agent-runtime/config/settings.py` `RuntimeSettings` class:
  - Add `DEFAULT_AGENT_INSTRUCTIONS: str = "You are a helpful voice assistant. Be concise and friendly."` — system prompt for the default agent
  - Add `DEFAULT_AGENT_GREETING: str = "Greet the user warmly and offer your assistance."` — greeting instruction for the default agent
- Update `agent-runtime/.env.example`:
  - Add `DEFAULT_AGENT_INSTRUCTIONS` and `DEFAULT_AGENT_GREETING` with default values and descriptions
- Update `agent-runtime/main.py`:
  - Use `settings.DEFAULT_AGENT_INSTRUCTIONS` and `settings.DEFAULT_AGENT_GREETING` when creating the `BaseAgent` instead of hardcoded strings

**Acceptance Criteria:**

- [ ] `config/settings.py` includes `DEFAULT_AGENT_INSTRUCTIONS` and `DEFAULT_AGENT_GREETING`
- [ ] Both settings have sensible defaults
- [ ] `.env.example` documents the new variables
- [ ] `main.py` reads agent instructions and greeting from settings
- [ ] Changing `.env` values changes agent behavior without code modification

**Dependencies:** Task 14.4

---

## Domain 7: End-to-End Verification

### Task 14.8 — End-to-End Single Agent Conversation Test

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Verify the complete single-agent conversation flow end-to-end. This is a manual integration test that confirms the entire pipeline works: user speaks → STT transcribes → LLM generates response → TTS speaks back. The test also verifies that the greeting works, `SessionContext` is initialized, lifecycle hooks fire, and errors are handled.

**Tasks:**

- Create a verification checklist and run through it:
  1. Start LiveKit Server (via docker-compose)
  2. Start Agent Runtime (`poetry run python main.py dev`)
  3. Create a room and join with a test client (LiveKit CLI or web client)
  4. Verify: agent greets the user on join (via `BaseAgent.on_enter`)
  5. Verify: speak to the agent and receive a voice response
  6. Verify: multi-turn conversation works (context is maintained across turns)
  7. Verify: `SessionContext` is accessible (check logs for user metadata)
  8. Verify: interruption handling works (speak while agent is responding)
  9. Verify: lifecycle hook logs appear (`on_enter`, `on_user_turn_completed`)
  10. Verify: disconnecting ends the session gracefully
- Document the test results and any issues found
- Add verification steps to `agent-runtime/README.md` under a "Testing" section

**Acceptance Criteria:**

- [ ] Agent greets user on session start
- [ ] User speech is transcribed and processed by the LLM
- [ ] Agent responds with voice (TTS output)
- [ ] Multi-turn conversation maintains context
- [ ] `SessionContext` is initialized with user metadata (if provided)
- [ ] Lifecycle hook logs appear in the agent runtime output
- [ ] Interruption handling works (agent stops when user speaks)
- [ ] Session ends gracefully on user disconnect
- [ ] Verification steps documented in `README.md`

**Dependencies:** Task 14.4, Task 14.6

---

## Domain 8: Documentation

### Task 14.9 — Update Documentation for Single Agent

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Update the agent runtime documentation to cover the single agent implementation. This includes documenting the `BaseAgent` class, `SessionContext`, lifecycle hooks, chat context utilities, error handling, and the end-to-end conversation flow.

**Tasks:**

- Update `agent-runtime/README.md`:
  - **Agent Architecture** section:
    - Describe the `BaseAgent` class and its relationship to the SDK's `Agent`
    - Explain `instructions` (system prompt) and `greeting` parameters
    - Document lifecycle hooks (`on_enter`, `on_user_turn_completed`) and when they fire
  - **Session Context** section:
    - Describe the `SessionContext` dataclass and its fields
    - Explain how it's passed as `userdata` and accessed by agents
    - Document helper methods (`add_observation`, `set_flag`, `get_flag`)
  - **Error Handling** section:
    - Describe how pipeline errors are caught and logged
    - Document transient vs permanent error classification
  - **Configuration** section:
    - Add `DEFAULT_AGENT_INSTRUCTIONS` and `DEFAULT_AGENT_GREETING` to the config reference
  - **Project Structure** section:
    - Update directory listing to include new files (`agents/base_agent.py`, `core/context.py`, `core/chat.py`, `core/error_handler.py`)

**Acceptance Criteria:**

- [ ] `README.md` documents `BaseAgent` class and lifecycle hooks
- [ ] `README.md` documents `SessionContext` dataclass and helper methods
- [ ] `README.md` documents error handling approach
- [ ] New configuration variables documented
- [ ] Project structure listing updated
- [ ] A new developer can understand the single-agent architecture by reading the docs

**Dependencies:** Task 14.8

---

## Recommended Execution Order

1. **Task 14.1** — Create SessionContext Dataclass
2. **Task 14.2** — Create BaseAgent Class with System Prompt
3. **Task 14.3** — Implement Agent Lifecycle Hooks
4. **Task 14.5** — Create ChatContext Helper Utilities
5. **Task 14.4** — Wire Agent and SessionContext into Entrypoint
6. **Task 14.6** — Add Voice Pipeline Error Handling
7. **Task 14.7** — Add Default Agent Settings to Configuration
8. **Task 14.8** — End-to-End Single Agent Conversation Test
9. **Task 14.9** — Update Documentation for Single Agent

---

## Definition of Done

Epic 14 is complete when:

- [x] All 9 tasks marked COMPLETED
- [x] `BaseAgent` class exists with system prompt and lifecycle hooks
- [x] `SessionContext` dataclass is initialized and passed as `userdata`
- [x] Agent greets the user on session start via `on_enter` hook
- [x] End-to-end single-agent conversation works (speak → hear response)
- [x] ChatContext is maintained across multiple conversation turns
- [x] Pipeline errors are caught, logged, and classified
- [x] Agent instructions and greeting are configurable via environment variables
- [x] Documentation is comprehensive and accurate
- [x] No regressions in Epics 1-8, 12-13
