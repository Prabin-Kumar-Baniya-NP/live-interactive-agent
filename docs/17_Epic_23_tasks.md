# Epic 23 — LiveKit Client Integration

## Task Breakdown

**Epic Summary:** Integrate the `livekit-client` SDK into the frontend — connecting to LiveKit rooms, managing the WebRTC connection, and handling participant events. This is the real-time communication layer of the frontend. This epic covers SDK installation, Room connection flow (connect with access token, handle connection states), participant event handling, connection state management, room disconnection and cleanup, error handling (connection failures, token expiry, network issues), React context/provider for LiveKit room state, custom hooks for room status/participants/tracks, reconnection strategy, and connection quality monitoring. This epic does NOT cover audio I/O and playback (Epic 24), camera/screenshare controls (Epic 25), session UI and agent state display (Epic 26), RPC handler system (Epic 27), or panel manager framework (Epic 28).

**Layer:** Frontend
**Dependencies:** Epic 2 (LiveKit Server Infrastructure), Epic 22 (Frontend Application Foundation)

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

## Domain 1: SDK Installation & TypeScript Types

### Task 23.1 — Install LiveKit Client SDK

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Install the `livekit-client` SDK package in the frontend workspace. This is the core JavaScript/TypeScript SDK for connecting to LiveKit rooms, managing WebRTC connections, and handling real-time communication. No additional component libraries are needed at this stage — we build our own React integration layer using the SDK directly, which gives us full control over the UI and behavior.

**Tasks:**

- Install `livekit-client` in the frontend workspace:
  - Run `pnpm --filter frontend add livekit-client`
- Verify the package is added to `frontend/package.json` under `dependencies`
- Verify the SDK imports work:
  - `import { Room, RoomEvent, ConnectionState } from 'livekit-client'`
- Verify `pnpm dev` and `pnpm build` still work without errors

**Acceptance Criteria:**

- [ ] `livekit-client` is listed in `frontend/package.json` dependencies
- [ ] `import { Room } from 'livekit-client'` resolves without TypeScript errors
- [ ] `pnpm dev` starts without errors
- [ ] `pnpm build` completes without errors

**Dependencies:** Epic 22 (Frontend Application Foundation)

---

### Task 23.2 — Define LiveKit TypeScript Types and Interfaces

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create TypeScript type definitions and interfaces for the LiveKit integration layer. These types define the shapes used throughout the React context, hooks, and service modules. They provide type safety for connection state, participant data, and room configuration. The `livekit-client` SDK exports its own types, but we define application-level types that wrap or extend them for our specific use case.

**Tasks:**

- Create `frontend/types/livekit.ts`:
  - Define `ConnectionStatus` type: `'disconnected' | 'connecting' | 'connected' | 'reconnecting'`
  - Define `RoomConnectionConfig` interface:
    - `url: string` — LiveKit server URL
    - `token: string` — LiveKit access token (JWT)
    - `options?: RoomConnectOptions` — optional SDK connect options
  - Define `ParticipantInfo` interface:
    - `identity: string` — participant identity
    - `name?: string` — participant display name
    - `metadata?: string` — participant metadata (JSON string from token)
    - `isLocal: boolean` — whether this is the local participant
  - Define `ConnectionQuality` type: `'excellent' | 'good' | 'poor' | 'unknown'`
  - Define `RoomState` interface:
    - `status: ConnectionStatus`
    - `roomName: string | null`
    - `participants: ParticipantInfo[]`
    - `connectionQuality: ConnectionQuality`
    - `error: string | null`
- Export all types from `frontend/types/index.ts`

**Acceptance Criteria:**

- [ ] `types/livekit.ts` exists with all specified types and interfaces
- [ ] `ConnectionStatus`, `RoomConnectionConfig`, `ParticipantInfo`, `ConnectionQuality`, `RoomState` are defined
- [ ] All types are exported from `types/index.ts`
- [ ] `import { RoomState, ConnectionStatus } from '@/types'` works without error
- [ ] Types align with the `livekit-client` SDK's own type definitions (no conflicts)

**Dependencies:** Task 23.1

