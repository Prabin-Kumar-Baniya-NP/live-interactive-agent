# Epic 5 — Authentication & Authorization System

## Task Breakdown

**Epic Summary:** Implement the authentication and authorization layer for platform customers (the people who create and manage agents). This covers user registration, login, JWT token management via HTTP-only cookies, role-based access control (RBAC), and organization/tenant model. This is NOT end-user auth — it's for the dashboard/admin side. It builds directly on top of the FastAPI foundation (Epic 4) and the existing `User` and `Organization` models (Epic 3).

**Authentication Strategy:** HTTP-only cookie-based authentication. The frontend and backend run on different subdomains of the same domain (e.g., `app.example.com` and `api.example.com`). Cookies are scoped to the parent domain (`.example.com`) to enable cross-subdomain sharing. This approach prevents XSS-based token theft since JavaScript cannot access HTTP-only cookies.

**Layer:** Platform API
**Dependencies:** Epic 4 (Platform API Foundation), Epic 3 (Database & Cache Layer — provides `User`, `Organization` models)

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

## Domain 1: Password Hashing & Auth Utilities

### Task 5.1 — Create Password Hashing Utility Module

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create a utility module for password hashing and verification using `bcrypt`. The `bcrypt` package was already added as a dependency in Epic 3 (Task 3.7 — seed script), so no new install is needed. This module centralizes all password handling in one place for the entire application.

**Tasks:**

- Create `backend/app/core/security.py` with:
  - `hash_password(plain_password: str) -> str` — hashes a plaintext password using bcrypt
  - `verify_password(plain_password: str, hashed_password: str) -> bool` — verifies a plaintext password against a hash
- Keep it simple — just bcrypt, no custom salting logic (bcrypt handles salts internally)

**Acceptance Criteria:**

- [ ] `backend/app/core/security.py` exists with `hash_password()` and `verify_password()` functions
- [ ] Hashing a password returns a bcrypt hash string (starts with `$2b$`)
- [ ] Verifying the correct password returns `True`
- [ ] Verifying a wrong password returns `False`
- [ ] `from app.core.security import hash_password, verify_password` works

**Dependencies:** Epic 4 (Task 4.1 — project structure)

---

### Task 5.2 — Create JWT Token & Cookie Utility Module

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create a JWT utility module for creating and decoding access tokens and refresh tokens using the `PyJWT` library. Add JWT and cookie-related settings to the application config. Tokens will be delivered to the client as HTTP-only cookies (not in response body), so this task also includes a helper for setting auth cookies on a response.

**Cookie Strategy:** Frontend (`app.example.com`) and backend (`api.example.com`) are on different subdomains of the same parent domain. Cookies are set with `domain=.example.com` so the browser sends them on cross-subdomain requests. `SameSite=Lax` is sufficient since subdomains of the same registered domain are considered same-site.

**Tasks:**

- Add `PyJWT` as a dependency in `backend/pyproject.toml` via Poetry
- Add the following settings to `backend/app/core/config.py` (`Settings` class):
  - `JWT_SECRET_KEY: str` — secret key for signing JWTs (loaded from env, required)
  - `JWT_ALGORITHM: str = "HS256"`
  - `ACCESS_TOKEN_EXPIRE_MINUTES: int = 30`
  - `REFRESH_TOKEN_EXPIRE_DAYS: int = 7`
  - `COOKIE_DOMAIN: str = "localhost"` — parent domain for cookies (e.g., `.example.com` in production)
  - `COOKIE_SECURE: bool = False` — set to `True` in production (HTTPS only)
- Add `JWT_SECRET_KEY`, `COOKIE_DOMAIN`, and `COOKIE_SECURE` to `backend/.env.example`
- Add JWT functions to `backend/app/core/security.py`:
  - `create_access_token(data: dict, expires_delta: timedelta | None = None) -> str` — creates a signed JWT access token with an `exp` claim
  - `create_refresh_token(data: dict) -> str` — creates a signed JWT refresh token with a longer expiry
  - `decode_token(token: str) -> dict` — decodes and validates a JWT, raises an exception if expired or invalid
