# Epic Task Breakdown — Multi-Agent Interactive AI Platform

> **Nomenclature:** We use the term **"Epic"** — a standard industry term (from Agile/Scrum) — to refer to each high-level block of work. Each Epic represents a cohesive feature area that will later be decomposed into **10–20 individual implementation tasks (stories/tickets).**
>
> Epics are grouped by **Domain** for organizational clarity.

---

## How to Read This Document

- **Epic Title** — The name of the high-level work block.
- **Description** — What this Epic achieves and why it exists.
- **Scope** — Concrete areas of work included under this Epic.
- **Dependencies** — Which other Epics must be completed (or at least started) before this one.
- **Layer** — Which system layer this Epic primarily touches (`Frontend`, `Platform API`, `Agent Runtime`, `Infrastructure`, or `Cross-Cutting`).

---

## Domain 1: Infrastructure & Foundation

### Epic 1 — Development Environment & Monorepo Setup

**Layer:** `Cross-Cutting`
**Dependencies:** None (starting point)

**Description:**
Establish the foundational development environment, project structure, and monorepo configuration. This is the absolute minimum needed for any developer to clone, install, and start working on any layer of the platform.

**Scope:**
- Monorepo structure setup (frontend, backend API, agent runtime as separate packages/directories)
- Package managers configuration (npm/pnpm for frontend, pip/poetry for Python backend & agent)
- Shared environment variable management (`.env` structure, dotenv loading)
- Linting & formatting standards (ESLint + Prettier for TS, Ruff/Black for Python)
- Git hooks (pre-commit, commit message standards)
- `docker-compose.yml` for local development services (PostgreSQL, Redis, LiveKit Server)
- README with setup instructions
- CI pipeline skeleton (GitHub Actions / GitLab CI) — just the structure, not full CI

---

### Epic 2 — LiveKit Server Infrastructure

**Layer:** `Infrastructure`
**Dependencies:** Epic 1

**Description:**
Set up the LiveKit Server — the WebRTC SFU backbone that routes all media and data between the frontend and agent runtime. This includes both local development and production deployment configurations.

**Scope:**
- LiveKit Server deployment via Docker (local dev)
- LiveKit Server configuration (API key/secret generation, port mapping, TURN/STUN config)
- LiveKit Cloud evaluation and configuration (alternative to self-hosted)
- Webhook endpoint registration (room_started, room_finished events)
- LiveKit CLI setup for room/token debugging
- Network configuration for WebRTC (TURN server setup for production, firewall rules)
- Health check and status monitoring for the LiveKit Server
- Documentation of LiveKit SDK versions and compatibility matrix

---

### Epic 3 — Database & Cache Layer Setup

**Layer:** `Infrastructure`
**Dependencies:** Epic 1

**Description:**
Set up PostgreSQL as the primary relational data store and Redis as the ephemeral cache/session store. Define the foundational schema, migration tooling, and connection pooling.

**Scope:**
- PostgreSQL container setup in docker-compose
- Database migration tooling (Alembic for Python/SQLAlchemy)
- Initial schema design & migration: `users`, `organizations`, `sessions` tables
- Redis container setup in docker-compose
- Redis connection utilities (aioredis for async FastAPI)
- Connection pooling configuration (asyncpg pool for PostgreSQL)
- Database seeding scripts for development
- Backup and restore strategy documentation

---

## Domain 2: Platform API (Backend)

### Epic 4 — Platform API Foundation (FastAPI)

**Layer:** `Platform API`
**Dependencies:** Epic 1, Epic 3

**Description:**
Build the FastAPI application skeleton — the platform's central API that handles authentication, configuration management, and acts as the bridge between the dashboard and the agent runtime.

**Scope:**
- FastAPI project structure (routers, models, schemas, services, middleware)
- Application factory pattern & startup/shutdown lifecycle
- CORS, rate limiting, and request validation middleware
- Health check and status endpoints
- Error handling framework (structured error responses, exception handlers)
- Logging infrastructure (structured JSON logging)
- API versioning strategy (`/api/v1/...`)
- OpenAPI/Swagger documentation auto-generation
- Base Pydantic models and shared schemas

---

### Epic 5 — Authentication & Authorization System

**Layer:** `Platform API`
**Dependencies:** Epic 4

**Description:**
Implement the authentication and authorization layer for platform customers (the people who create and manage agents). This is NOT end-user auth — it's for the dashboard/admin side.

**Scope:**
- User registration and login endpoints
- Password hashing (bcrypt) and secure storage
- JWT token issuance and refresh mechanism
- Role-based access control (RBAC) model — admin, member, viewer roles
- Organization/tenant model (multi-tenancy support)
- API key management for programmatic access
- Session management and token revocation
- OAuth2/SSO integration points (Google, GitHub — structural, not full implementation)
- Rate limiting per user/org

---

### Epic 6 — Agent Definition CRUD

**Layer:** `Platform API`
**Dependencies:** Epic 4, Epic 5

**Description:**
Build the API endpoints and database models for creating, reading, updating, and deleting AI agent definitions. This is the core of what platform customers configure — the agents' personalities, tools, and behaviors.

**Scope:**
- Agent definition database schema (`agents` table: name, instructions, model, voice, tools, handoff targets)
- CRUD REST endpoints for agent definitions (`POST/GET/PUT/DELETE /api/v1/agents`)
- Agent versioning (save previous versions of agent configs for rollback)
- Agent duplication and templating
- Validation logic (e.g., handoff targets must reference existing agents, tools must exist in registry)
- Agent grouping (agent sets / agent topologies — defining which agents belong together)
- Agent-level model and voice configuration storage
- Modality needs configuration per agent (audio-only, audio+camera, audio+screenshare)
- Workspace panel assignment per agent (which panels an agent can use)
- Bulk operations (import/export agent configurations as JSON)

