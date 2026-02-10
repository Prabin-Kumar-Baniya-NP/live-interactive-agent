# Low-Level Design (LLD) — Multi-Agent Interactive AI Platform

---

## 1. Design Philosophy

This platform allows **users (platform customers)** to create, configure, and deploy multiple AI agents that can **talk to, see, and interact with end-users** in real time. The core architecture must satisfy three constraints simultaneously:

1. **Low Latency** — Sub-second voice round-trip; immediate visual context when needed.
2. **Cost Effective** — Vision and multimodal models are expensive. We only activate them when genuinely needed.
3. **Multi-Agent** — Multiple specialized agents share a single session. Only one is "active" at a time, but they can hand off control seamlessly.
4. **Extensible I/O** — The system supports not just standard browser inputs (mic, camera, screenshare) but also **Interactive Workspace Panels** — rich, agent-controllable client-side tools (Slide Presenter, Notepad, Coding IDE, etc.) that serve as both input and output surfaces.

The design leans on the **LiveKit Agents SDK** as the primary runtime, using its native primitives (AgentSession, Agent, Handoff, Tools, RoomIO, Video Sampler) rather than reinventing them.

---

## 2. What LiveKit Agent SDK Gives Us (Primitives We Build On)

Before describing our platform's components, it's essential to understand what the SDK already provides out-of-the-box, because we build *on top of* these — not around them.

### 2.1 AgentSession

The main orchestrator. A single `AgentSession` per end-user session. It owns:
- The **voice pipeline** (STT → LLM → TTS), streaming audio in and out.
- The **active Agent** — which agent currently controls the conversation.
- The **video sampler** — when and how to capture frames from camera or screenshare.
- The **chat context** (`ChatContext`) — the rolling conversation history fed to the LLM.
- The **userdata** object — arbitrary typed state shared across all agents in the session.

The session runs inside a **Job** — a subprocess spawned by the Agent Server when a room is created. This means each end-user conversation is isolated at the process level.

### 2.2 Agent (The Unit of Personality & Capability)

An `Agent` is a lightweight object — not a separate server or process. It is defined by:
- **Instructions** (system prompt) — who is the agent, how should it behave.
- **Tools** (function tools) — what actions can it perform, including handing off to another agent.
- **LLM/TTS/STT overrides** — optionally, a different model or voice per agent.
- **Lifecycle hooks** — `on_enter` (when agent takes control), `on_user_turn_completed` (after user speaks).

Multiple agents exist in memory simultaneously, but only one is "active" on the session at a time. Switching is instantaneous — no network overhead, no new process. It simply swaps the system prompt, tools, and optionally the LLM/TTS plugin on the existing pipeline.

### 2.3 Agent Handoffs

Control transfer between agents happens via **tool returns**. When the LLM decides (based on conversation) that a handoff is appropriate, it calls a tool (e.g., `transfer_to_coding_expert`). The tool function returns a new `Agent` instance. The SDK automatically:
1. Records an `AgentHandoff` item in the chat history.
2. Calls `on_enter` on the new agent.
3. The new agent becomes the active controller of the session.

The previous conversation context can be **preserved** (pass `chat_ctx` to the new agent) or **reset** (clean slate), depending on the use case.

### 2.4 RoomIO & Track Management

`RoomIO` manages the WebRTC tracks between the session and the LiveKit room:
- **Audio Input** — end-user's microphone stream → fed into STT.
- **Audio Output** — TTS-generated audio → published as an audio track.
- **Video Input** — camera or screenshare track → sampled into frames for the LLM.

Key configuration via `RoomOptions`:
- `audio_input` — controls noise cancellation, mic selection.
- `video_input` — `True` or `False`. Enables the video sampler to capture frames from the most recently published video track (camera or screenshare — whichever was last).

### 2.5 Video Sampler

When `video_input` is enabled, the SDK's built-in `VoiceActivityVideoSampler` captures:
- **~1 frame/second** while the user is speaking.
- **~0.3 frames/second** during silence.

Frames are encoded as JPEG, resized to fit within 1024×1024, and injected into the LLM's chat context as image content. This is **passive** — it does not affect turn detection. Custom samplers can override the rate and encoding.

### 2.6 Tools & RPC

- **Function Tools** — Python functions decorated with `@function_tool`. The LLM decides when to call them. They can perform API calls, database lookups, or trigger agent handoffs.
- **RPC (Remote Procedure Call)** — Agent can call functions on the frontend client (e.g., "open this URL", "scroll down", "highlight this element") using `room.local_participant.perform_rpc()`. The frontend registers RPC handlers. This is how the agent "acts" on the user's machine.
- **MCP Servers** — Agents can connect to external MCP servers for tooling.

### 2.7 Data Channels & Byte Streams

Beyond media tracks, LiveKit provides:
- **Data Channels** — low-level, low-latency message passing (text/binary) between participants.
- **Byte Streams** — chunked file/image transfer from frontend to agent (e.g., user uploads a document or screenshot).

### 2.8 Agent Server Lifecycle

- Agent code registers as an **Agent Server** with the LiveKit server.
- When a room is created, LiveKit dispatches a **Job** to an available server.
- The server spawns a subprocess, runs the **entrypoint function**, which creates an `AgentSession` and starts it.
- Load balancing and horizontal scaling are handled automatically.
- Graceful shutdown drains active sessions before terminating.

---

## 3. Platform Architecture Layers

Our platform has three distinct layers, each with a clear responsibility:

```
┌──────────────────────────────────────────────────────────┐
│                    LAYER 1: FRONTEND                     │
│          (Next.js Web App — End-User Interface)          │
├──────────────────────────────────────────────────────────┤
│                    LAYER 2: PLATFORM API                 │
│      (FastAPI — User Auth, Agent CRUD, Config Store)     │
├──────────────────────────────────────────────────────────┤
│                    LAYER 3: AGENT RUNTIME                │
│   (LiveKit Agent Server — Session, Agent, Pipeline)      │
└──────────────────────────────────────────────────────────┘
        ↕ All layers communicate through LiveKit Server ↕
```