---

## Domain 2: Room Connection Service

### Task 23.3 — Create LiveKit Room Connection Service

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create a service module that encapsulates the LiveKit room connection logic — creating a `Room` instance, connecting to the LiveKit server with an access token, and disconnecting cleanly. This service abstracts the raw `livekit-client` SDK calls into a clean API that the React context will use. It handles connection options, token-based authentication, and proper cleanup on disconnection.

**Tasks:**

- Create `frontend/services/livekit.ts`:
  - Function `createRoom(): Room`:
    - Create and return a new `Room` instance from the SDK
    - Configure default room options:
      - `adaptiveStream: true` — enables adaptive stream quality
      - `dynacast: true` — enables dynamic broadcasting (bandwidth optimization)
  - Function `connectToRoom(room: Room, url: string, token: string): Promise<void>`:
    - Connect the room instance to the LiveKit server using the provided URL and token
    - Handle and rethrow connection errors with descriptive messages
  - Function `disconnectFromRoom(room: Room): Promise<void>`:
    - Disconnect the room instance
    - Clean up any event listeners
    - Handle errors during disconnection gracefully (log but don't throw)
- Export all functions from `frontend/services/index.ts`

**Acceptance Criteria:**

- [ ] `services/livekit.ts` exists with `createRoom`, `connectToRoom`, and `disconnectFromRoom` functions
- [ ] `createRoom()` returns a configured `Room` instance with `adaptiveStream` and `dynacast` enabled
- [ ] `connectToRoom()` connects to a LiveKit server using the provided URL and token
- [ ] `disconnectFromRoom()` disconnects and cleans up without errors
- [ ] Connection errors are caught and rethrown with descriptive messages
- [ ] `import { createRoom, connectToRoom, disconnectFromRoom } from '@/services'` works

**Dependencies:** Task 23.1

---

## Domain 3: React Context & Provider

### Task 23.4 — Create LiveKit Room Context and Provider

**Status:** COMPLETED
**Estimated Effort:** L

**Description:**
Create a React context and provider component that manages the LiveKit room instance, connection state, and participant data. This is the central state management layer for all LiveKit-related functionality in the frontend. The provider wraps the session pages and exposes room state, connection/disconnection methods, and participant information to all child components via React context. It listens to SDK room events and updates state accordingly.

**Tasks:**

- Create `frontend/hooks/useLiveKit.tsx`:
  - Define `LiveKitContextType` interface:
    - `room: Room | null` — the current Room instance
    - `status: ConnectionStatus` — current connection status
    - `roomName: string | null` — current room name
    - `participants: ParticipantInfo[]` — list of participants
    - `connectionQuality: ConnectionQuality` — local connection quality
    - `error: string | null` — last error message, if any
    - `connect: (url: string, token: string) => Promise<void>` — connect to a room
    - `disconnect: () => Promise<void>` — disconnect from the room
  - Create `LiveKitContext` using `createContext`
  - Create `LiveKitProvider` component:
    - Manage `Room` instance via `useRef` (one instance per provider lifecycle)
    - Manage connection state via `useState`:
      - `status: ConnectionStatus` (default: `'disconnected'`)
      - `roomName: string | null` (default: `null`)
      - `participants: ParticipantInfo[]` (default: `[]`)
      - `connectionQuality: ConnectionQuality` (default: `'unknown'`)
      - `error: string | null` (default: `null`)
    - Implement `connect` function:
      - Set status to `'connecting'`
      - Create a room via `createRoom()` if not already created
      - Call `connectToRoom(room, url, token)`
      - On success: set status to `'connected'`, set `roomName`
      - On error: set status to `'disconnected'`, set `error`
    - Implement `disconnect` function:
      - Call `disconnectFromRoom(room)`
      - Reset all state to defaults
    - Register room event listeners in `useEffect`:
      - `RoomEvent.Connected` — update status
      - `RoomEvent.Disconnected` — update status, clean up
      - `RoomEvent.Reconnecting` — set status to `'reconnecting'`
      - `RoomEvent.Reconnected` — set status to `'connected'`
      - `RoomEvent.ParticipantConnected` — add to participants list
      - `RoomEvent.ParticipantDisconnected` — remove from participants list
      - `RoomEvent.ConnectionQualityChanged` — update connection quality for local participant
    - Clean up event listeners and disconnect on unmount
  - Create `useLiveKit()` hook:
    - Call `useContext(LiveKitContext)`
    - Throw descriptive error if used outside `LiveKitProvider`
  - All components are `'use client'` annotated

**Acceptance Criteria:**

- [ ] `hooks/useLiveKit.tsx` exists with `LiveKitProvider` and `useLiveKit` hook
- [ ] `LiveKitProvider` manages room instance, connection state, and participants
- [ ] `connect()` transitions status from `disconnected` → `connecting` → `connected`
- [ ] `disconnect()` resets all state and cleans up the room
- [ ] Room events (`Connected`, `Disconnected`, `Reconnecting`, `Reconnected`) update status correctly
- [ ] Participant events (`ParticipantConnected`, `ParticipantDisconnected`) update participant list
- [ ] Connection quality changes update the `connectionQuality` state for the local participant
- [ ] Error state is set when connection fails
- [ ] Room and event listeners are cleaned up on unmount
- [ ] `useLiveKit()` throws a descriptive error if used outside `LiveKitProvider`

**Dependencies:** Task 23.2, Task 23.3

---

### Task 23.5 — Integrate LiveKitProvider into Session Layout

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Wire the `LiveKitProvider` into the session route group layout so that all session pages have access to the LiveKit room context. The session layout (`app/(session)/layout.tsx`) wraps its children with the `LiveKitProvider`, making the `useLiveKit` hook available to all components within the session route group. The dashboard and auth route groups do NOT need the LiveKit provider.

**Tasks:**

- Update `frontend/app/(session)/layout.tsx`:
  - Import `LiveKitProvider` from `@/hooks/useLiveKit`
  - Wrap `{children}` with `<LiveKitProvider>`
  - Mark the layout as `'use client'` since it uses a client-side provider
- Verify that the session page (`/session/[id]`) can access `useLiveKit()` without error
- Verify that dashboard and auth pages are not affected

**Acceptance Criteria:**

- [ ] `app/(session)/layout.tsx` wraps children with `LiveKitProvider`
- [ ] Components within the session route group can call `useLiveKit()` without error
- [ ] Dashboard and auth pages still work without LiveKit provider
- [ ] `pnpm dev` starts without errors
- [ ] No hydration mismatch warnings

**Dependencies:** Task 23.4

---

## Domain 4: Custom Hooks

### Task 23.6 — Create useConnectionStatus Hook

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a focused custom hook that provides just the connection status from the LiveKit context. This is a convenience hook for components that only need to know the connection state (e.g., connection indicators, conditional rendering) without accessing the full LiveKit context. It derives from the `useLiveKit` context.

**Tasks:**

- Create `frontend/hooks/useConnectionStatus.ts`:
  - Import `useLiveKit` from `@/hooks/useLiveKit`
  - Return an object with:
    - `status: ConnectionStatus` — current connection status
    - `isConnected: boolean` — convenience flag (`status === 'connected'`)
    - `isConnecting: boolean` — convenience flag (`status === 'connecting'`)
    - `isReconnecting: boolean` — convenience flag (`status === 'reconnecting'`)
    - `isDisconnected: boolean` — convenience flag (`status === 'disconnected'`)
    - `error: string | null` — last error message

**Acceptance Criteria:**

- [ ] `hooks/useConnectionStatus.ts` exists with the `useConnectionStatus` hook
- [ ] Hook returns `status` and all convenience boolean flags
- [ ] `isConnected` is `true` only when status is `'connected'`
- [ ] `error` reflects the error from the LiveKit context
- [ ] Hook works within components wrapped by `LiveKitProvider`
- [ ] `import { useConnectionStatus } from '@/hooks/useConnectionStatus'` works

**Dependencies:** Task 23.4

---

### Task 23.7 — Create useParticipants Hook

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a custom hook that provides participant information from the LiveKit context. This hook returns the current list of participants and convenience methods for identifying the local participant vs remote participants (i.e., the agent). Components like the session UI (Epic 26) will use this hook to display participant information without accessing the full LiveKit context.

**Tasks:**

- Create `frontend/hooks/useParticipants.ts`:
  - Import `useLiveKit` from `@/hooks/useLiveKit`
  - Return an object with:
    - `participants: ParticipantInfo[]` — all participants
    - `localParticipant: ParticipantInfo | null` — the local user
    - `remoteParticipants: ParticipantInfo[]` — all remote participants (agents, other users)
    - `participantCount: number` — total participant count

**Acceptance Criteria:**

- [ ] `hooks/useParticipants.ts` exists with the `useParticipants` hook
- [ ] Hook returns `participants`, `localParticipant`, `remoteParticipants`, `participantCount`
- [ ] `localParticipant` filters for the participant where `isLocal === true`
- [ ] `remoteParticipants` filters for participants where `isLocal === false`
- [ ] `participantCount` matches the length of the `participants` array
- [ ] Hook works within components wrapped by `LiveKitProvider`
- [ ] `import { useParticipants } from '@/hooks/useParticipants'` works

**Dependencies:** Task 23.4

---

## Domain 5: Error Handling & Reconnection

### Task 23.8 — Add Connection Error Handling

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Enhance the `LiveKitProvider` to handle common connection failure scenarios — invalid tokens, expired tokens, network failures, and server unreachability. Each error type should produce a user-friendly error message and set the appropriate connection state. This ensures the session UI (Epic 26) can display meaningful error states to the user.

**Tasks:**

- Update `frontend/hooks/useLiveKit.tsx`:
  - In the `connect` function, wrap the connection call with error handling:
    - Catch and classify errors:
      - **Token errors** (invalid/expired JWT) → set error: `'Session token is invalid or expired. Please start a new session.'`
      - **Network errors** (connection refused, timeout) → set error: `'Unable to connect to the server. Please check your network connection.'`
      - **Server errors** (server unavailable) → set error: `'The server is currently unavailable. Please try again later.'`
      - **Unknown errors** → set error with the original error message
    - Set status to `'disconnected'` on any connection error
    - Log errors to console for debugging
  - In the room event handlers, handle `RoomEvent.Disconnected`:
    - Check the disconnect reason from the SDK
    - Set appropriate error messages for unexpected disconnections
- Create `frontend/utils/livekit-errors.ts`:
  - Function `classifyConnectionError(error: unknown): string`:
    - Analyze the error object and return a user-friendly message
    - Handle `Error`, `DOMException`, and string error types
  - Function `isTokenError(error: unknown): boolean`:
    - Check if the error relates to token validation/expiry
  - Export all functions from `frontend/utils/index.ts`

**Acceptance Criteria:**

- [ ] `utils/livekit-errors.ts` exists with `classifyConnectionError` and `isTokenError` functions
- [ ] Connection errors in `LiveKitProvider.connect()` are caught, classified, and stored in state
- [ ] Token errors produce a user-friendly message about expired/invalid session
- [ ] Network errors produce a user-friendly message about connectivity
- [ ] Unexpected disconnections update the error state with a descriptive message
- [ ] All errors are logged to console for debugging
- [ ] Connection status is set to `'disconnected'` on error
- [ ] `import { classifyConnectionError } from '@/utils'` works

**Dependencies:** Task 23.4

---

### Task 23.9 — Implement Reconnection Strategy

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
The `livekit-client` SDK has built-in reconnection support that automatically attempts to reconnect when the WebRTC connection drops. This task configures the reconnection behavior and ensures the React state layer reflects reconnection attempts accurately. The SDK handles the actual reconnection logic — we configure it and keep the UI state in sync.

**Tasks:**

- Update `frontend/services/livekit.ts`:
  - In `createRoom()`, configure reconnection options via `RoomOptions`:
    - `reconnectPolicy`: use the SDK's default reconnection policy (exponential backoff)
    - The SDK automatically handles reconnection attempts — no custom logic needed
- Update `frontend/hooks/useLiveKit.tsx`:
  - Ensure `RoomEvent.Reconnecting` handler sets status to `'reconnecting'`
  - Ensure `RoomEvent.Reconnected` handler:
    - Sets status to `'connected'`
    - Clears any previous error message
    - Refreshes the participant list (participants may have changed during disconnection)
  - Handle `RoomEvent.Disconnected` after failed reconnection:
    - Set status to `'disconnected'`
    - Set error message: `'Connection lost. Please rejoin the session.'`
- Log reconnection events for observability

**Acceptance Criteria:**

- [ ] Room is created with SDK default reconnection options enabled
- [ ] `RoomEvent.Reconnecting` sets status to `'reconnecting'`
- [ ] `RoomEvent.Reconnected` sets status to `'connected'` and clears error
- [ ] Participant list is refreshed after reconnection
- [ ] Failed reconnection (final `Disconnected` event) sets error and status to `'disconnected'`
- [ ] Reconnection events are logged to console
- [ ] No custom reconnection logic beyond SDK configuration — SDK handles retries

**Dependencies:** Task 23.4, Task 23.8

---

## Domain 6: Connection Quality Monitoring

### Task 23.10 — Implement Connection Quality Monitoring

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Implement connection quality monitoring using the SDK's `RoomEvent.ConnectionQualityChanged` event. This tracks the WebRTC connection quality (excellent, good, poor) and exposes it through the LiveKit context. The session UI (Epic 26) will use this to show a connection quality indicator to the user. Only the local participant's connection quality is tracked.

**Tasks:**

- Update `frontend/hooks/useLiveKit.tsx`:
  - In the room event listeners, handle `RoomEvent.ConnectionQualityChanged`:
    - Map the SDK's `ConnectionQuality` enum to the application's `ConnectionQuality` type:
      - `ConnectionQuality.Excellent` → `'excellent'`
      - `ConnectionQuality.Good` → `'good'`
      - `ConnectionQuality.Poor` → `'poor'`
      - `ConnectionQuality.Unknown` (or default) → `'unknown'`
    - Only update state when the event is for the local participant
    - Update the `connectionQuality` state value
- Create `frontend/hooks/useConnectionQuality.ts`:
  - Import `useLiveKit` from `@/hooks/useLiveKit`
  - Return an object with:
    - `quality: ConnectionQuality` — current connection quality
    - `isGoodConnection: boolean` — `true` when quality is `'excellent'` or `'good'`

**Acceptance Criteria:**

- [ ] `RoomEvent.ConnectionQualityChanged` handler maps SDK quality values correctly
- [ ] Only the local participant's connection quality is tracked
- [ ] `connectionQuality` state updates in the LiveKit context
- [ ] `hooks/useConnectionQuality.ts` exists with `useConnectionQuality` hook
- [ ] `isGoodConnection` returns `true` for `'excellent'` and `'good'` quality
- [ ] `import { useConnectionQuality } from '@/hooks/useConnectionQuality'` works

**Dependencies:** Task 23.4

---

## Domain 7: Hooks Barrel Export

### Task 23.11 — Update Hooks Index with LiveKit Exports

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Update the `hooks/index.ts` barrel file to export all LiveKit-related hooks for clean imports throughout the application. This follows the same pattern established in Epic 22 for the `components/ui/index.ts` barrel file.

**Tasks:**

- Update `frontend/hooks/index.ts`:
  - Export `LiveKitProvider` and `useLiveKit` from `./useLiveKit`
  - Export `useConnectionStatus` from `./useConnectionStatus`
  - Export `useParticipants` from `./useParticipants`
  - Export `useConnectionQuality` from `./useConnectionQuality`
  - Keep existing exports (`useTheme`, `ThemeProvider`)

**Acceptance Criteria:**

- [ ] `hooks/index.ts` exports all LiveKit hooks and providers
- [ ] `import { useLiveKit, LiveKitProvider } from '@/hooks'` works
- [ ] `import { useConnectionStatus } from '@/hooks'` works
- [ ] `import { useParticipants } from '@/hooks'` works
- [ ] `import { useConnectionQuality } from '@/hooks'` works
- [ ] Existing `useTheme` and `ThemeProvider` exports are preserved
- [ ] No circular import issues

**Dependencies:** Task 23.6, Task 23.7, Task 23.10

---

## Domain 8: Documentation

### Task 23.12 — Update Documentation for LiveKit Client Integration

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Update the frontend documentation to cover the LiveKit client integration. This includes documenting the service module, context/provider, custom hooks, error handling, and how to use the integration in components. Also update the project structure listing and add relevant notes to the README.

**Tasks:**

- Update `frontend/README.md`:
  - **LiveKit Integration** section:
    - Describe the `livekit-client` SDK usage and version
    - Document the `services/livekit.ts` module and its functions (`createRoom`, `connectToRoom`, `disconnectFromRoom`)
    - Document the `LiveKitProvider` and where it's integrated (session layout)
    - Document available hooks and their purposes:
      - `useLiveKit()` — full LiveKit context (room, status, connect/disconnect)
      - `useConnectionStatus()` — connection status and convenience flags
      - `useParticipants()` — participant list with local/remote filtering
      - `useConnectionQuality()` — connection quality monitoring
    - Document error handling behavior (error classification, user-friendly messages)
    - Document reconnection behavior (SDK-managed, state sync)
  - **Project Structure** section:
    - Update directory listing to include new files (`services/livekit.ts`, `hooks/useLiveKit.tsx`, `hooks/useConnectionStatus.ts`, `hooks/useParticipants.ts`, `hooks/useConnectionQuality.ts`, `types/livekit.ts`, `utils/livekit-errors.ts`)
  - **Environment Variables** section:
    - Confirm `NEXT_PUBLIC_LIVEKIT_URL` documentation is accurate

**Acceptance Criteria:**

- [ ] `README.md` documents the LiveKit client integration architecture
- [ ] All hooks are documented with their purpose and return values
- [ ] Error handling and reconnection behavior are documented
- [ ] Project structure listing is updated with new files
- [ ] A new developer can understand the LiveKit integration by reading the docs

**Dependencies:** Task 23.11

---

## Recommended Execution Order

1. **Task 23.1** — Install LiveKit Client SDK
2. **Task 23.2** — Define LiveKit TypeScript Types and Interfaces
3. **Task 23.3** — Create LiveKit Room Connection Service
4. **Task 23.4** — Create LiveKit Room Context and Provider
5. **Task 23.5** — Integrate LiveKitProvider into Session Layout
6. **Task 23.6** — Create useConnectionStatus Hook
7. **Task 23.7** — Create useParticipants Hook
8. **Task 23.8** — Add Connection Error Handling
9. **Task 23.9** — Implement Reconnection Strategy
10. **Task 23.10** — Implement Connection Quality Monitoring
11. **Task 23.11** — Update Hooks Index with LiveKit Exports
12. **Task 23.12** — Update Documentation for LiveKit Client Integration

---

## Definition of Done

Epic 23 is complete when:

- [ ] All 12 tasks marked COMPLETED
- [ ] `livekit-client` SDK is installed and imports work
- [ ] TypeScript types are defined for connection state, participants, and room configuration
- [ ] Room connection service provides `createRoom`, `connectToRoom`, `disconnectFromRoom`
- [ ] `LiveKitProvider` manages room instance, connection state, and participant list
- [ ] `LiveKitProvider` is integrated into the session route group layout
- [ ] Custom hooks available: `useLiveKit`, `useConnectionStatus`, `useParticipants`, `useConnectionQuality`
- [ ] Connection errors are classified and produce user-friendly messages
- [ ] Reconnection state transitions are handled (`reconnecting` → `connected` or `disconnected`)
- [ ] Connection quality monitoring tracks the local participant's quality
- [ ] All hooks are exported from `hooks/index.ts` barrel file
- [ ] Documentation is comprehensive and accurate
- [ ] `pnpm dev` and `pnpm build` complete without errors
- [ ] No regressions in Epics 1-8, 12-14, 22
