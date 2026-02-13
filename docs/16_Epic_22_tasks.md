# Epic 22 — Frontend Application Foundation

## Task Breakdown

**Epic Summary:** Set up the Next.js application with the foundational structure, styling system, and routing. This is the shell that all frontend features will be built inside. This epic covers project structure creation, global CSS/design system setup (color tokens, typography, spacing), layout components (app shell, header, sidebar), routing structure, environment variable management, font loading, responsive design foundation, dark mode support, and SEO defaults. This epic does NOT cover LiveKit client integration (Epic 23), audio I/O (Epic 24), camera/screenshare controls (Epic 25), session UI (Epic 26), RPC handlers (Epic 27), or panel framework (Epic 28).

**Layer:** Frontend
**Dependencies:** Epic 1 (Development Environment & Monorepo Setup)

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

## Domain 1: Project Structure

### Task 22.1 — Create Frontend Directory Structure

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create the standard directory structure for the Next.js frontend application under `frontend/`. The project is already initialized with Next.js App Router (Epic 1), but the internal directory structure for components, hooks, services, utilities, and types needs to be created. This follows standard Next.js conventions and mirrors the organizational approach used in the backend and agent-runtime packages.

**Tasks:**

- Create the following directory structure under `frontend/`:
  ```
  frontend/
  ├── app/                        # Next.js App Router (already exists)
  │   ├── layout.tsx              # Root layout (already exists)
  │   ├── page.tsx                # Home page (already exists)
  │   ├── (auth)/                 # Auth route group (login, signup pages)
  │   │   └── layout.tsx
  │   ├── (dashboard)/            # Dashboard route group
  │   │   └── layout.tsx
  │   └── (session)/              # Session route group (live AI session)
  │       └── layout.tsx
  ├── components/                 # Reusable UI components
  │   ├── ui/                     # Base UI primitives (buttons, inputs, cards)
  │   └── layout/                 # Layout components (header, sidebar, shell)
  ├── hooks/                      # Custom React hooks
  ├── services/                   # API client and service modules
  ├── utils/                      # Utility/helper functions
  ├── types/                      # TypeScript type definitions and interfaces
  ├── styles/                     # Global CSS and design tokens
  └── public/                     # Static assets (favicon, images)
  ```
- Add placeholder `index.ts` barrel files in `components/`, `hooks/`, `services/`, `utils/`, `types/` for clean imports
- Create `.gitkeep` in empty directories if needed

**Acceptance Criteria:**

- [ ] All directories created as specified
- [ ] Route groups `(auth)`, `(dashboard)`, `(session)` exist under `app/`
- [ ] Each route group has a placeholder `layout.tsx`
- [ ] `components/ui/`, `components/layout/` subdirectories exist
- [ ] `hooks/`, `services/`, `utils/`, `types/`, `styles/` directories exist
- [ ] `public/` directory exists for static assets
- [ ] `pnpm dev` still starts without errors after changes

**Dependencies:** Epic 1 (Next.js initialized)

---

### Task 22.2 — Configure Path Aliases

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Configure TypeScript path aliases in `tsconfig.json` to enable clean imports across the project. This avoids deep relative imports (e.g., `../../../components/ui/Button`) and follows Next.js conventions for path mapping.

**Tasks:**

- Update `frontend/tsconfig.json`:
  - Add `baseUrl: "."` to `compilerOptions`
  - Add `paths` mapping:
    ```json
    {
      "@/*": ["./*"],
      "@/components/*": ["components/*"],
      "@/hooks/*": ["hooks/*"],
      "@/services/*": ["services/*"],
      "@/utils/*": ["utils/*"],
      "@/types/*": ["types/*"],
      "@/styles/*": ["styles/*"]
    }
    ```
- Verify that imports using `@/` prefix resolve correctly
- Update existing `app/layout.tsx` and `app/page.tsx` if they have any imports to use the new aliases

**Acceptance Criteria:**

- [ ] `tsconfig.json` includes `baseUrl` and `paths` configuration
- [ ] Imports using `@/components/...` resolve correctly
- [ ] Imports using `@/hooks/...`, `@/services/...`, `@/utils/...`, `@/types/...` resolve correctly
- [ ] `pnpm dev` starts without TypeScript errors
- [ ] `pnpm build` completes without path resolution errors

