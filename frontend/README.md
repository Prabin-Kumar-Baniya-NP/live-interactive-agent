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
  - `(session)` - Live session interface
- `components/`
  - `ui/` - Reusable UI primitives (Button, Input, Card)
  - `layout/` - Layout components (AppShell, Sidebar, Header)
- `hooks/` - Custom React hooks (useTheme, etc.)
- `services/` - API clients and configuration
- `styles/` - Global CSS and design tokens
- `types/` - TypeScript definitions

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