### Layer 1: Frontend (Next.js)

**What it does:**
- Connects the end-user to a LiveKit **Room** using the `livekit-client` SDK.
- Publishes the appropriate media tracks: microphone (always), camera (optional), screenshare (optional).
- Subscribes to the agent's audio track for playback.
- Renders UI state: which agent is active, whether the agent is thinking/speaking/listening.
- Registers **RPC handlers** so the agent can trigger client-side actions.
- Sends images/files to the agent via **byte streams** when needed.
- **Hosts Interactive Workspace Panels** — embeddable UI components (Slide Presenter, Notepad, Coding IDE, etc.) that the agent can open, control, and read from. These panels are rendered client-side but orchestrated by the agent via RPC and Data Channels.

**Key Decisions:**
- The frontend does NOT decide which agent is active — that's the runtime's job.
- The frontend controls which tracks are published (camera, screenshare, mic) based on the session's modality configuration, which is received from the Platform API when the session starts.
- The frontend owns a **Panel Manager** — a runtime registry of available workspace panels. Panels can be opened/closed/controlled by the agent, and their state changes are relayed back to the agent.

### Layer 2: Platform API (FastAPI)

**What it does:**
- **User Authentication** — platform customers (the people creating agents) log in here.
- **Agent CRUD** — customers create, edit, and configure their agent definitions (prompts, tools, voice, model preferences) via a dashboard.
- **Session Configuration** — when an end-user starts a session, the API determines which agent set to load, what modalities are enabled, and generates a **LiveKit access token** with embedded metadata.
- **Config Store** — PostgreSQL stores agent definitions, prompt templates, tool registries, session logs. Redis caches active session state and rate limits.
- **Webhook Listener** — receives `room_started` / `room_finished` events from LiveKit for session tracking, billing, and analytics.

**What it does NOT do:**
- It does not process audio, video, or run LLMs. That's the Agent Runtime's job.
- It does not maintain a persistent connection to the end-user. That's LiveKit's job.

### Layer 3: Agent Runtime (LiveKit Agent Server)

**What it does:**
- Runs as a persistent process registered with LiveKit.
- When dispatched to a room, spawns a **Job** subprocess.
- Inside the Job:
  1. Reads the **session metadata** from the room (which agent set, what modalities).
  2. Loads the corresponding **agent definitions** from the config store.
  3. Creates an `AgentSession` with the appropriate STT, LLM, TTS, VAD, turn detection plugins.
  4. Instantiates all **Agent** objects for this session (e.g., Triage, Coder, Vision Analyst).
  5. Sets the **initial agent** (usually a Triage/Greeting agent) and starts the session.
  6. The session then runs autonomously — agents hand off to each other based on conversation.

---

## 4. Multi-Agent System Design

### 4.1 Agent Hierarchy & Roles

Every session starts with a **Triage Agent** (the greeter/router). From there, specialized agents take over. The platform customer defines these agents via the dashboard. Example topology:

```
                    ┌──────────────┐
                    │ Triage Agent │  (entry point)
                    │  "How can I  │
                    │  help you?"  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ Coding   │  │ Vision   │  │ General  │
      │ Expert   │  │ Analyst  │  │ Chat     │
      └──────────┘  └──────────┘  └──────────┘
```

**Important:** All agents live in the **same process, same session**. Switching is a function call — not a network hop.

### 4.2 How Agents Are Defined (By Platform Customers)

A platform customer configures each agent through the dashboard with:

| Field | Description |
|-------|-------------|
| **Name** | Display name (e.g., "Coding Expert") |
| **Instructions** | System prompt — personality, rules, expertise |
| **Tools** | Which tools this agent can use (from the platform's tool registry) |
| **Handoff Targets** | Which other agents this agent can transfer to |
| **LLM Model** | Which LLM to use (can differ per agent for cost optimization) |
| **TTS Voice** | Voice identity (e.g., a specific Cartesia or ElevenLabs voice) |
| **Modality Needs** | What input it needs: audio-only, audio+camera, audio+screenshare |
| **Workspace Panels** | Which Interactive Panels this agent can use (Slide Presenter, Notepad, Coding IDE, etc.) |

At runtime, these configurations are loaded and turned into `Agent` class instances with the appropriate instructions, tools (including handoff tools), and plugin overrides.

### 4.3 How Handoff Works Step-by-Step

1. **User says something** → STT converts to text → sent to active agent's LLM.
2. **LLM reasons** about the request. If it decides the request is outside its scope, it calls a handoff tool (e.g., `transfer_to_vision_analyst`).
3. **The tool function** returns a new `Agent` instance (the Vision Analyst), optionally passing the current `chat_ctx` for context continuity.
4. **The SDK** swaps the active agent. The new agent's `on_enter` fires, generating a transition message ("Let me take a look at your screen...").
5. **The pipeline continues** — now with the Vision Analyst's instructions, tools, and optionally a different LLM or TTS.

**Context Preservation:** When preserving context, the new agent receives the full `ChatContext` (conversation history). When resetting, it gets a clean context, useful when the new agent doesn't need historical conversation (e.g., switching to a diagnostics agent that only cares about the current screen).

### 4.4 Shared Session State

A `SessionContext` dataclass (passed as `userdata` to `AgentSession`) stores:
- **User profile** — name, preferences, metadata from the access token.
- **Accumulated observations** — things any agent has learned ("user is on VS Code", "user is confused about line 42").
- **Modality state** — current active tracks (is camera on? is screenshare active?).
- **Panel state** — which workspace panels are currently open, their latest content snapshots.
- **Session flags** — custom per-use-case data (e.g., interview score, items ordered).

All agents in the session read and write to this shared state. It persists for the lifetime of the session.

---

## 5. Media Data Flow — Audio, Camera, and Screen Share

This section explains precisely how each media type flows through the system and when it is activated.

### 5.1 Audio Flow (Always Active)

Audio is the **primary modality** — it is always on in every session.

```
End-User Mic → [WebRTC] → LiveKit Server → [WebRTC] → Agent Runtime
                                                         │
                                                    STT (Streaming)
                                                         │
                                                    Text Transcript
                                                         │
                                                    LLM (Active Agent)
                                                         │
                                                    Response Text
                                                         │
                                                    TTS (Streaming)
                                                         │
Agent Runtime → [WebRTC] → LiveKit Server → [WebRTC] → End-User Speaker
```

**How it works internally:**
1. The end-user's microphone audio is published as a WebRTC audio track.
2. LiveKit's SFU forwards this to the Agent Runtime.
3. The SDK's `RoomIO` feeds the audio into the configured **STT** plugin (e.g., Deepgram, AssemblyAI) which streams back text tokens.
4. **VAD (Voice Activity Detection)** — Silero VAD detects when the user starts/stops speaking. The **Turn Detector** model identifies end-of-turn boundaries.
5. When an end-of-turn is detected, the accumulated transcript is sent to the **active agent's LLM**.
6. The LLM streams back text tokens.
7. Text tokens are streamed into the **TTS** plugin, which generates audio chunks.
8. Audio chunks are published back through LiveKit as an audio track to the end-user.

**Latency Optimizations:**
- **Streaming STT** — transcript words arrive as they're spoken, not after silence.
- **Preemptive Generation** — optionally, start LLM inference as soon as partial transcript arrives, before end-of-turn is confirmed. Reduces latency at the cost of occasional wasted inference.
- **Streaming TTS** — audio generation starts as soon as the first few LLM tokens arrive. The user hears the response before the LLM finishes generating.
- **Interruption Handling** — if the user speaks while the agent is talking, the agent stops mid-sentence. No wasted TTS or audio playback.

**Cost Consideration:**
- STT and TTS run proportionally to conversation duration. Budget ~$0.01-0.03/minute for STT+TTS combined.
- LLM costs depend on turn length and model choice. Using smaller models (GPT-4.1-mini) for simple agents and larger models only for complex reasoning agents significantly reduces cost.

### 5.2 Camera (Webcam) Flow — On-Demand, Not Always

The camera provides **visual context about the user** — facial expressions, physical environment, identity verification. It is NOT always needed.

```
End-User Webcam → [WebRTC Video Track] → LiveKit Server → Agent Runtime
                                                               │
                                                    Video Sampler (frame capture)
                                                               │
                                                    JPEG Frame (1024x1024)
                                                               │
                                                    Injected into LLM ChatContext
                                                    as ImageContent alongside text
```

**When Camera is Active:**
- The **session configuration** (set by the platform customer) specifies whether camera is needed.
- The frontend only publishes the camera track when the configuration says so.
- Agent can also request camera activation at runtime via RPC to the frontend.

**When Camera is NOT Active (most of the time):**
- **General conversation** — no visual context needed. Audio-only pipeline.
- **Screen sharing** — the screenshare track replaces camera as the video source. Running both simultaneously is wasteful unless the use case genuinely requires seeing the user AND their screen.

**How It Works When Active:**
1. Frontend publishes a camera video track.
2. The SDK's `video_input: True` in `RoomOptions` enables the video sampler.
3. The `VoiceActivityVideoSampler` captures frames at ~1fps during speech, ~0.3fps during silence.
4. Each frame is resized to fit 1024×1024 and encoded as JPEG.
5. On each user turn completion, the latest frame is appended to the `ChatContext` as `ImageContent`.
6. The LLM processes the image alongside the text transcript, giving it visual context.

**Cost Considerations:**
- Each image adds tokens to the LLM context. A 1024×1024 JPEG is roughly 500-800 tokens.
- At 1fps during a 5-minute conversation, that could be ~300 frames. Sending all of them would be extremely expensive.
- The sampler mitigates this by only injecting the **latest frame at each turn**, not every frame. So a 5-minute conversation with 20 turns adds ~20 images.
- **Inference detail** can be set to "low" for further token savings when high visual fidelity isn't needed.

### 5.3 Screen Share Flow — On-Demand, High-Value

Screen sharing provides **application context** — what the user is working on, error messages, documents open.

```
End-User Screen → [WebRTC Screen Track] → LiveKit Server → Agent Runtime
                                                                 │
                                                      Video Sampler (frame capture)
                                                                 │
                                                      JPEG Frame (1024x1024)
                                                                 │
                                                      Injected into LLM ChatContext
```

**When Screen Share is Active:**
- Explicitly triggered by the user (clicks "Share Screen" in the UI).
- Some use cases auto-request it (e.g., coding interview sessions).
- The agent can request screenshare via RPC to the frontend.

**Key Behavior — Camera vs. Screen Share Priority:**
- LiveKit's `video_input` processes the **most recently published video track**.
- If the user starts camera first, then starts screenshare → the screenshare becomes the active video input.
- If the use case requires **both simultaneously** (rare — e.g., identity verification + screen monitoring), we need to handle this at the agent level by subscribing to both tracks explicitly, not through the default video sampler.

**When Neither Camera Nor Screen Share is Needed:**
- **Basic conversation mode** — audio-only. No vision model invocation, no image tokens. This is the cheapest mode.
- The `video_input` is set to `False` in `RoomOptions`. The video sampler doesn't run. Zero vision cost.

### 5.4 Modality Decision Matrix

| Scenario | Audio | Camera | Screen Share | Video Sampler | Vision Cost |
|----------|-------|--------|-------------|---------------|-------------|
| General Chat | ✅ | ❌ | ❌ | Off | $0 |
| Interview (verbal only) | ✅ | ❌ | ❌ | Off | $0 |
| Interview (with identity) | ✅ | ✅ | ❌ | On (camera) | Medium |
| Interview (with code) | ✅ | ❌ | ✅ | On (screen) | Medium |
| Interview (full) | ✅ | ✅ | ✅ | On (screen) | Medium-High |
| IT Support (verbal) | ✅ | ❌ | ❌ | Off | $0 |
| IT Support (screen diag) | ✅ | ❌ | ✅ | On (screen) | Medium |
| Sales Demo | ✅ | ✅ | ✅ | On (screen) | Medium-High |
| Tutoring (screen review) | ✅ | ❌ | ✅ | On (screen) | Medium |

**The platform customer chooses the modality profile when configuring their agent set.** The runtime respects this configuration and only activates what's needed.

### 5.5 Dynamic Modality Switching

Modalities can change mid-session. For example:
1. Session starts as audio-only (general chat).
2. User says "Let me share my screen so you can see the error."
3. Frontend publishes screenshare track.
4. Agent Runtime detects the new video track via `track_subscribed` event.
5. Video sampler activates automatically (if `video_input` is `True`).
6. Active agent now receives visual context on next turn.

This can also work in reverse — user stops screenshare, and the pipeline gracefully falls back to audio-only without interruption.

**Agent-Driven Modality Requests:**
An agent can request modality changes via RPC:
- "Could you share your screen so I can see the error?" — agent sends RPC `requestScreenShare` to frontend.
- Frontend shows a screenshare prompt to the user.
- If user accepts, track is published and vision activates.

---

## 6. Interactive Workspace Panels

Beyond the standard browser inputs (mic, camera, screenshare), the platform provides a category of **Interactive Workspace Panels** — rich UI components embedded in the frontend that the agent can open, drive, and read from. These are the agent's "hands" on the client side.

### 6.1 The Two Categories of I/O

```
┌─────────────────────────────────────────────────────────────┐
│                      END-USER BROWSER                       │
│                                                             │
│  STANDARD BROWSER INPUTS          INTERACTIVE WORKSPACE     │
│  (Native browser APIs)            PANELS (Platform-built)   │
│  ┌─────────────────────┐          ┌───────────────────────┐ │
│  │ 🎤 Microphone       │          │ 📊 Slide Presenter    │ │
│  │ 📷 Camera           │          │ 📝 Notepad            │ │
│  │ 🖥️ Screen Share     │          │ 💻 Coding IDE         │ │
│  └─────────────────────┘          │ 📋 Whiteboard         │ │
│                                   │ 📄 Document Viewer    │ │
│  Controlled by: User              │ 🌐 Browser Preview    │ │
│  Data flow: WebRTC Tracks         │ ... (extensible)      │ │
│                                   └───────────────────────┘ │
│                                   Controlled by: Agent+User │
│                                   Data flow: RPC + DataCh.  │
└─────────────────────────────────────────────────────────────┘
```

**Standard Browser Inputs** are media streams — raw audio/video sent over WebRTC tracks. The agent processes them through STT and Vision pipelines.

**Interactive Workspace Panels** are structured UI components — they exchange **structured data** (JSON, text, file content) over RPC and Data Channels, not raw media streams. This is a critical distinction that makes them cost-effective: the agent doesn't need vision to "see" a panel's content — it receives the content as text directly.

### 6.2 Panel Architecture

Each panel follows a consistent architecture pattern:

**Panel Definition:**
| Property | Description |
|----------|-------------|
| **Panel ID** | Unique identifier (e.g., `slide_presenter`, `notepad`, `coding_ide`) |
| **Display Name** | Human-readable name shown in UI |
| **Component** | The React component that renders the panel |
| **Input Capabilities** | What structured data can be sent TO the panel (slides JSON, code text, etc.) |
| **Output Capabilities** | What structured data can be read FROM the panel (user-typed text, code edits, etc.) |
| **Agent RPC Methods** | What RPC methods the panel exposes for the agent to call |
| **Event Streams** | What events the panel emits back to the agent (content changed, slide advanced, etc.) |

**Panel Manager (Frontend):**
The frontend has a **Panel Manager** — a registry that:
- Knows all available panels for this session (configured in the Session Template).
- Opens/closes panels in response to agent RPC calls.
- Routes RPC calls from the agent to the correct panel.
- Relays panel events back to the agent via Data Channels.
- Manages layout — which panels are visible, their size and position.

### 6.3 How Panels Work — The Data Flow

**Unlike camera/screenshare, panels do NOT use WebRTC media tracks.** They use LiveKit's **RPC** and **Data Channels** for all communication. This is intentional:

- **No vision model needed** — the agent receives panel content as structured text, not pixels. A notepad sends its text content, not a screenshot.
- **Bidirectional** — the agent can both push content to a panel AND read content from it.
- **Low cost** — text over data channels costs nothing compared to vision model inference.
- **Low latency** — RPC round-trips are sub-100ms over LiveKit.

```
Agent-to-Panel Flow (Agent pushes content):

Agent Runtime                  LiveKit Server              Frontend Panel Manager
    │                               │                              │
    │──── RPC: openPanel ───────────►│─────────────────────────────►│
    │     {panel: "slides",          │                              │── Opens Slide
    │      action: "show",           │                              │   Presenter UI
    │      data: {slides: [...]}}    │                              │
    │                               │                              │
    │◄── RPC Response: {ok} ────────│◄─────────────────────────────│
    │                               │                              │
    │──── RPC: controlPanel ────────►│─────────────────────────────►│
    │     {panel: "slides",          │                              │── Advances to
    │      action: "next_slide"}     │                              │   next slide
    │                               │                              │

Panel-to-Agent Flow (User interacts, agent gets notified):

Frontend Panel                 LiveKit Server              Agent Runtime
    │                               │                              │
    │ User types in Notepad          │                              │
    │                               │                              │
    │──── DataChannel: event ───────►│─────────────────────────────►│
    │     {panel: "notepad",         │                              │── Stored in
    │      event: "content_changed", │                              │   SessionContext
    │      data: {text: "..."}}      │                              │
    │                               │                              │
    │ Agent later asks LLM           │                              │
    │ with notepad content           │                              │
    │ as context                     │                              │
```

### 6.4 Built-In Panel Types

#### Slide Presenter
- **Purpose:** Agent presents slides to the user during explanations, onboarding, tutorials, sales demos.
- **Agent → Panel:** `openPanel(slides, {slides: [{title, content, image_url}]})` — loads slide deck. `controlPanel(slides, {action: "goto", slide: 3})` — navigates to a specific slide.
- **Panel → Agent:** Events like `slide_viewed` (user saw slide N for X seconds), `slide_interaction` (user clicked a link on a slide).
- **Data flow:** The agent sends slide content as structured JSON (title, bullet points, image URLs). The panel renders them. No vision needed — the agent knows what's on each slide because it authored the content.
- **Cost impact:** Near zero. Text-only data channel messages.

#### Notepad
- **Purpose:** User types free-form text — answers, notes, drafts. Agent can read what the user typed.
- **Agent → Panel:** `openPanel(notepad, {placeholder: "Type your answer here..."})` — opens with prompt. `controlPanel(notepad, {action: "set_content", text: "..."})` — pre-fills content.
- **Panel → Agent:** `content_changed` event (debounced) with current text. Agent receives the text directly — no OCR needed.
- **When agent needs the content:** The agent calls a tool `read_notepad()` which fetches the latest text snapshot from `SessionContext.panel_state["notepad"]`. This text is injected into the LLM context as a user message.
- **Cost impact:** Near zero. Text over data channel.

#### Coding IDE
- **Purpose:** User writes/edits code. Agent can see the code, provide suggestions, verify solutions.
- **Agent → Panel:** `openPanel(coding_ide, {language: "python", initial_code: "...", instructions: "Fix the bug"})`. `controlPanel(coding_ide, {action: "highlight_lines", lines: [12, 15]})` — highlights specific lines.
- **Panel → Agent:** `code_changed` event with the full code text and language. `code_run_requested` event when user clicks "Run".
- **Key advantage over screenshare:** With screenshare, the agent would need vision model to read code from a screenshot — expensive, slow, and error-prone (OCR on code is terrible). With the Coding IDE panel, the agent receives the **exact code text** directly. Zero vision cost, zero OCR errors, instant.
- **Cost impact:** Near zero for reading code. The LLM processes the code as text tokens (far cheaper than image tokens for the same code).

#### Whiteboard
- **Purpose:** Collaborative drawing — agent or user can sketch diagrams.
- **Agent → Panel:** `openPanel(whiteboard, {})`. `controlPanel(whiteboard, {action: "draw", elements: [{type: "rect", ...}]})` — agent draws shapes.
- **Panel → Agent:** `canvas_snapshot` — periodic PNG/SVG export of the whiteboard state. This is the ONE panel type where the agent MAY need vision, since drawings are inherently visual.
- **Cost impact:** Low if snapshot-based (only when agent needs to "look"). Higher if continuous.

#### Document Viewer
- **Purpose:** Agent presents a document (PDF, contract, form) for the user to read/review.
- **Agent → Panel:** `openPanel(document_viewer, {url: "...", highlight_sections: [...]})`. Agent can highlight, annotate, and navigate sections.
- **Panel → Agent:** `section_viewed` event, `user_annotation` event.
- **Cost impact:** Near zero.

### 6.5 Panel Lifecycle

1. **Registration** — During session bootstrap, the Panel Manager on the frontend registers available panels (determined by the Session Template configuration).
2. **Opening** — The agent (via a tool) sends an RPC to open a specific panel with initial data. The Panel Manager renders the panel in the UI.
3. **Interaction** — Both agent and user interact with the panel. Agent pushes content via RPC. User interactions generate events sent back via Data Channels.
4. **State Sync** — Panel state is continuously synced to `SessionContext.panel_state` on the Agent Runtime. Any agent can read this state.
5. **Closing** — The agent sends an RPC to close the panel, or the user closes it manually. The final state snapshot is preserved in session history.

### 6.6 Why Panels Are Superior to Screenshare for Structured Content

| Aspect | Screenshare + Vision | Interactive Panels |
|--------|---------------------|-------------------|
| **How agent reads content** | Screenshot → Vision Model → OCR/Analysis | Direct structured data (text/JSON) |
| **Latency to read** | 1-3 seconds (vision inference) | <100ms (data channel) |
| **Cost per read** | 500-800 tokens per image | ~0 (text over data channel) |
| **Accuracy** | OCR errors on code, small text | 100% accurate (exact text) |
| **Agent can write/control** | Cannot control user's screen | Full control (push content, navigate) |
| **Requires user setup** | User must share screen | Auto-opens in the session UI |

**When to still use screenshare:** When the user is working in an **external application** that isn't a platform panel (e.g., their own VS Code, a third-party website, Excel). The agent needs vision for those because it can't access structured data from external apps.

### 6.7 How Agents Use Panels (Tool Integration)

Panels are exposed to agents as **tools** in the tool registry:

- `open_slide_presenter` — opens the Slide Presenter with a slide deck.
- `advance_slide` — moves to next/previous/specific slide.
- `open_notepad` — opens the Notepad with an optional prompt.
- `read_notepad` — returns the current text content from the notepad.
- `open_coding_ide` — opens the IDE with a language and optional starter code.
- `read_code` — returns the current code from the IDE.
- `highlight_code_lines` — highlights specific lines in the IDE.
- `open_whiteboard` — opens a blank whiteboard.
- `close_panel` — closes any open panel.

The LLM decides when to call these tools based on the conversation context. For example:
- User says "Can you explain how merge sort works?" → Agent calls `open_slide_presenter` with a merge sort explanation deck, then talks through each slide using `advance_slide`.
- Agent says "Try writing the function yourself" → calls `open_coding_ide` with a Python template. User writes code. Agent calls `read_code` to review it.
- Agent says "Take some notes on this" → calls `open_notepad`. User types. Agent later calls `read_notepad` to review.

### 6.8 Panel Data Flow with Audio (Combined Experience)

A typical interaction combining voice + panels looks like this:

```
Timeline:

[00:00] Agent (voice): "Let me walk you through merge sort."
[00:02] Agent (tool):   open_slide_presenter({slides: [...]})  →  Panel opens on client
[00:03] Agent (voice): "As you can see on slide 1, merge sort divides the array..."
[00:15] Agent (tool):   advance_slide(2)  →  Panel shows slide 2
[00:16] Agent (voice): "Now on step 2, we merge the sorted halves..."
[00:30] Agent (voice): "Now try implementing it yourself."
[00:31] Agent (tool):   close_panel(slides) + open_coding_ide({lang: "python"})  →  IDE opens
[00:45] User types code in IDE...
[00:46] Panel → Agent:  code_changed event → stored in SessionContext
[01:00] User (voice):  "I think I'm done, can you check?"
[01:01] Agent (tool):   read_code()  →  Returns code text
[01:02] Agent (LLM):   Analyzes code text (as text tokens, NOT image tokens)
[01:03] Agent (voice): "Almost! You have an off-by-one error on line 7..."
[01:04] Agent (tool):   highlight_code_lines([7])  →  IDE highlights line 7
```

Notice: **No vision model was used at any point.** All content exchange is structured text. The entire interaction runs on the audio pipeline + text-based panel communication.

### 6.9 Extensibility — Adding New Panel Types

The panel system is designed to be extensible. Adding a new panel type requires:
1. **Frontend:** Build a new React component that implements the Panel interface (receives RPC commands, emits events).
2. **Platform API:** Register the panel type with its capabilities in the panel registry.
3. **Agent Runtime:** Add corresponding tools to the tool registry.
4. **Dashboard:** Platform customers can now assign the new panel to their agents.

No changes to the core pipeline, LiveKit integration, or agent handoff system. Panels are a purely additive feature layer.

---

## 7. Session Lifecycle (End-to-End)

### Phase 0: Configuration (Before Any Session)

1. Platform customer logs into dashboard.
2. Creates agent definitions (Triage, Specialist A, Specialist B) with prompts, tools, voices.
3. Configures session modality (audio-only, audio+camera, audio+screen, etc.).
4. **Selects which Workspace Panels** are available for this session template (Slide Presenter, Notepad, Coding IDE, etc.).
5. Platform API stores this as a **Session Template** in PostgreSQL.

### Phase 1: Session Initiation

1. End-user visits the platform customer's deployment (embedded widget or standalone page).
2. Frontend requests an access token from the **Platform API**.
3. API generates a **LiveKit JWT** with metadata:
   - `session_template_id` — which agent set and config to load.
   - `user_id` — for personalization and logging.
   - `modality_profile` — which tracks to publish.
   - `enabled_panels` — which Workspace Panels the frontend should register.
4. Frontend uses this token to **connect to a LiveKit Room** via `livekit-client`.
5. **Frontend Panel Manager registers** all enabled panels and their RPC handlers.
6. LiveKit Server dispatches a **Job** to an available **Agent Server**.

### Phase 2: Agent Runtime Bootstrap

1. Job subprocess starts. Entrypoint function runs.
2. Reads `session_template_id` from the room participant metadata.
3. Fetches the session template from the config store (API call or Redis cache).
4. Instantiates all agent objects: `TriageAgent`, `CodingExpert`, `VisionAnalyst`, etc.
5. Registers **panel tools** (e.g., `open_slide_presenter`, `read_notepad`, `open_coding_ide`) for agents that have panel access configured.
6. Creates `AgentSession` with:
   - STT, LLM, TTS, VAD, Turn Detection plugins (as specified in the template).
   - `userdata` → `SessionContext` with user profile, initial state, and empty `panel_state`.
   - `video_sampler` → configured based on modality profile.
7. Starts the session with the `TriageAgent` as the initial active agent.
8. `TriageAgent.on_enter()` fires → generates a greeting via TTS.

### Phase 3: Conversation Loop

Once the session is running, the pipeline operates in a continuous loop:

```
User speaks → VAD detects speech → STT streams transcript
    → Turn Detector identifies end-of-turn
    → (Optional) Latest video frame attached
    → (Optional) Latest panel state snapshots attached (if relevant)
    → Active Agent's LLM processes: [instructions + chat_ctx + tools + transcript + (image) + (panel data)]
    → LLM generates response OR tool call
        IF tool call:
            → Execute tool (API call, RPC, handoff, panel control)
            → IF panel tool: RPC to frontend → Panel Manager executes → result returned
            → IF handoff: swap active agent, fire on_enter
            → Feed tool result back to LLM
        IF text response:
            → Stream to TTS
            → Audio published to user
    → Loop

    Meanwhile (async): Panel events from frontend → stored in SessionContext.panel_state
```

### Phase 4: Session End

1. End-user disconnects (closes browser, navigates away).
2. LiveKit detects the last non-agent participant has left.
3. Room closes. Agent Runtime receives close event.
4. Session performs graceful shutdown:
   - Drains pending speech.
   - Logs session history (chat context, agent transitions, tool calls) to the database via Platform API.
   - Job process terminates.

---

## 8. Cost Optimization Strategies

### 8.1 Tiered LLM Usage

Not all agents need GPT-4o. Use model size appropriate to the task:

| Agent Type | Recommended LLM | Rationale |
|-----------|-----------------|-----------|
| Triage / Greeter | GPT-4.1-mini or GPT-4.1-nano | Simple routing, no complex reasoning |
| General Chat | GPT-4.1-mini | Conversational, moderate reasoning |
| Coding Expert | GPT-4.1 or Claude | Complex reasoning, code analysis |
| Vision Analyst | GPT-4o or Gemini 2.0 Flash | Multimodal, needs vision |

**Agent-level LLM overrides** (supported by the SDK) make this trivial. Each agent can specify its own LLM.

### 8.2 Vision Cost Control

- **Default to audio-only**. Most conversation turns don't need visual context.
- **Frame sampling rate** — default 1fps is already conservative. For cost-critical deployments, drop to 0.5fps or lower.
- **Inference detail "low"** — halves token count per image with minimal quality loss for most use cases.
- **Only capture on turn completion** — don't send frames during silence or mid-speech. Only attach the latest frame when the LLM is actually being invoked.
- **Agent-gated vision** — the Vision Analyst agent is the only one that uses vision. Other agents don't get frames, even if a video track is active. This is controlled by configuring `video_input` only when the Vision Analyst is active (done by overriding `RoomOptions` or managing the sampler state on handoff).

### 8.3 Panel Cost Advantage

- **Panels replace vision for structured content.** A coding agent reading code via the Coding IDE panel costs zero vision tokens. The same code read via screenshare would cost 500-800 image tokens per turn.
- **Panels are text-based.** Data channel messages are free. LLM processes panel content as text tokens (far cheaper than image tokens for equivalent information).
- **Panels reduce STT ambiguity.** When a user types an answer in the Notepad instead of speaking it, there's no STT cost and no transcription errors.

### 8.4 STT/TTS Selection

- **Deepgram Nova-2** for STT — fast, accurate, cost-effective WebSocket streaming.
- **Cartesia Sonic** for TTS — low-latency, reasonable quality. For premium voices, ElevenLabs Turbo.
- **Silero VAD** — runs locally, zero API cost.
- **Preemptive generation** — enable only for latency-critical scenarios (e.g., sales demos). Disable for cost-critical scenarios (e.g., tutoring).

### 8.5 Session Timeout & Cleanup

- **User away timeout** — if the user is silent for 15 seconds (configurable), set user state to "away". Optionally pause expensive processing.
- **Max session duration** — hard limit configurable per template. Prevents runaway costs.
- **Idle agent downscaling** — Agent Servers that have no active jobs consume minimal resources. The SDK's automatic load balancing handles this.

---

## 9. Tool System Design

### 9.1 Platform Tool Registry

The platform maintains a **global registry of tools** that platform customers can assign to their agents:

- **Built-in Tools** — provided by the platform:
  - `request_screen_share` — sends RPC to frontend to prompt screenshare.
  - `request_camera` — sends RPC to frontend to prompt camera.
  - `send_ui_action` — sends structured RPC to frontend (open URL, highlight element, show toast).
  - `search_knowledge_base` — RAG lookup against uploaded documents.
  - `log_observation` — writes to the shared `SessionContext.observations`.

- **Panel Tools** — auto-generated for each enabled workspace panel:
  - `open_{panel_id}` — opens the panel on the frontend with initial data.
  - `control_{panel_id}` — sends commands to an open panel (navigate, highlight, set content).
  - `read_{panel_id}` — reads the current content/state from a panel.
  - `close_panel` — closes any open panel.
  - These tools internally use RPC to communicate with the frontend Panel Manager.

- **Custom Tools** — defined by the platform customer:
  - Configured via dashboard with: name, description, parameter schema, endpoint URL.
  - At runtime, the tool calls the customer's webhook endpoint with the parameters.
  - Response is fed back to the LLM.

- **Handoff Tools** — auto-generated for each agent:
  - For every handoff target configured, a `transfer_to_{agent_name}` tool is created.
  - The tool function returns the target `Agent` instance with optional context preservation.

### 9.2 Tool Forwarding to Frontend

For actions that require client-side execution (e.g., "open the settings page", "show a slide", "open the IDE"):

1. Agent calls a tool (e.g., `open_coding_ide`, `send_ui_action`, `advance_slide`).
2. Tool function uses RPC to call the frontend Panel Manager or RPC handler.
3. Frontend executes the action (opens panel, updates UI, navigates slides).
4. Frontend returns a success/failure response.
5. Response is fed back to the LLM as the tool result.

This is how the agent **interacts with the client-side workspace** — through structured RPC calls, not by controlling the user's screen.

---

## 10. Data Flow Diagram (Complete)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                            END-USER BROWSER                              │
│                                                                          │
│  STANDARD BROWSER INPUTS              INTERACTIVE WORKSPACE PANELS       │
│  ┌──────────┐ ┌────────┐ ┌─────────┐  ┌────────┐ ┌───────┐ ┌────────┐  │
│  │   Mic    │ │ Camera │ │ Screen  │  │ Slides │ │Notepad│ │Code IDE│  │
│  │  (Audio) │ │ (Video)│ │ Share   │  │Presenter│ │       │ │        │  │
│  └────┬─────┘ └───┬────┘ └───┬─────┘  └───┬────┘ └───┬───┘ └───┬────┘  │
│       │           │          │             │          │          │       │
│       └───────────┴──────────┘             └──────────┴──────────┘       │
│              │ WebRTC Tracks                    │ RPC + DataChannels     │
│              ▼                                  ▼                 ▲      │
├─────────────────────────────────────────────────┬─────────────────┤      │
│                  LIVEKIT SERVER (SFU)            │   DataChannel   │      │
│           Routes tracks, RPC, data              │   Routing       │      │
├─────────────────────────────────────────────────┴─────────────────┤      │
│                   AGENT RUNTIME (Job Process)                      │      │
│                                                                    │      │
│  ┌──────────────────────────────────────────────────────────────┐  │      │
│  │                      AgentSession                            │  │      │
│  │                                                              │  │      │
│  │  Audio In ───► STT ───► Transcript                           │  │      │
│  │                              │                               │  │      │
│  │  Video In ──► Sampler ──► Frame (JPEG)                       │  │      │
│  │                              │                               │  │      │
│  │  Panel Events ──► SessionContext.panel_state (structured text)│  │      │
│  │                              │                               │  │      │
│  │                    ┌─────────▼──────────┐                    │  │      │
│  │                    │    Active Agent     │                    │  │      │
│  │                    │  (Instructions +   │                    │  │      │
│  │                    │   Tools + LLM)     │                    │  │      │
│  │                    └─────────┬──────────┘                    │  │      │
│  │                              │                               │  │      │
│  │         ┌────────────────────┼──────────────────┐            │  │      │
│  │         ▼          ▼        ▼         ▼        ▼            │  │      │
│  │    Text Resp   Tool Call  Handoff  Panel Tool  Read Panel   │  │      │
│  │         │          │        │         │          │            │  │      │
│  │         ▼          ▼        ▼         ▼          ▼            │  │      │
│  │      TTS→Audio  Execute   Swap    RPC to      Return text   │  │      │
│  │         │      (API/DB)  Agent   Frontend      from state   │  │      │
│  │         ▼                          │                         │  │      │
│  │    Audio Out                       └──── Panel opens/updates─┼──┼──────┘
│  │         │                                                    │  │
│  └─────────┼────────────────────────────────────────────────────┘  │
│            ▼                                                       │
├────────────────────────────────────────────────────────────────────┤
│                     LIVEKIT SERVER (SFU)                           │
├────────────────────────────────────────────────────────────────────┤
│                       END-USER BROWSER                             │
│           ┌──────────┐  ┌──────────────┐  ┌───────────────────┐   │
│           │  Speaker │  │  UI Updates  │  │ Workspace Panels  │   │
│           │ (Audio)  │  │  (via RPC)   │  │ (Slides/Notepad/  │   │
│           │          │  │              │  │  IDE/Whiteboard)   │   │
│           └──────────┘  └──────────────┘  └───────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

---

## 11. Component Interaction Details

### 11.1 Frontend ↔ Platform API

| Interaction | Method | Data |
|------------|--------|------|
| User initiates session | `POST /api/session/start` | `{ template_id, user_info }` |
| API returns connection info | Response | `{ livekit_url, access_token, modality_config, enabled_panels }` |
| Frontend queries session state | `GET /api/session/{id}/status` | Session metadata |
| Session logs submitted | `POST /api/session/{id}/log` | Chat history, panel interactions, events |

### 11.2 Platform API ↔ Agent Runtime

| Interaction | Method | Data |
|------------|--------|------|
| Runtime reads session config | HTTP GET to API (or Redis cache) | `{ agents[], tools[], panels[], modality, models }` |
| Runtime logs events | HTTP POST to API | `{ agent_transitions, tool_calls, panel_events, timestamps }` |
| Webhook: room lifecycle | LiveKit webhook → API | `{ room_started, room_finished }` |

### 11.3 Agent Runtime ↔ Frontend (via LiveKit)

| Interaction | Channel | Data |
|------------|---------|------|
| User voice → Agent | WebRTC Audio Track | Raw audio stream |
| Agent voice → User | WebRTC Audio Track | TTS-generated audio stream |
| User camera/screen → Agent | WebRTC Video Track | Video frames (sampled) |
| Agent opens/controls panel | RPC (over DataChannel) | `{ panel_id, action, data }` |
| Panel state → Agent | DataChannel (event stream) | `{ panel_id, event, data }` |
| Agent triggers UI action | RPC (over DataChannel) | `{ method, params }` |
| Agent state updates | DataChannel (text) | `{ agent_name, state: thinking/speaking }` |
| User uploads image/file | Byte Stream | Binary data chunks |

---

## 12. Technology Stack Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Frontend** | Next.js + `livekit-client` SDK | SSR, React ecosystem, native LiveKit integration |
| **Platform API** | Python FastAPI | Async, high-performance, shares Python ecosystem with Agent Runtime |
| **Database** | PostgreSQL | Relational data: users, templates, logs |
| **Cache** | Redis | Ephemeral data: session state, token cache, rate limits |
| **Agent Runtime** | `livekit-agents` SDK (Python) | Native LiveKit integration, built-in voice pipeline, multi-agent handoff |
| **LiveKit Server** | Self-hosted (Docker) or LiveKit Cloud | WebRTC SFU, room management, agent dispatch |
| **STT** | Deepgram Nova-2 (default), AssemblyAI (alternative) | Low-latency streaming, cost-effective |
| **TTS** | Cartesia Sonic (default), ElevenLabs Turbo (premium) | Fast generation, natural voices |
| **LLM** | OpenAI GPT-4.1-mini (default), GPT-4o (vision), Gemini 2.0 Flash (alternative) | Tiered by agent complexity |
| **VAD** | Silero VAD | Local, zero API cost, accurate |
| **Turn Detection** | LiveKit Multilingual Model | Native SDK integration, state-of-the-art |

---

## 13. Scaling & Production Considerations

### 13.1 Horizontal Scaling

- **Agent Servers** support multiple concurrent jobs, each isolated in its own process.
- New Agent Server instances can be spun up to handle load. LiveKit auto-distributes jobs.
- **Kubernetes** deployment is natively supported by the SDK with Helm charts.

### 13.2 Fault Isolation

- Each session runs in its own subprocess. A crash in one session does not affect others.
- Agent Server graceful shutdown drains active sessions before terminating.

### 13.3 Observability

- **Agent state events** — `agent_state_changed` (listening, thinking, speaking) are emitted and can be logged.
- **Session history** — full chat context, agent transitions, tool calls are logged per session.
- **LiveKit metrics** — room duration, participant count, track quality, jitter, packet loss.

### 13.4 Security

- Access tokens are short-lived JWTs signed with API keys.
- Agent metadata is embedded in tokens — the runtime validates it.
- RPC calls between agent and frontend are authenticated via LiveKit's participant identity.
- Custom tools that call external endpoints use per-customer API keys stored encrypted in the database.

---

## 14. Summary of Key Design Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Multi-agent via SDK handoffs, not separate processes | In-process agent swapping | Zero-latency handoff, shared memory state |
| Audio-only as default modality | Camera/screen opt-in | Cost-effective; vision adds significant LLM token cost |
| Video sampler on turn completion only | Not continuous streaming | 20 images per session vs 300; massive cost reduction |
| Tiered LLM models per agent | Mini for simple, full for complex | 5-10x cost difference between models |
| Interactive Panels over screenshare for structured content | RPC + text, not vision | Near-zero cost vs 500-800 image tokens; 100% accuracy vs OCR errors |
| Panels as agent-controlled tools | Tool → RPC → Panel Manager | LLM decides when to open/read panels; natural integration with conversation |
| RPC for client-side actions | Not direct machine control | Secure, sandboxed, user-consented |
| Config-driven agent definitions | Dashboard → Database → Runtime | New use cases without code changes |
| LiveKit as the backbone | Not custom WebRTC | Production-ready SFU, agent SDK, load balancing out of the box |