**Dependencies:** Task 22.1

---

## Domain 2: Design System & Global Styles

### Task 22.3 — Create CSS Design System (Color Tokens, Typography, Spacing)

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the global CSS design system that defines all design tokens — colors, typography, spacing, border radii, shadows, and transitions. This uses CSS custom properties (variables) for theming and consistency. The design system supports both light and dark modes via CSS variable overrides. This is the foundation that all components and pages will reference.

**Tasks:**

- Create `frontend/styles/globals.css`:
  - Define CSS custom properties under `:root` for light mode:
    - **Colors:** `--color-primary`, `--color-primary-hover`, `--color-secondary`, `--color-background`, `--color-surface`, `--color-surface-hover`, `--color-text-primary`, `--color-text-secondary`, `--color-text-muted`, `--color-border`, `--color-error`, `--color-success`, `--color-warning`
    - **Typography:** `--font-family-sans`, `--font-family-mono`, `--font-size-xs` through `--font-size-3xl`, `--font-weight-regular`, `--font-weight-medium`, `--font-weight-semibold`, `--font-weight-bold`, `--line-height-tight`, `--line-height-normal`, `--line-height-relaxed`
    - **Spacing:** `--spacing-xs` through `--spacing-3xl` (4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px)
    - **Border radius:** `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-full`
    - **Shadows:** `--shadow-sm`, `--shadow-md`, `--shadow-lg`
    - **Transitions:** `--transition-fast`, `--transition-normal`, `--transition-slow`
  - Define dark mode overrides under `[data-theme="dark"]` or `@media (prefers-color-scheme: dark)`:
    - Override color tokens for dark backgrounds, light text, darker surfaces
  - Add global resets (box-sizing, margin, padding, font smoothing)
  - Set `body` base styles using design tokens
- Import `globals.css` in the root `app/layout.tsx`

**Acceptance Criteria:**

- [ ] `styles/globals.css` exists with all design tokens defined as CSS custom properties
- [ ] Light mode color palette is defined under `:root`
- [ ] Dark mode color overrides are defined
- [ ] Typography tokens (font sizes, weights, line heights) are defined
- [ ] Spacing scale is defined (xs through 3xl)
- [ ] Border radius, shadow, and transition tokens are defined
- [ ] Global CSS reset is applied (box-sizing, margin, padding)
- [ ] `body` uses design tokens for base styling
- [ ] `globals.css` is imported in `app/layout.tsx`
- [ ] `pnpm dev` renders the page with the new global styles applied

**Dependencies:** Task 22.1

---

### Task 22.4 — Load Google Fonts (Inter & Outfit)

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Configure Google Fonts loading using Next.js's built-in `next/font/google` API. Per the LLD (Epic 22 scope), the platform uses Inter as the primary sans-serif font and Outfit as a secondary/display font. Next.js's font API handles self-hosting, optimal loading, and zero layout shift.

**Tasks:**

- Create `frontend/styles/fonts.ts`:
  - Import `Inter` and `Outfit` from `next/font/google`
  - Configure `Inter` with subsets: `['latin']`, display: `'swap'`, variable: `'--font-inter'`
  - Configure `Outfit` with subsets: `['latin']`, display: `'swap'`, variable: `'--font-outfit'`
  - Export both font objects
- Update `frontend/app/layout.tsx`:
  - Import font objects from `@/styles/fonts`
  - Apply font CSS variables to the `<html>` element using `className`
- Update `frontend/styles/globals.css`:
  - Set `--font-family-sans: var(--font-inter), system-ui, sans-serif`
  - Set `--font-family-display: var(--font-outfit), system-ui, sans-serif`

**Acceptance Criteria:**

- [ ] `styles/fonts.ts` exists with Inter and Outfit font configurations
- [ ] Fonts use Next.js `next/font/google` API (self-hosted, no external requests)
- [ ] Font CSS variables (`--font-inter`, `--font-outfit`) applied to `<html>` element
- [ ] `globals.css` references font variables for `--font-family-sans` and `--font-family-display`
- [ ] Text renders in Inter font on the page
- [ ] No layout shift (CLS) from font loading
- [ ] `pnpm build` completes without font-related errors