---

### Epic 7 — Session Template & Configuration System

**Layer:** `Platform API`
**Dependencies:** Epic 6

**Description:**
Build the session template system — the configuration blueprint that defines what happens when an end-user connects. A session template bundles together agent sets, modalities, panel permissions, and behavioral settings.

**Scope:**
- Session template database schema (`session_templates` table)
- CRUD endpoints for session templates
- Template fields: agent set reference, modality profile, enabled panels, timeout settings, max duration
- Modality profile configuration (audio-only, audio+camera, audio+screenshare combinations)
- Panel enablement configuration (which Interactive Workspace Panels are available)
- Initial agent selection (which agent greets the user)
- Environment-specific overrides (dev vs staging vs production template variants)
- Template validation (ensuring all referenced agents and tools exist)
- Template sharing and cloning across organizations

---

### Epic 8 — LiveKit Token Generation & Session Initiation

**Layer:** `Platform API`
**Dependencies:** Epic 2, Epic 7

**Description:**
Implement the endpoint that end-users call to start a session. This generates a LiveKit JWT access token with embedded metadata and creates a LiveKit room, triggering the agent runtime dispatch.

**Scope:**
- Session start endpoint (`POST /api/session/start`)
- LiveKit JWT token generation with the `livekit-api` Python SDK
- Token metadata embedding (`session_template_id`, `user_id`, `modality_profile`, `enabled_panels`)
- Room name generation strategy (unique, deterministic naming)
- Session record creation in the database (status tracking, timestamps)
- Token expiry and refresh strategy
- Access control (validating session template belongs to the requesting org)
- Rate limiting on session creation (per user, per org)
- Session listing and status query endpoints

---

### Epic 9 — Webhook Listener & Session Lifecycle Events

**Layer:** `Platform API`
**Dependencies:** Epic 4, Epic 8

**Description:**
Build the webhook listener that receives room lifecycle events from the LiveKit Server. These events drive session tracking, billing triggers, and analytics data collection.

