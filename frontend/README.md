# Frontend Application

The frontend is a **Next.js 14+ (App Router)** application that provides the user interface for the Live Interactive Agent platform. It connects to the Platform API for data and LiveKit for real-time media streaming.

## Prerequisites

- **Node.js**: v20 or higher
- **pnpm**: v8 or higher

## Installation

```bash
pnpm install
```

## Development

Start the development server:

```bash
pnpm dev
# or from root
make frontend-dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

- `app/` - App Router pages and layouts
  - `(auth)` - Authentication pages (Login, Signup)
  - `(dashboard)` - Main application dashboard
  - `(session)` - Live session interface (LiveKitProvider wrapper)
- `components/`
  - `ui/` - Reusable UI primitives (Button, Input, Card)
  - `layout/` - Layout components (AppShell, Sidebar, Header)
- `hooks/` - Custom React hooks (useLiveKit, useConnectionStatus, etc.)
- `services/` - API clients, LiveKit service
- `styles/` - Global CSS and design tokens
- `types/` - TypeScript definitions (livekit)
- `utils/` - Utility functions (livekit-errors)

## Design System

The application uses a **CSS Variables** based design system defined in `styles/globals.css`. It supports:

- **Colors**: Semantic tokens (`--color-primary`, `--color-background`, etc.)
- **Typography**: Inter (Sans) and Outfit (Display) fonts
- **Dark Mode**: Automatic system detection with manual toggle
- **Responsiveness**: Standard breakpoints (sm, md, lg, xl)

## Environment Variables

Copy `.env.example` to `.env.local` for development.

| Variable                  | Description                                                             |
| ------------------------- | ----------------------------------------------------------------------- |
| `NEXT_PUBLIC_LIVEKIT_URL` | WebSocket URL for LiveKit Server (default: `ws://localhost:7880`)       |
| `NEXT_PUBLIC_API_URL`     | Base URL for the Platform API (default: `http://localhost:8000/api/v1`) |

## LiveKit Integration

The frontend integrates the `livekit-client` SDK (v2.17+) for real-time WebRTC communication. This integration is modularized into services, context providers, and custom hooks.

### Architecture

- **Service (`services/livekit.ts`)**: Encapsulates raw SDK logic (`createRoom`, `connectToRoom`, `disconnectFromRoom`).
- **Context (`LiveKitProvider`)**: Manages the `Room` instance state, connection status, participants, and errors. Wrapped around the session layout (`app/(session)/layout.tsx`).
- **Hooks**:
  - `useLiveKit()`: Full access to the LiveKit context.
  - `useConnectionStatus()`: Simplified connection flags (`isConnected`, `isReconnecting`, etc.).
  - `useParticipants()`: Participant lists with `localParticipant` and `remoteParticipants` helpers.
  - `useConnectionQuality()`: Connection quality monitoring for the local user.

### Features

- **Reconnection**: Handled automatically by the SDK with UI state synchronization.
- **Error Handling**: Connection failures and token errors are classified into user-friendly messages (`utils/livekit-errors.ts`).
- **State Management**: React state reflects real-time room events (`Connected`, `Disconnected`, `ParticipantConnected`, etc.).