**Dependencies:** Task 22.3

---

## Domain 3: Layout Components

### Task 22.5 — Create App Shell Layout Component

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the main application shell layout component that provides the structural frame for the dashboard pages. This includes a sidebar for navigation, a header bar, and a main content area. The session page will use a different layout (full-screen, no sidebar), so this app shell is specifically for the dashboard route group. The component should be responsive — collapsing the sidebar on smaller screens.

**Tasks:**

- Create `frontend/components/layout/AppShell.tsx`:
  - Layout structure:
    - Fixed sidebar on the left (collapsible on mobile)
    - Header bar at the top of the content area
    - Main content area that fills remaining space
  - Accept `children` as prop for the main content rendering
  - Use CSS custom properties from the design system for all styling
  - Create corresponding `frontend/components/layout/AppShell.module.css` for styles
- Create `frontend/components/layout/Sidebar.tsx`:
  - Navigation links (placeholder items for now — will be populated in Epic 33)
  - Platform logo/name at the top
  - Collapse/expand toggle for responsive behavior
  - Active link highlighting (using `usePathname` from `next/navigation`)
  - Create corresponding `Sidebar.module.css`
- Create `frontend/components/layout/Header.tsx`:
  - Page title area (dynamic based on route)
  - User avatar/profile section (placeholder for now — populated in Epic 33)
  - Create corresponding `Header.module.css`
- Wire `AppShell` into `app/(dashboard)/layout.tsx`

**Acceptance Criteria:**

- [ ] `components/layout/AppShell.tsx` exists with sidebar + header + content layout
- [ ] `components/layout/Sidebar.tsx` exists with navigation structure and collapse toggle
- [ ] `components/layout/Header.tsx` exists with title and user section
- [ ] All components use CSS Modules for styling
- [ ] All styles use CSS custom properties from the design system
- [ ] Dashboard route group (`app/(dashboard)/layout.tsx`) uses `AppShell`
- [ ] Sidebar collapses on viewports below 768px
- [ ] `pnpm dev` renders the layout without errors

**Dependencies:** Task 22.3, Task 22.4

---

## Domain 4: Routing Structure

### Task 22.6 — Set Up Route Groups and Placeholder Pages

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create the routing structure for the three main areas of the application: authentication pages, dashboard pages, and the live session page. Next.js App Router's route groups (`(auth)`, `(dashboard)`, `(session)`) allow different layouts per section without affecting the URL structure. Each section gets a placeholder page so the routing is demonstrable.

**Tasks:**

- Create placeholder pages under each route group:
  - `app/(auth)/login/page.tsx` — Login page placeholder
  - `app/(auth)/signup/page.tsx` — Signup page placeholder
  - `app/(dashboard)/dashboard/page.tsx` — Dashboard home page placeholder
  - `app/(dashboard)/agents/page.tsx` — Agent management page placeholder
  - `app/(dashboard)/templates/page.tsx` — Session templates page placeholder
  - `app/(session)/session/[id]/page.tsx` — Live session page placeholder (dynamic route with session ID)
- Each placeholder page should:
  - Export a default React component
  - Render a heading with the page name
  - Be a valid Next.js page component
- Update `app/(auth)/layout.tsx`:
  - Minimal centered layout for auth pages (no sidebar, no header)
- Update `app/(session)/layout.tsx`:
  - Full-screen layout with no sidebar (session is immersive)

**Acceptance Criteria:**

- [ ] Login page accessible at `/login`
- [ ] Signup page accessible at `/signup`
- [ ] Dashboard page accessible at `/dashboard`
- [ ] Agents page accessible at `/agents`
- [ ] Templates page accessible at `/templates`
- [ ] Session page accessible at `/session/[id]` (dynamic route)
- [ ] Auth pages use centered layout (no sidebar)
- [ ] Dashboard pages use `AppShell` layout (sidebar + header)
- [ ] Session page uses full-screen layout (no sidebar/header)
- [ ] `pnpm dev` — navigation between routes works without errors

**Dependencies:** Task 22.5

---

## Domain 5: Environment Variables