- Add cookie helper to `backend/app/core/security.py`:
  - `set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None`:
    - Sets `access_token` as an HTTP-only cookie (`Path=/`, `SameSite=Lax`, `Secure` based on config, `Domain` from config)
    - Sets `refresh_token` as an HTTP-only cookie (`Path=/api/v1/auth/refresh`, scoped to refresh endpoint only, same cookie settings)
  - `clear_auth_cookies(response: Response) -> None`:
    - Clears both auth cookies from the response

**Acceptance Criteria:**

- [ ] `PyJWT` is in `backend/pyproject.toml`
- [ ] JWT and cookie settings are added to `Settings` class in `config.py`
- [ ] `JWT_SECRET_KEY`, `COOKIE_DOMAIN`, `COOKIE_SECURE` are in `backend/.env.example`
- [ ] `create_access_token()` returns a valid JWT string
- [ ] `create_refresh_token()` returns a valid JWT with longer expiry
- [ ] `decode_token()` returns payload for valid tokens
- [ ] `decode_token()` raises an exception for expired or tampered tokens
- [ ] `set_auth_cookies()` sets HTTP-only, SameSite=Lax cookies on the response
- [ ] `clear_auth_cookies()` removes both cookies from the response

**Dependencies:** Task 5.1

---

## Domain 2: User Registration & Login Endpoints

### Task 5.3 — Create Auth Pydantic Schemas

**Status:** COMPLETED
**Estimated Effort:** S

**Comment:** Schemas were renamed for better clarity: `SignupSchema`, `LoginSchema`, `UserSchema`, and `GenericMessageSchema`.

**Description:**
Create the Pydantic request/response schemas for authentication endpoints (registration, login). Since tokens are delivered via HTTP-only cookies (not in the response body), the response schema returns user profile info instead of tokens.

**Tasks:**