**Scope:**
- Webhook receiver endpoint (`POST /api/webhooks/livekit`)
- Webhook signature validation (using LiveKit's signing mechanism)
- `room_started` event handling — update session status, log start time
- `room_finished` event handling — update session status, calculate duration, log end time
- `participant_joined` / `participant_left` event handling
- Event-driven session cleanup (mark sessions as completed)
- Webhook retry handling and idempotency (duplicate event protection)
- Event logging to database for audit trail
- Integration with billing/analytics pipelines (hooks for future billing system)

---

### Epic 10 — Tool Registry API

**Layer:** `Platform API`
**Dependencies:** Epic 6

**Description:**
Build the platform's tool registry — the central catalog of tools that can be assigned to agents. This includes built-in tools, panel tools (auto-generated), and custom webhook tools defined by platform customers.

**Scope:**
- Tool definition database schema (`tools` table: name, description, parameter schema, type, endpoint URL)
- Built-in tool registration (request_screen_share, request_camera, send_ui_action, search_knowledge_base, log_observation)
- Panel tool auto-generation logic (when a panel type is configured, auto-create open/control/read/close tools)
- Custom tool CRUD endpoints (platform customers define their own webhook tools)
- Tool parameter schema validation (JSON Schema format)
- Tool assignment to agents (many-to-many relationship)
- Handoff tool auto-generation (for each agent's configured handoff targets)
- Tool testing endpoint (dry-run a tool call for validation)
- Tool usage logging and analytics

---

### Epic 11 — Session Logging & History API

**Layer:** `Platform API`
**Dependencies:** Epic 9

**Description:**
Build the system that receives, stores, and serves session history — conversation logs, agent transitions, tool calls, and panel interactions. This data powers the analytics dashboard and debugging tools.

**Scope:**
- Session log ingestion endpoint (accepting structured logs from agent runtime)
- Chat history storage schema (messages, roles, timestamps, media references)
- Agent transition logging (which agent was active when, handoff events)
- Tool call logging (what tools were called, parameters, results, latency)
- Panel interaction logging (which panels opened, content snapshots, events)
- Session replay data format design
- Query endpoints for session history (with filtering, pagination)
- Session summary generation (duration, turn count, agents used, tools called)
- Data retention policies and cleanup jobs
- Export endpoints (CSV/JSON export of session data)

---

## Domain 3: Agent Runtime (LiveKit Agent Server)

### Epic 12 — Agent Runtime Foundation

**Layer:** `Agent Runtime`
**Dependencies:** Epic 2, Epic 4

**Description:**
Set up the LiveKit Agent Server — the Python process that registers with the LiveKit Server and handles room dispatch. This is the foundational runtime that all agent logic runs inside.

**Scope:**
- `livekit-agents` SDK installation and project structure
- Agent Server entrypoint (`main.py` with agent registration)
- Job subprocess lifecycle (spawn, run, terminate)
- Room event handling boilerplate (connected, disconnected, track events)
- LiveKit server connection configuration (URL, API key/secret)
- Environment variable management for the runtime
- Graceful shutdown and session draining
- Logging setup (structured logging compatible with the platform)
- Local development workflow (running the agent alongside LiveKit Server)
- Health check mechanism for the agent server process

---

### Epic 13 — AgentSession & Voice Pipeline Setup

**Layer:** `Agent Runtime`
**Dependencies:** Epic 12

**Description:**
Implement the core `AgentSession` creation and voice pipeline configuration — the STT → LLM → TTS streaming pipeline that powers every conversation. This is the heart of the agent runtime.

**Scope:**
- `AgentSession` instantiation with configurable plugins
- STT plugin integration (Deepgram Nova-2 as default, plugin-based architecture for alternatives)
- TTS plugin integration (Cartesia Sonic as default, ElevenLabs Turbo as premium option)
- LLM plugin integration (OpenAI GPT-4.1-mini as default)
- VAD integration (Silero VAD for voice activity detection)
- Turn detection configuration (LiveKit multilingual model)
- Streaming audio output (TTS → WebRTC audio track publication)
- Interruption handling (stop TTS when user speaks mid-response)
- `RoomIO` configuration and track subscription setup
- Audio input processing: noise cancellation options
- Session startup sequence (connect to room, subscribe to tracks, start pipeline)

---

### Epic 14 — Single Agent Implementation

**Layer:** `Agent Runtime`
**Dependencies:** Epic 13

**Description:**
Implement a complete single-agent experience — one agent that can listen, think, and respond. This validates the entire voice pipeline end-to-end before adding multi-agent complexity.

**Scope:**
- `Agent` class implementation with instructions (system prompt)
- `ChatContext` management (building and maintaining conversation history)
- Agent lifecycle hooks (`on_enter`, `on_user_turn_completed`)
- System prompt injection and management
- LLM response streaming and delivery
- End-to-end single-agent conversation flow (user speaks → agent responds)
- Configurable greeting on session start
- Basic error handling (LLM failures, STT failures, TTS failures)
- `SessionContext` (userdata) initialization with user profile data
- Testing framework for agent behavior (mock STT/LLM/TTS for unit tests)

---

### Epic 15 — Multi-Agent Handoff System

**Layer:** `Agent Runtime`
**Dependencies:** Epic 14

**Description:**
Implement the multi-agent handoff system — multiple agents co-existing in a session with the ability to transfer control via tool-based handoffs. This is a defining feature of the platform.

**Scope:**
- Multiple `Agent` instances co-existing in a single session
- Handoff tool generation (auto-create `transfer_to_{agent_name}` tools per agent)
- Handoff execution (tool returns new `Agent` → SDK swaps active agent)
- Context preservation on handoff (passing `ChatContext` to new agent)
- Context reset on handoff (clean slate for the new agent)
- `AgentHandoff` item recording in chat history
- `on_enter` hook for transition messages (new agent greets user after takeover)
- Agent-specific LLM overrides (different models per agent)
- Agent-specific TTS voice overrides (different voices per agent)
- Shared `SessionContext` read/write across all agents
- Handoff loop prevention (agent A → B → A infinite loop detection)
- Handoff logging (which agent was active when, transition timestamps)

---

### Epic 16 — Dynamic Configuration Loading

**Layer:** `Agent Runtime`
**Dependencies:** Epic 7, Epic 12

**Description:**
Implement the mechanism by which the Agent Runtime loads session configuration from the Platform API at job startup. Instead of hardcoded agents, the runtime dynamically instantiates agents based on the session template.

**Scope:**
- Reading `session_template_id` from room participant metadata (LiveKit JWT)
- Fetching session template from Platform API (HTTP client with retry/timeout)
- Redis cache layer for session templates (avoid API calls for repeated templates)
- Dynamic `Agent` instantiation from configuration (instructions, tools, models, voices)
- Dynamic tool registration based on agent configuration
- Dynamic modality configuration (enabling/disabling video sampler based on template)
- Configuration validation at runtime (fail fast on bad config)
- Fallback/default configuration (if API is unreachable)
- Hot-reload support (future consideration — update agents mid-session)
- Template caching invalidation strategy

---

### Epic 17 — Function Tool System

**Layer:** `Agent Runtime`
**Dependencies:** Epic 14, Epic 10

**Description:**
Build the tool execution system on the agent runtime — the mechanism by which agents call functions (API calls, database lookups, RPC to frontend, custom webhooks) as decided by the LLM.

**Scope:**
- `@function_tool` decorator usage for built-in tools
- Built-in tool implementations: `request_screen_share`, `request_camera`, `log_observation`, `send_ui_action`
- Custom webhook tool execution (calling customer-defined HTTP endpoints)
- Tool parameter validation before execution
- Tool result formatting and injection back into LLM context
- Tool timeout and error handling (what happens if a tool call fails)
- Tool call logging (parameters, result, latency)
- Concurrent tool call handling (if LLM requests multiple tools)
- Tool call rate limiting (prevent runaway tool calls)
- `search_knowledge_base` tool — RAG integration point (structural)

---

### Epic 18 — RPC Communication (Agent ↔ Frontend)

**Layer:** `Agent Runtime` + `Frontend`
**Dependencies:** Epic 17

**Description:**
Implement the RPC (Remote Procedure Call) system that allows the agent to trigger actions on the frontend — and the frontend to respond. This is how the agent "acts" on the client side.

**Scope:**
- Agent-side RPC invocation (`room.local_participant.perform_rpc()`)
- RPC method definitions (request_screen_share, request_camera, send_ui_action, open URL, show toast)
- Frontend-side RPC handler registration (`room.local_participant.register_rpc_method()`)
- RPC request/response serialization (JSON payloads)
- RPC timeout handling (frontend doesn't respond in time)
- RPC error handling (frontend rejects the request)
- Bidirectional data: frontend calling agent RPC methods
- RPC authentication (validating participant identity)
- RPC method registry discovery (agent knows what RPCs the frontend supports)
- Integration testing framework for RPC calls

---

### Epic 19 — Video & Vision Pipeline

**Layer:** `Agent Runtime`
**Dependencies:** Epic 13

**Description:**
Implement the video input pipeline — camera and screenshare track subscription, frame sampling, and injection of visual context into the LLM. This includes the cost-optimization strategies for vision.

**Scope:**
- `video_input: True` configuration in `RoomOptions`
- `VoiceActivityVideoSampler` configuration (frame rate during speech vs silence)
- Custom video sampler implementation (override sampling rates)
- Frame encoding (JPEG, resize to 1024×1024)
- Frame injection into `ChatContext` as `ImageContent`
- Camera track subscription and processing
- Screenshare track subscription and processing
- Camera vs Screenshare priority handling (most recently published track)
- Dynamic modality switching (screenshare starts/stops mid-session)
- `track_subscribed` / `track_unsubscribed` event handling
- Vision cost control: only inject frame on turn completion
- Inference detail configuration (low vs high)
- Agent-gated vision (only Vision Analyst agent gets frames)
- Disabling video sampler for audio-only agents

---

### Epic 20 — Data Channel & Byte Stream Communication

**Layer:** `Agent Runtime` + `Frontend`
**Dependencies:** Epic 12

**Description:**
Implement the Data Channel and Byte Stream communication layer — low-latency message passing between the agent and frontend beyond media tracks. This is the backbone for panel event streaming and file uploads.

**Scope:**
- Data Channel setup (agent → frontend text/binary messages)
- Data Channel setup (frontend → agent text/binary messages)
- Event message format definition (JSON schema for panel events, state updates)
- Reliable vs unreliable data channel modes
- Agent state broadcasting (thinking, listening, speaking states via data channel)
- Byte Stream receiving (user uploads document/image to agent)
- Byte Stream sending (agent sends files/data to frontend)
- Message ordering and delivery guarantees
- Data channel reconnection handling
- Payload size limits and chunking strategies

---

### Epic 21 — Session Lifecycle Management (Runtime Side)

**Layer:** `Agent Runtime`
**Dependencies:** Epic 13, Epic 14

**Description:**
Manage the full lifecycle of a session from the agent runtime's perspective — from job dispatch through active conversation to graceful shutdown and log submission.

**Scope:**
- Job dispatch handling (receiving room assignment from LiveKit)
- Session bootstrap sequence (read metadata → fetch config → create session → start pipeline)
- Participant join/leave event handling
- User away detection (silence timeout → pause expensive processing)
- Session max duration enforcement
- Graceful shutdown (drain pending speech, finalize logs)
- Session history collection (chat context, agent transitions, tool calls)
- Session log submission to Platform API
- Crash recovery and cleanup (orphaned sessions)
- Session metrics collection (duration, turn count, latency measurements)

---

## Domain 4: Frontend (Next.js)

### Epic 22 — Frontend Application Foundation

**Layer:** `Frontend`
**Dependencies:** Epic 1

**Description:**
Set up the Next.js application with the foundational structure, styling system, and routing. This is the shell that all frontend features will be built inside.

**Scope:**
- Next.js project initialization (App Router)
- Project structure (components, hooks, services, utils, types directories)
- Global styles, CSS/design system setup (color tokens, typography, spacing)
- Layout components (app shell, header, sidebar structure)
- Routing structure (pages for session, dashboard, auth)
- Environment variable management (NEXT_PUBLIC_ variables)
- Font loading (Google Fonts — Inter/Outfit)
- Responsive design foundation (breakpoints, media queries)
- Dark mode support (system preference detection, toggle)
- SEO defaults (meta tags, OG tags, favicon)

---

### Epic 23 — LiveKit Client Integration

**Layer:** `Frontend`
**Dependencies:** Epic 2, Epic 22

**Description:**
Integrate the `livekit-client` SDK into the frontend — connecting to LiveKit rooms, managing the WebRTC connection, and handling participant events. This is the real-time communication layer of the frontend.

**Scope:**
- `livekit-client` SDK installation and setup
- Room connection flow (connect with access token, handle connection states)
- Participant event handling (joined, left, track subscribed/unsubscribed)
- Connection state management (connecting, connected, reconnecting, disconnected)
- Room disconnection and cleanup
- Error handling (connection failures, token expiry, network issues)
- React context/provider for LiveKit room state
- Custom hooks for room status, participants, tracks
- Reconnection strategy (auto-reconnect with backoff)
- Connection quality monitoring

---

### Epic 24 — Audio I/O & Playback System

**Layer:** `Frontend`
**Dependencies:** Epic 23

**Description:**
Implement the audio input (microphone) and output (agent voice playback) system. This is the primary interaction modality — always active in every session.

**Scope:**
- Microphone permission request and access
- Audio track publication to LiveKit room
- Agent audio track subscription and playback
- Mute/unmute toggle for microphone
- Microphone device selection (if multiple mics available)
- Audio level visualization (voice activity indicator for user and agent)
- Audio playback interruption handling (agent stops when user speaks)
- Browser autoplay policy handling (user gesture required for audio playback)
- Audio quality settings (sample rate, echo cancellation, noise suppression)
- Fallback handling (no microphone available)

---

### Epic 25 — Camera & Screen Share Controls

**Layer:** `Frontend`
**Dependencies:** Epic 23

**Description:**
Implement the camera (webcam) and screen share publishing controls — allowing the user to share visual context with the agent on demand.

**Scope:**
- Camera permission request and video track publication
- Camera preview (local video element showing user's camera feed)
- Camera on/off toggle
- Camera device selection (if multiple cameras)
- Screen share initiation (browser native screen picker)
- Screen share track publication
- Screen share start/stop toggle
- Camera vs Screen Share priority management (which is the active video track)
- Agent-requested camera activation (responding to RPC from agent)
- Agent-requested screen share (responding to RPC — showing prompt to user)
- Modality configuration respect (hide camera button if modality is audio-only)
- Video track quality settings

---

### Epic 26 — Session UI & Agent State Display

**Layer:** `Frontend`
**Dependencies:** Epic 23, Epic 24

**Description:**
Build the session interface that displays the conversation state — which agent is active, whether the agent is listening/thinking/speaking, and the overall session status.

**Scope:**
- Session page layout (main conversation area, controls bar, side panels)
- Agent state display (listening, thinking, speaking indicators with animations)
- Active agent name and avatar display
- Agent transition animation (when handoff occurs, visually show the new agent)
- Session timer / duration display
- Connection status indicator (connected, reconnecting, lost)
- Session controls bar (mute, camera, screenshare, end session)
- End session confirmation dialog and cleanup
- Session loading state (connecting to room, waiting for agent)
- Error states (connection failed, agent unavailable)
- Responsive layout (mobile-friendly session view)

---

### Epic 27 — RPC Handler System (Frontend Side)

**Layer:** `Frontend`
**Dependencies:** Epic 23

**Description:**
Build the frontend's RPC handler infrastructure — the system that receives and executes remote procedure calls from the agent. This is how the agent triggers client-side actions.

**Scope:**
- RPC handler registration framework (register methods on room connection)
- Built-in RPC handlers: `requestScreenShare`, `requestCamera`, `openUrl`, `showToast`
- RPC handler for `openPanel` — routes to Panel Manager
- RPC handler for `controlPanel` — routes to Panel Manager
- RPC handler for `closePanel` — routes to Panel Manager
- RPC response formatting (success/error payloads)
- RPC handler error handling and logging
- User consent prompts for sensitive actions (screen share, camera)
- RPC handler registry (dynamically register/unregister handlers)
- RPC handler timeout handling

---

### Epic 28 — Panel Manager & Panel Framework

**Layer:** `Frontend`
**Dependencies:** Epic 27

**Description:**
Build the Panel Manager — the central orchestrator for Interactive Workspace Panels on the frontend. This includes the framework that all individual panels plug into, handling layout, lifecycle, and data routing.

**Scope:**
- Panel Manager architecture (registry, state management, lifecycle control)
- Panel interface definition (TypeScript interface that all panels implement)
- Panel registration on session bootstrap (based on `enabled_panels` from token metadata)
- Panel opening/closing logic (triggered by RPC from agent)
- Panel layout management (positioning, sizing, split views, maximizing/minimizing)
- Panel state synchronization (sending state changes to agent via Data Channels)
- Panel event routing (user interactions in panels → DataChannel events to agent)
- Panel data receiving (RPC commands from agent → routed to correct panel)
- React context/provider for panel state
- Panel animation (open/close transitions, resize animations)
- Panel header chrome (panel title, close button, minimize/maximize)

---

### Epic 29 — Slide Presenter Panel

**Layer:** `Frontend`
**Dependencies:** Epic 28

**Description:**
Build the Slide Presenter panel — a workspace panel that allows the agent to present slides to the user during explanations, tutorials, onboarding, or sales demos.

**Scope:**
- Slide Presenter React component
- Slide rendering (title, content/bullet points, image display)
- Slide navigation (next, previous, go-to-slide — triggered by agent RPC)
- Slide transition animations
- Slide progress indicator (slide N of M)
- User interaction events (slide_viewed, time spent per slide, link clicked)
- Agent data format: receiving slide deck as JSON array
- Responsive slide layout (adapts to panel size)
- Image loading and caching within slides
- Keyboard navigation support (arrow keys for next/previous)
- Fullscreen mode for slides

---

### Epic 30 — Notepad Panel

**Layer:** `Frontend`
**Dependencies:** Epic 28

**Description:**
Build the Notepad panel — a free-form text area where the user types answers, notes, or drafts, and the agent can read the content directly as structured text.

**Scope:**
- Notepad React component (rich text area)
- Placeholder text support (set by agent via RPC)
- Content pre-filling (agent sets initial content)
- `content_changed` event emission (debounced) to agent via Data Channel
- Agent `read_notepad` support (latest text stored and accessible)
- Character/word count display
- Basic text formatting (bold, italic, lists — optional)
- Auto-save state to SessionContext
- Clear/reset notepad action
- Copy-to-clipboard support
- Accessibility (keyboard navigation, screen reader support)

---

### Epic 31 — Coding IDE Panel

**Layer:** `Frontend`
**Dependencies:** Epic 28

**Description:**
Build the Coding IDE panel — an embedded code editor where the user writes/edits code. The agent receives the exact code text (no OCR needed), making this far superior to screenshare for coding scenarios.

**Scope:**
- Code editor component integration (Monaco Editor or CodeMirror)
- Language support configuration (Python, JavaScript, Java, C++, etc.)
- Syntax highlighting and auto-indentation
- Initial code injection (agent sets starter code via RPC)
- `code_changed` event emission to agent via Data Channel
- Line highlighting (agent highlights specific lines via RPC)
- Code read support (returning full code text to agent)
- Code execution interface (Run button — UI only, execution is a future concern)
- Multiple file/tab support (optional — v1 can be single file)
- Editor theme (dark mode, matching platform theme)
- Font size and editor settings
- Agent-driven annotations/markers on specific lines

---

### Epic 32 — Whiteboard & Document Viewer Panels

**Layer:** `Frontend`
**Dependencies:** Epic 28

**Description:**
Build the remaining workspace panels — Whiteboard for collaborative drawing and Document Viewer for presenting PDFs/contracts. These are secondary panels that extend the platform's versatility.

**Scope:**
- **Whiteboard Panel:**
  - Canvas-based drawing component (HTML5 Canvas or library like Excalidraw/Fabric.js)
  - Agent-driven drawing (receive draw commands via RPC: shapes, lines, text)
  - User free-drawing mode (pen, shapes, text)
  - Canvas export (PNG/SVG snapshot) for agent vision (the one panel that may use vision)
  - Undo/redo support
  - Clear canvas action
- **Document Viewer Panel:**
  - PDF rendering component (react-pdf or similar)
  - Page navigation (agent navigates to specific pages via RPC)
  - Section highlighting (agent highlights specific sections)
  - User interaction events (section_viewed, user_annotation)
  - Zoom controls
  - Document URL loading

---

## Domain 5: Platform Dashboard

### Epic 33 — Dashboard Foundation & Authentication UI

**Layer:** `Frontend`
**Dependencies:** Epic 5, Epic 22

**Description:**
Build the platform customer dashboard — the web interface where platform customers log in, manage their account, and access agent configuration. This Epic covers the auth flow and dashboard shell.

**Scope:**
- Login page (email/password form, error handling)
- Registration page (sign-up form with validation)
- Authentication state management (JWT storage, refresh token handling)
- Protected routes (redirect to login if unauthenticated)
- Dashboard layout (sidebar navigation, header with user info, main content area)
- Organization selector (if user belongs to multiple orgs)
- Dashboard home page (overview/stats cards — placeholder data initially)
- Logout flow and token cleanup
- Profile settings page (update name, email, password)
- Responsive dashboard layout

---

### Epic 34 — Agent Configuration Dashboard

**Layer:** `Frontend`
**Dependencies:** Epic 6, Epic 33

**Description:**
Build the dashboard pages for creating, editing, and managing AI agents. This is the primary interface platform customers use to define their agent experiences.

**Scope:**
- Agent list page (table/card view of all agents, search, filter)
- Agent creation form (name, instructions/system prompt editor, model selection, voice selection)
- Agent editing page (update and save agent configuration)
- System prompt editor (large text area with markdown preview)
- Model selector dropdown (GPT-4.1-mini, GPT-4.1, GPT-4o, Gemini, etc.)
- Voice selector (with optional voice preview/playback)
- Tool assignment UI (multi-select from available tools)
- Handoff target configuration (select which agents this agent can hand off to)
- Modality needs selector (audio-only, + camera, + screenshare)
- Panel assignment selector (Slide Presenter, Notepad, IDE, Whiteboard, Document Viewer)
- Agent topology visualization (graph view of agent handoff relationships)
- Agent delete with confirmation
- Agent version history view

---

### Epic 35 — Session Template & Deployment Dashboard

**Layer:** `Frontend`
**Dependencies:** Epic 7, Epic 34

**Description:**
Build the dashboard pages for creating session templates and deploying them. This includes the configuration of modality profiles, panel selections, and generating embed/deploy URLs.

**Scope:**
- Session template list page
- Session template creation form (select agent set, modality profile, enabled panels, timeout settings)
- Session template editing and deletion
- Deployment configuration (generate embed URL, standalone session URL)
- Embed code snippet generation (for platform customers to embed in their sites)
- Session template testing (initiate a test session from the dashboard)
- Session template analytics overview (total sessions, avg duration)
- Active sessions monitoring (live view of running sessions)
- Session history browser (search/filter past sessions, view logs)
- Session replay viewer (replay a past session's conversation — structural, playback is complex)

---

## Domain 6: Cross-Cutting Concerns

### Epic 36 — End-to-End Testing & Quality Assurance

**Layer:** `Cross-Cutting`
**Dependencies:** Epic 14, Epic 24 (minimum viable product of backend + frontend)

**Description:**
Build the testing infrastructure and write end-to-end tests that validate the complete flow — from session initiation through conversation to session end. This also includes unit and integration testing frameworks for each layer.

**Scope:**
- Unit testing framework per layer (pytest for Python, Jest/Vitest for frontend)
- Mock infrastructure (mock STT/LLM/TTS for agent runtime tests, mock LiveKit for frontend tests)
- Integration tests for Platform API endpoints (TestClient with test DB)
- Integration tests for Agent Runtime (mock LiveKit room interactions)
- End-to-end test framework (Playwright or Cypress for frontend)
- E2E test scenarios: session creation, single-agent conversation, multi-agent handoff, panel interactions
- CI pipeline integration (run tests on PR, block merge on failure)
- Code coverage reporting
- Load testing framework (simulate concurrent sessions)
- Test data management (fixtures, factories, seeding)

---

### Epic 37 — Observability & Monitoring

**Layer:** `Cross-Cutting`
**Dependencies:** Epic 21

**Description:**
Implement observability across all layers — structured logging, metrics, tracing, and alerting. This ensures the platform is debuggable and monitorable in production.

**Scope:**
- Structured logging standard (JSON format, consistent fields across all layers)
- Log aggregation setup (e.g., ELK stack, Grafana Loki — structural decisions)
- Agent state event logging (listening, thinking, speaking transitions)
- Session metrics (duration, turn count, latency, model usage, cost estimates)
- LiveKit metrics integration (room quality, jitter, packet loss)
- Error tracking integration (Sentry or similar)
- Health check dashboards (system status page)
- Alerting rules (session failures, high error rates, LiveKit disconnections)
- Distributed tracing (OpenTelemetry spans across API → Runtime → LiveKit)
- Performance profiling tools and baselines

---

### Epic 38 — Security Hardening

**Layer:** `Cross-Cutting`
**Dependencies:** Epic 5, Epic 8, Epic 18

**Description:**
Harden the security posture across all layers — token management, data encryption, input validation, and secure defaults. This is critical for a platform handling real-time media and potentially sensitive conversations.

**Scope:**
- JWT token security audit (expiry, claims validation, key rotation)
- RPC authentication (validate participant identity on all RPC calls)
- Input sanitization on all API endpoints
- HTTPS enforcement (TLS termination strategy)
- API key encryption at rest (for custom tool webhook credentials)
- Content Security Policy (CSP) headers for frontend
- CORS configuration hardening (restrict to known origins)
- Rate limiting audit across all endpoints
- Data encryption in transit and at rest (database, Redis)
- Security headers (HSTS, X-Frame-Options, X-Content-Type-Options)
- Dependency vulnerability scanning (dependabot, pip-audit)
- Secrets management strategy (vault, env encryption)

---

### Epic 39 — DevOps & Production Deployment

**Layer:** `Infrastructure`
**Dependencies:** Epic 36, Epic 37

**Description:**
Set up the production deployment pipeline — containerization, orchestration, CI/CD, and infrastructure-as-code. This takes the platform from local development to a deployable production system.

**Scope:**
- Dockerfiles for all services (Frontend, Platform API, Agent Runtime)
- Docker Compose for staging environment (all services running together)
- Kubernetes manifests (Deployments, Services, ConfigMaps, Secrets)
- Helm charts for the complete platform
- CI/CD pipeline (build, test, dockerize, deploy)
- Infrastructure-as-code (Terraform/Pulumi for cloud resources — optional)
- LiveKit Server production deployment (self-hosted or Cloud)
- Database migration strategy for production (Alembic in CI/CD)
- SSL/TLS certificate management (Let's Encrypt or AWS ACM)
- Environment management (dev, staging, production configs)
- Rollback strategy and blue-green deployment
- Auto-scaling configuration (agent server instances based on load)

---

### Epic 40 — Cost Management & Billing Infrastructure

**Layer:** `Cross-Cutting`
**Dependencies:** Epic 11, Epic 21

**Description:**
Build the infrastructure for tracking usage costs and enabling per-customer billing. This includes metering LLM usage, STT/TTS consumption, and session duration per organization.

**Scope:**
- Usage metering per session (LLM tokens in/out, STT minutes, TTS minutes, vision calls)
- Cost estimation engine (map usage metrics to $ amounts based on provider pricing)
- Per-organization usage aggregation
- Usage dashboard (show platform customers their consumption — charts, tables)
- Usage alerts (approaching limits, unusual spikes)
- Billing integration points (Stripe or similar — structural, not full implementation)
- Usage quotas and enforcement (max sessions per day, max duration)
- Cost optimization recommendations (suggest cheaper models for simple agents)
- Cost breakdown by agent (show which agents consume the most)
- Free tier / trial period management

---

## Summary Table

| # | Epic | Layer | Dependencies |
|---|------|-------|-------------|
| 1 | Development Environment & Monorepo Setup | Cross-Cutting | None |
| 2 | LiveKit Server Infrastructure | Infrastructure | 1 |
| 3 | Database & Cache Layer Setup | Infrastructure | 1 |
| 4 | Platform API Foundation (FastAPI) | Platform API | 1, 3 |
| 5 | Authentication & Authorization System | Platform API | 4 |
| 6 | Agent Definition CRUD | Platform API | 4, 5 |
| 7 | Session Template & Configuration System | Platform API | 6 |
| 8 | LiveKit Token Generation & Session Initiation | Platform API | 2, 7 |
| 9 | Webhook Listener & Session Lifecycle Events | Platform API | 4, 8 |
| 10 | Tool Registry API | Platform API | 6 |
| 11 | Session Logging & History API | Platform API | 9 |
| 12 | Agent Runtime Foundation | Agent Runtime | 2, 4 |
| 13 | AgentSession & Voice Pipeline Setup | Agent Runtime | 12 |
| 14 | Single Agent Implementation | Agent Runtime | 13 |
| 15 | Multi-Agent Handoff System | Agent Runtime | 14 |
| 16 | Dynamic Configuration Loading | Agent Runtime | 7, 12 |
| 17 | Function Tool System | Agent Runtime | 14, 10 |
| 18 | RPC Communication (Agent ↔ Frontend) | Agent Runtime + Frontend | 17 |
| 19 | Video & Vision Pipeline | Agent Runtime | 13 |
| 20 | Data Channel & Byte Stream Communication | Agent Runtime + Frontend | 12 |
| 21 | Session Lifecycle Management (Runtime Side) | Agent Runtime | 13, 14 |
| 22 | Frontend Application Foundation | Frontend | 1 |
| 23 | LiveKit Client Integration | Frontend | 2, 22 |
| 24 | Audio I/O & Playback System | Frontend | 23 |
| 25 | Camera & Screen Share Controls | Frontend | 23 |
| 26 | Session UI & Agent State Display | Frontend | 23, 24 |
| 27 | RPC Handler System (Frontend Side) | Frontend | 23 |
| 28 | Panel Manager & Panel Framework | Frontend | 27 |
| 29 | Slide Presenter Panel | Frontend | 28 |
| 30 | Notepad Panel | Frontend | 28 |
| 31 | Coding IDE Panel | Frontend | 28 |
| 32 | Whiteboard & Document Viewer Panels | Frontend | 28 |
| 33 | Dashboard Foundation & Authentication UI | Frontend | 5, 22 |
| 34 | Agent Configuration Dashboard | Frontend | 6, 33 |
| 35 | Session Template & Deployment Dashboard | Frontend | 7, 34 |
| 36 | End-to-End Testing & Quality Assurance | Cross-Cutting | 14, 24 |
| 37 | Observability & Monitoring | Cross-Cutting | 21 |
| 38 | Security Hardening | Cross-Cutting | 5, 8, 18 |
| 39 | DevOps & Production Deployment | Infrastructure | 36, 37 |
| 40 | Cost Management & Billing Infrastructure | Cross-Cutting | 11, 21 |

---

## Dependency Graph (Simplified)

```
                    ┌─────────┐
                    │ Epic 1  │  Dev Environment
                    └────┬────┘
              ┌──────────┼──────────────────┐
              ▼          ▼                  ▼
         ┌────────┐ ┌────────┐         ┌────────┐
         │ Epic 2 │ │ Epic 3 │         │Epic 22 │  Frontend Foundation
         │LiveKit │ │  DB    │         └───┬────┘
         └───┬────┘ └───┬────┘             │
             │          │            ┌─────┴─────┐
             │     ┌────▼────┐      │  Epic 23   │  LiveKit Client
             │     │ Epic 4  │      └─────┬──────┘
             │     │FastAPI  │       ┌────┴────┬────────┐
             │     └────┬────┘       ▼         ▼        ▼
             │          │       Epic 24    Epic 25   Epic 27
             │     ┌────▼────┐  Audio      Camera    RPC Handlers
             │     │ Epic 5  │    │                     │
             │     │  Auth   │    ▼                     ▼
             │     └────┬────┘  Epic 26              Epic 28
             │          │       Session UI            Panel Manager
             │     ┌────▼────┐                    ┌────┴────┬────────┐
             │     │ Epic 6  │                    ▼         ▼        ▼
             │     │Agent CRUD│               Epic 29  Epic 30   Epic 31
             │     └────┬────┘               Slides   Notepad   Code IDE
             │     ┌────▼────┐                              Epic 32
             │     │ Epic 7  │                          Whiteboard+DocViewer
             │     │Templates│
             │     └────┬────┘
             │          │
             ▼          ▼
         ┌────────────────┐       ┌──────────┐
         │    Epic 8      │       │ Epic 12  │  Agent Runtime Foundation
         │Token/Session   │       └────┬─────┘
         └───────┬────────┘            │
                 │                ┌────▼─────┐
            ┌────▼────┐          │ Epic 13  │  Voice Pipeline
            │ Epic 9  │          └────┬─────┘
            │Webhooks │               │
            └────┬────┘          ┌────▼─────┐
                 │               │ Epic 14  │  Single Agent
            ┌────▼────┐         └────┬─────┘
            │Epic 11  │         ┌────┴────┬──────────┐
            │Logging  │         ▼         ▼          ▼
            └─────────┘    Epic 15    Epic 17    Epic 19
                           Handoff    Tools      Vision
                                        │
                                   ┌────▼────┐
                                   │Epic 18  │
                                   │  RPC    │
                                   └─────────┘
```

---

## Recommended Execution Order (Phases)

While Epics can be parallelized across teams, here is a suggested ordering for a single team:

### Phase A — Foundation (Epics 1, 2, 3)
Get the dev environment, LiveKit, and database running locally.

### Phase B — Backend Core (Epics 4, 5, 6, 7, 8)
Build the Platform API with auth, agent CRUD, and session initiation.

### Phase C — Agent Runtime Core (Epics 12, 13, 14)
Get a single agent talking end-to-end.

### Phase D — Frontend Core (Epics 22, 23, 24, 26)
Build the session UI with audio in/out.

### Phase E — First Integration Milestone 🎯
Connect Frontend → Platform API → LiveKit → Agent Runtime. One agent, voice-only, end-to-end.

### Phase F — Multi-Agent & Tools (Epics 15, 16, 17, 10)
Add multi-agent handoff, dynamic config, and tool system.

### Phase G — RPC & Media (Epics 18, 19, 20, 25, 27)
Add agent↔frontend RPC, vision pipeline, camera/screenshare.

### Phase H — Panels (Epics 28, 29, 30, 31, 32)
Build the panel framework and all panel types.

### Phase I — Dashboard (Epics 33, 34, 35)
Build the platform customer dashboard.

### Phase J — Production Readiness (Epics 9, 11, 21, 36, 37, 38, 39, 40)
Webhooks, logging, testing, observability, security, deployment, billing.