### Task 22.7 — Configure Frontend Environment Variables

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Configure the environment variable strategy for the Next.js frontend. Next.js requires environment variables exposed to the browser to be prefixed with `NEXT_PUBLIC_`. The `.env.example` file already has `NEXT_PUBLIC_LIVEKIT_URL`, but we need to add the Platform API URL and structure the env loading properly for both development and production.

**Tasks:**

- Update `frontend/.env.example`:

  - Add all frontend environment variables with descriptions:

    ```
    # LiveKit Server URL (WebSocket connection)
    NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880

    # Platform API Base URL
    NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    ```

- Update `frontend/.env.local` (gitignored, for local development):
  - Set development values matching docker-compose and backend defaults
- Create `frontend/services/config.ts`:
  - Export a typed configuration object that reads from `process.env`:
    ```typescript
    export const config = {
      livekitUrl: process.env.NEXT_PUBLIC_LIVEKIT_URL || "ws://localhost:7880",
      apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
    } as const;
    ```
  - Add type safety and validation (warn in console if required variables are missing)

**Acceptance Criteria:**

- [ ] `.env.example` documents all frontend environment variables with descriptions
- [ ] `.env.local` has local development values
- [ ] `services/config.ts` exports a typed config object
- [ ] Config reads from `process.env` with sensible defaults
- [ ] Missing required variables log a warning in development
- [ ] `NEXT_PUBLIC_` prefix correctly used for browser-exposed variables
- [ ] `pnpm dev` loads environment variables without errors

**Dependencies:** Task 22.1

---

## Domain 6: Base UI Components

### Task 22.8 — Create Base UI Primitives (Button, Input, Card)

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the foundational UI primitive components that will be reused across the application — Button, Input, and Card. These components use CSS Modules and reference the design system tokens. They should be simple, accessible, and composable. This is not a full component library — just the minimum reusable primitives needed for the auth, dashboard, and session pages.

**Tasks:**

- Create `frontend/components/ui/Button.tsx`:
  - Props: `variant` (`primary` | `secondary` | `ghost` | `danger`), `size` (`sm` | `md` | `lg`), `disabled`, `loading`, `children`, standard button HTML attributes
  - CSS Module: `Button.module.css`
  - Uses design tokens for colors, padding, border radius, transitions
  - Loading state — show a simple spinner/indicator and disable interaction
  - Accessible — proper `aria` attributes when disabled/loading
- Create `frontend/components/ui/Input.tsx`:
  - Props: `label`, `error`, `helperText`, standard input HTML attributes
  - CSS Module: `Input.module.css`
  - Label and error message rendering
  - Uses design tokens for styling
  - Accessible — `id` and `htmlFor` linkage between label and input
- Create `frontend/components/ui/Card.tsx`:
  - Props: `children`, `padding` (optional), standard div HTML attributes
  - CSS Module: `Card.module.css`
  - Surface container with border, shadow, and border radius from design tokens
- Export all components from `frontend/components/ui/index.ts`

**Acceptance Criteria:**

- [ ] `components/ui/Button.tsx` exists with variant, size, disabled, and loading support
- [ ] `components/ui/Input.tsx` exists with label, error, and helper text support
- [ ] `components/ui/Card.tsx` exists as a surface container
- [ ] All components use CSS Modules for styling
- [ ] All styles reference CSS custom properties from the design system
- [ ] Components are accessible (proper ARIA attributes, label linkage)
- [ ] `components/ui/index.ts` exports all components
- [ ] `import { Button, Input, Card } from '@/components/ui'` works

**Dependencies:** Task 22.3

---

## Domain 7: Responsive Design & Dark Mode

### Task 22.9 — Implement Responsive Design Foundation

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Define the responsive design breakpoints and utility patterns for the application. This establishes the breakpoint values, viewport meta tag, and responsive patterns that all components will follow. The approach uses CSS media queries with standardized breakpoints defined as CSS custom properties.

**Tasks:**