- Create `backend/app/schemas/auth.py` with:
  - `UserRegisterRequest` — `email: EmailStr`, `password: str` (min length 8), `full_name: str | None`, `organization_name: str` (required — the name of the user's organization)
  - `UserLoginRequest` — `email: EmailStr`, `password: str`
  - `UserResponse` — `id: UUID`, `email: str`, `full_name: str | None`, `role: str`, `organization_id: UUID`, `is_active: bool`, `created_at: datetime`, `updated_at: datetime | None` (extends `BaseSchema` with `from_attributes=True` for ORM)
  - `MessageResponse` — `message: str` (for logout and other simple responses)
- Add `pydantic[email]` (or `email-validator`) as a dependency if not already present, for `EmailStr` support

**Acceptance Criteria:**

- [ ] `backend/app/schemas/auth.py` exists with all schemas listed above
- [ ] `EmailStr` validates email format correctly
- [ ] `password` has minimum length validation (8 characters)
- [ ] `organization_name` is a required field in `UserRegisterRequest`
- [ ] `UserResponse` can be constructed from an ORM `User` model instance (via `from_attributes`)
- [ ] All schemas are importable from `app.schemas.auth`

**Dependencies:** Epic 4 (Task 4.8 — base schemas)

---

### Task 5.4 — Create Auth Service Layer

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the auth service module that contains the business logic for user registration and login. This service layer sits between the API routes and the database, following the layered architecture pattern established in Epic 4.

**Tasks:**

- Create `backend/app/services/` directory with `__init__.py`
- Create `backend/app/services/auth.py` with:
  - `register_user(db: AsyncSession, email: str, password: str, full_name: str | None, organization_name: str) -> User`:
    - Check if user with email already exists → raise `BadRequestException` if duplicate
    - Create the organization with the provided `organization_name`
    - Hash the password
    - Create the user with role `"admin"` (first user of their org is always admin)
    - Return the created user
  - `authenticate_user(db: AsyncSession, email: str, password: str) -> User`:
    - Fetch user by email → raise `BadRequestException("Invalid credentials")` if not found
    - Verify password → raise `BadRequestException("Invalid credentials")` if wrong
    - Check `is_active` → raise `ForbiddenException("Account is disabled")` if inactive
    - Return the user

**Acceptance Criteria:**

- [ ] `backend/app/services/` directory exists with `__init__.py`
- [ ] `backend/app/services/auth.py` exists with `register_user()` and `authenticate_user()` functions
- [ ] Registration requires `organization_name` — no default or auto-generated value
- [ ] Registration creates a new user and organization in the database
- [ ] Registration rejects duplicate emails with a clear error
- [ ] Authentication returns user for valid credentials
- [ ] Authentication rejects invalid email or password with a generic "Invalid credentials" message (no info leakage)
- [ ] Authentication rejects disabled accounts

**Dependencies:** Task 5.1, Task 5.3, Epic 3 (User, Organization models)

---

### Task 5.5 — Create Registration & Login API Endpoints

**Status:** COMPLETED
**Estimated Effort:** M

**Comment:** Endpoint `/register` was renamed to `/signup` as part of auth refinement.

**Description:**
Create the API endpoints for user registration and login. These are public endpoints (no auth required). Instead of returning JWT tokens in the response body, tokens are set as HTTP-only cookies on the response. The response body contains the user profile.

**Tasks:**

- Create `backend/app/api/v1/auth.py` with:
  - `POST /api/v1/auth/register` — accepts `UserRegisterRequest`, calls `register_user()` service, sets auth cookies on response, returns `UserResponse`
  - `POST /api/v1/auth/login` — accepts `UserLoginRequest`, calls `authenticate_user()` service, sets auth cookies on response, returns `UserResponse`
- Register the auth router in `backend/app/api/v1/router.py` with tag `"auth"`
- JWT token payload (`sub` claim) should contain the user's ID (UUID as string)
- Use `set_auth_cookies()` helper from Task 5.2 to set cookies
- Both endpoints should return structured error responses on failure (using the error handling framework from Epic 4)
- Update CORS middleware configuration to include `allow_credentials=True` (already set in Epic 4, verify it's correct)

**Acceptance Criteria:**

- [ ] `POST /api/v1/auth/register` creates a user and sets `access_token` + `refresh_token` as HTTP-only cookies
- [ ] `POST /api/v1/auth/register` response body contains `UserResponse` (no tokens in body)
- [ ] `POST /api/v1/auth/register` returns 400 if email is already taken
- [ ] `POST /api/v1/auth/login` sets auth cookies and returns `UserResponse` for valid credentials
- [ ] `POST /api/v1/auth/login` returns 400 for invalid email or password
- [ ] Cookies have `HttpOnly=True`, `SameSite=Lax`, `Domain` from config, `Secure` from config
- [ ] Endpoints appear in Swagger UI under the "auth" tag
- [ ] Error responses follow the structured format `{"error": {"code": "...", "message": "..."}}`

**Dependencies:** Task 5.2, Task 5.4

---

## Domain 3: Authentication Dependency, Token Refresh & Logout

### Task 5.6 — Create Authentication Dependency (get_current_user)

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create a FastAPI dependency that extracts and validates the JWT access token from the `access_token` HTTP-only cookie, and returns the current authenticated user. This dependency will be used on all protected endpoints across the application.

**Tasks:**

- Add to `backend/app/core/security.py`:
  - Create `get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User`:
    - Read the `access_token` cookie from `request.cookies`
    - Decode the JWT token using `decode_token()`
    - Extract user ID from `sub` claim
    - Fetch user from database
    - Raise `401 Unauthorized` if cookie missing, token invalid, token expired, or user not found
    - Raise `403 Forbidden` if user is inactive
    - Return the `User` ORM instance
- Add `UnauthorizedException` to `backend/app/exceptions/base.py`:
  - 401 status code, error code `"unauthorized"`

**Acceptance Criteria:**

- [ ] `get_current_user` dependency reads the `access_token` cookie from the request
- [ ] Valid cookie token returns the corresponding `User` from the database
- [ ] Expired token returns `401 {"error": {"code": "unauthorized", "message": "..."}}`
- [ ] Missing cookie returns `401`
- [ ] Inactive user returns `403`
- [ ] `UnauthorizedException` is added to exceptions
- [ ] Protected endpoints can use `current_user: User = Depends(get_current_user)` to require auth

**Dependencies:** Task 5.2, Task 5.5

---

### Task 5.7 — Create Token Refresh & Logout Endpoints

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create endpoints to refresh the access token using the refresh token cookie, and to log out by clearing auth cookies. These complete the cookie-based auth lifecycle.

**Tasks:**

- Add to `backend/app/api/v1/auth.py`:
  - `POST /api/v1/auth/refresh`:
    - Read the `refresh_token` cookie from the request
    - Decode and validate the refresh token
    - Fetch the user from the database to ensure they still exist and are active
    - Issue a new access token and refresh token pair, set as cookies on response
    - Return `UserResponse`
  - `POST /api/v1/auth/logout`:
    - Clear both `access_token` and `refresh_token` cookies using `clear_auth_cookies()`
    - Return `MessageResponse` with `"Logged out successfully"`

**Acceptance Criteria:**

- [ ] `POST /api/v1/auth/refresh` reads the refresh token from cookie (not request body)
- [ ] Refresh sets new auth cookies and returns `UserResponse`
- [ ] Returns `401` if refresh token cookie is missing, expired, or invalid
- [ ] Returns `403` if the user is inactive or deleted
- [ ] `POST /api/v1/auth/logout` clears both auth cookies
- [ ] After logout, subsequent requests to protected endpoints return `401`
- [ ] Both endpoints appear in Swagger UI under the "auth" tag

**Dependencies:** Task 5.6

---

### Task 5.8 — Create Get Current User Profile Endpoint

**Status:** COMPLETED
**Estimated Effort:** S

**Comment:** Endpoint `/me` was renamed to `/user` for consistency.

**Description:**
Create an endpoint that returns the currently authenticated user's profile. This is a simple protected endpoint that validates the auth dependency is working end-to-end with cookies.

**Tasks:**

- Add to `backend/app/api/v1/auth.py`:
  - `GET /api/v1/auth/me` — requires authentication (uses `get_current_user` dependency), returns `UserResponse`
- This endpoint is the simplest "protected endpoint" and serves as validation that the entire cookie auth flow works

**Acceptance Criteria:**

- [ ] `GET /api/v1/auth/me` returns the current user's profile when a valid `access_token` cookie is present
- [ ] Returns `401` when no cookie or an invalid cookie is provided
- [ ] Response matches the `UserResponse` schema
- [ ] Endpoint appears in Swagger UI under the "auth" tag

**Dependencies:** Task 5.6

---

## Domain 4: Role-Based Access Control (RBAC)

### Task 5.9 — Create RBAC Permission Dependencies

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Create FastAPI dependencies for role-based access control. The system supports two roles: `admin` and `member`. These dependencies can be composed on any endpoint to enforce minimum role requirements.

**Tasks:**

- Create `backend/app/core/permissions.py` with:
  - Define role hierarchy: `admin` > `member`
  - `require_role(required_role: str)` — returns a FastAPI dependency that checks if the current user has at least the required role level
    - Usage: `Depends(require_role("admin"))` on an endpoint
    - Raises `ForbiddenException` if the user's role is insufficient
  - `require_admin` — shorthand dependency for admin-only endpoints
- Roles are stored in the `User.role` column (already exists from Epic 3)
- Update the `User` model's `role` column default from `"member"` to `"member"` (already correct — first user gets `"admin"` via registration logic in Task 5.4, additional users default to `"member"`)

**Acceptance Criteria:**

- [ ] `backend/app/core/permissions.py` exists with role checking dependencies
- [ ] `require_role("admin")` allows admin users and rejects members
- [ ] `require_role("member")` allows both admin and member users
- [ ] Insufficient role returns `403 {"error": {"code": "forbidden", "message": "Insufficient permissions"}}`
- [ ] Dependencies can be used with `Depends()` on any endpoint

**Dependencies:** Task 5.6

---

## Domain 5: Organization / Multi-Tenancy

### Task 5.10 — Create Organization Service & Management Endpoints

**Status:** COMPLETED
**Estimated Effort:** M

**Description:**
Create the organization service layer and API endpoints for managing organizations. This enables multi-tenancy — all resources (agents, sessions, templates) will be scoped to an organization. The organization was created during registration (Task 5.4), this task adds management capabilities.

**Tasks:**

- Create `backend/app/services/organization.py` with:
  - `get_organization(db: AsyncSession, org_id: UUID) -> Organization` — fetch by ID, raise `NotFoundException` if not found
  - `update_organization(db: AsyncSession, org_id: UUID, name: str) -> Organization` — update org name
  - `get_organization_members(db: AsyncSession, org_id: UUID) -> list[User]` — list all users in the org
- Create `backend/app/schemas/organization.py` with:
  - `OrganizationResponse` — `id: UUID`, `name: str`, `created_at: datetime`, `updated_at: datetime | None`
  - `OrganizationUpdateRequest` — `name: str`
  - `MemberResponse` — `id: UUID`, `email: str`, `full_name: str | None`, `role: str`, `is_active: bool`, `created_at: datetime`
- Create `backend/app/api/v1/organizations.py` with:
  - `GET /api/v1/organizations/me` — get the current user's organization (auth required)
  - `PUT /api/v1/organizations/me` — update the current user's organization name (admin only)
  - `GET /api/v1/organizations/me/members` — list members of the current user's org (admin only)
- Register the organizations router in `backend/app/api/v1/router.py` with tag `"organizations"`
- All endpoints scoped to the current user's organization (no cross-org access)

**Acceptance Criteria:**

- [ ] Organization service functions exist and work with the database
- [ ] `GET /api/v1/organizations/me` returns the current user's org
- [ ] `PUT /api/v1/organizations/me` updates the org name (admin only)
- [ ] `GET /api/v1/organizations/me/members` lists org members (admin only)
- [ ] Non-admin users get `403` when trying to update org or list members
- [ ] Endpoints appear in Swagger UI under the "organizations" tag

**Dependencies:** Task 5.9

---

## Domain 6: Documentation & Seed Data Update

### Task 5.11 — Update Seed Script & Documentation

**Status:** COMPLETED
**Estimated Effort:** S

**Description:**
Update the database seed script to include test data relevant to auth (e.g., users with different roles) and update documentation with auth-related developer instructions.

**Tasks:**

- Update `backend/scripts/seed.py`:
  - Ensure the existing admin user seed data is correct
  - Add a second user with role `"member"` in the test organization
  - Ensure all passwords are properly hashed with bcrypt
- Update `backend/README.md` or root `README.md` with:
  - Auth endpoints documentation (register, login, refresh, logout, me)
  - How to authenticate in development (using the seeded test user)
  - How to test cookie-based auth with curl (`--cookie-jar` / `--cookie` flags)
  - How to test in Swagger UI (note: cookie auth requires using the browser to login first, then Swagger UI sends cookies automatically since it's on the same origin)
  - Example curl commands for common auth flows
- Update `backend/.env.example` with any new environment variables added in this epic (`JWT_SECRET_KEY`, `COOKIE_DOMAIN`, `COOKIE_SECURE`)

**Acceptance Criteria:**

- [ ] Seed script creates users with `admin` and `member` roles
- [ ] Seed script remains idempotent (no duplicates on re-run)
- [ ] README documents all auth endpoints
- [ ] README includes example curl commands for register, login, and accessing protected endpoints with cookies
- [ ] `.env.example` is up to date with all new env vars
- [ ] A developer can follow the README to authenticate from a fresh setup

**Dependencies:** Task 5.10

---

## Recommended Execution Order

1. **Task 5.1** Create Password Hashing Utility Module
2. **Task 5.2** Create JWT Token & Cookie Utility Module
3. **Task 5.3** Create Auth Pydantic Schemas
4. **Task 5.4** Create Auth Service Layer
5. **Task 5.5** Create Registration & Login API Endpoints
6. **Task 5.6** Create Authentication Dependency (get_current_user)
7. **Task 5.7** Create Token Refresh & Logout Endpoints
8. **Task 5.8** Create Get Current User Profile Endpoint
9. **Task 5.9** Create RBAC Permission Dependencies
10. **Task 5.10** Create Organization Service & Management Endpoints
11. **Task 5.11** Update Seed Script & Documentation