- Update `frontend/styles/globals.css`:
  - Define breakpoint reference comments (CSS doesn't support variables in media queries, so document them clearly):
    ```css
    /* Breakpoints:
       --breakpoint-sm: 640px
       --breakpoint-md: 768px
       --breakpoint-lg: 1024px
       --breakpoint-xl: 1280px
    */
    ```
  - Add responsive utility classes (optional, for common patterns):
    - `.sr-only` — screen reader only
    - `.hide-mobile` — hidden below `768px`
    - `.hide-desktop` — hidden above `768px`
- Verify the default Next.js viewport meta tag is present in `app/layout.tsx`:
  - `<meta name="viewport" content="width=device-width, initial-scale=1" />` (Next.js handles this via metadata export)
- Export a metadata object from `app/layout.tsx` with viewport configuration

**Acceptance Criteria:**

- [ ] Breakpoint values documented in `globals.css`
- [ ] Responsive utility classes defined (`.sr-only`, `.hide-mobile`, `.hide-desktop`)
- [ ] Viewport meta tag configured in `app/layout.tsx` via Next.js metadata export
- [ ] Sidebar collapses correctly at the `md` breakpoint (768px) — verified visually
- [ ] Layout remains usable at mobile viewport widths (375px)
- [ ] No horizontal scroll at any standard viewport width

**Dependencies:** Task 22.3, Task 22.5

---

### Task 22.10 — Implement Dark Mode Support

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Implement dark mode support with system preference detection and a manual toggle. The design system (Task 22.3) already defines dark mode color overrides via `[data-theme="dark"]`. This task adds the logic to detect the user's system preference, allow manual toggling, and persist the preference in `localStorage`.

**Tasks:**

- Create `frontend/hooks/useTheme.ts`:
  - Custom hook that manages the current theme (`light` | `dark`)
  - On mount:
    - Check `localStorage` for saved preference
    - If no saved preference, detect system preference using `window.matchMedia('(prefers-color-scheme: dark)')`
    - Apply the theme by setting `data-theme` attribute on `<html>` element
  - Expose `theme` (current value), `toggleTheme()` function, and `setTheme(theme)` function
  - Listen for system preference changes (if no manual override set)
  - Persist manual preference in `localStorage`
- Create `frontend/components/ui/ThemeToggle.tsx`:
  - Sun/moon icon toggle button
  - Uses `useTheme` hook
  - Accessible label (aria-label describing the action)
  - CSS Module: `ThemeToggle.module.css`
- Update `frontend/styles/globals.css`:
  - Ensure dark mode token overrides work with `[data-theme="dark"]` selector on `<html>`
  - Add smooth `color-scheme` transition to prevent jarring switches
- Integrate `ThemeToggle` into the `Header` component

**Acceptance Criteria:**

- [ ] `hooks/useTheme.ts` exists with `theme`, `toggleTheme`, and `setTheme`
- [ ] System theme preference is detected on first visit
- [ ] Manual toggle switches between light and dark mode
- [ ] Preference is persisted in `localStorage`
- [ ] Subsequent visits use the saved preference
- [ ] `ThemeToggle` component renders a toggle button in the header
- [ ] All design tokens update correctly when theme changes
- [ ] No flash of wrong theme on page load (FOUC prevention)
- [ ] System preference changes are respected when no manual override is set

**Dependencies:** Task 22.3, Task 22.5

---

## Domain 8: SEO & Metadata

### Task 22.11 — Configure SEO Defaults and Metadata

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Configure the default SEO metadata for the application using Next.js's built-in metadata API. This includes the page title template, meta description, Open Graph tags, favicon, and other standard SEO elements. Individual pages can override these defaults as needed.

**Tasks:**

- Update `frontend/app/layout.tsx`:
  - Export a `metadata` object with:
    - `title`: default and template (e.g., `{ default: 'Live Interactive Agent', template: '%s | Live Interactive Agent' }`)
    - `description`: Platform description
    - `openGraph`: default OG tags (title, description, type, siteName)
    - `robots`: `{ index: true, follow: true }` (or `noindex` for development)
    - `icons`: favicon configuration
  - Export a `viewport` object with:
    - `width: 'device-width'`
    - `initialScale: 1`
- Add a favicon file to `frontend/public/`:
  - `favicon.ico` (can be a simple placeholder icon for now)
- Verify each placeholder page can override the title using the Next.js metadata API

**Acceptance Criteria:**

- [ ] Root `layout.tsx` exports `metadata` with title template and description
- [ ] Open Graph tags are configured
- [ ] Favicon is present in `public/` and referenced in metadata
- [ ] Viewport is configured correctly
- [ ] `<title>` renders as "Live Interactive Agent" on the home page
- [ ] Individual pages can override the title (e.g., "Login | Live Interactive Agent")
- [ ] `pnpm build` generates correct meta tags in HTML output

**Dependencies:** Task 22.1

---

## Domain 9: Documentation & Development Workflow

### Task 22.12 — Update Documentation and Add Makefile Commands

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Update the project documentation and Makefile with frontend-specific commands and development workflow instructions. This follows the same pattern established for the backend (`make api`) and agent-runtime (`make agent-dev`).

**Tasks:**

- Add Makefile targets for the frontend (update root `Makefile`):
  - `frontend-dev` — start the frontend dev server: `pnpm --filter frontend dev`
  - `frontend-build` — build the production bundle: `pnpm --filter frontend build`
  - `frontend-lint` — run ESLint: `pnpm --filter frontend lint`
  - `frontend-format` — run Prettier: `pnpm --filter frontend format`
- Create or update `frontend/README.md`:
  - **Overview** — what the frontend does and its role in the platform
  - **Prerequisites** — Node.js 20+, pnpm
  - **Installation** — `pnpm install` instructions
  - **Development** — `pnpm dev` to start the dev server
  - **Project Structure** — describe directories and their purposes
  - **Design System** — reference to CSS custom properties and how to use them
  - **Environment Variables** — description of each `NEXT_PUBLIC_` variable
  - **Routing** — describe route groups and page structure
- Ensure `pnpm dev` starts the frontend on a default port that doesn't conflict with the backend (port 3000 vs 8000)

**Acceptance Criteria:**

- [x] `make frontend-dev` starts the Next.js development server
- [x] `make frontend-build` builds the production bundle
- [x] `make frontend-lint` runs ESLint on frontend code
- [x] `make frontend-format` runs Prettier on frontend code
- [x] `frontend/README.md` documents the project structure, design system, and development workflow
- [x] Environment variables are documented with descriptions and defaults
- [x] All Makefile targets have descriptive comments
- [x] All targets work from the project root directory

**Dependencies:** Task 22.6

---

## Recommended Execution Order

1. **Task 22.1** — Create Frontend Directory Structure
2. **Task 22.2** — Configure Path Aliases
3. **Task 22.3** — Create CSS Design System (Color Tokens, Typography, Spacing)
4. **Task 22.4** — Load Google Fonts (Inter & Outfit)
5. **Task 22.7** — Configure Frontend Environment Variables
6. **Task 22.8** — Create Base UI Primitives (Button, Input, Card)
7. **Task 22.5** — Create App Shell Layout Component
8. **Task 22.6** — Set Up Route Groups and Placeholder Pages
9. **Task 22.9** — Implement Responsive Design Foundation
10. **Task 22.10** — Implement Dark Mode Support
11. **Task 22.11** — Configure SEO Defaults and Metadata
12. **Task 22.12** — Update Documentation and Add Makefile Commands

---

## Definition of Done

Epic 22 is complete when:

- [x] All 12 tasks marked COMPLETED
- [x] `pnpm dev` starts the frontend application without errors
- [x] Directory structure is organized with components, hooks, services, utils, types, styles
- [x] CSS design system defines color, typography, spacing, and transition tokens
- [x] Inter and Outfit fonts are loaded via `next/font/google`
- [x] App shell layout (sidebar + header + content) renders on dashboard pages
- [x] Auth pages use centered layout, session page uses full-screen layout
- [x] All placeholder pages are accessible at their expected routes
- [x] Dark mode toggle works with system preference detection and `localStorage` persistence
- [x] SEO metadata (title, description, OG tags, favicon) is configured
- [x] Environment variables are documented and loaded via typed config
- [x] Makefile commands work: `make frontend-dev`, `make frontend-build`, `make frontend-lint`, `make frontend-format`
- [x] Documentation is comprehensive and accurate
- [x] No regressions in Epics 1-8, 12-14
