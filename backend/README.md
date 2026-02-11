# Platform API (Backend)

The backend service for the Live Interactive Agent platform, built with **FastAPI**.

## 🚀 Quick Start

From the project root:

```bash
make api
```

Or manually:

```bash
cd backend
poetry run uvicorn app.main:app --reload --port 8000
```

Access the API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

## 📂 Project Structure

- `app/api/v1/`: API endpoints (versioned).
- `app/core/`: Core configuration (settings, logging).
- `app/db/`: Database connection and session management.
- `app/models/`: SQLAlchemy database models.
- `app/schemas/`: Pydantic schemas (request/response models).
- `app/middleware/`: Custom middleware (CORS, Request ID).
- `app/exceptions/`: Custom exception classes and handlers.
- `app/cache/`: Redis connection utilities.

## 🛠️ Adding New Endpoints

1.  **Define Schema:** Create request/response Pydantic models in `app/schemas/`.
2.  **Create Router:** Create a new module in `app/api/v1/` (e.g., `users.py`).
3.  **Implement Logic:** Use `APIRouter` to define endpoints.
4.  **Register Router:** Import and include the router in `app/api/v1/router.py`.

## 🔐 Authentication

The API uses **HTTP-Only Cookies** for authentication (`access_token`, `refresh_token`).

### Auth Endpoints

- `POST /api/v1/auth/signup` - Create account & organization
- `POST /api/v1/auth/login` - Login (sets cookies)
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Clear cookies
- `GET /api/v1/auth/user` - Get current user profile

### Development Testing

**Using cURL:**
Use `-c` (cookie-jar) to save cookies and `-b` (cookie) to send them.

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com", "password":"password123", "organization_name":"Test Org"}' \
  -c cookies.txt

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com", "password":"password123"}' \
  -c cookies.txt

# Access Protected Endpoint
curl -X GET http://localhost:8000/api/v1/auth/user \
  -b cookies.txt
```

**Using Swagger UI:**

1. Open [http://localhost:8000/docs](http://localhost:8000/docs)
2. Use the `auth/login` endpoint to log in.
3. The browser will automatically store the cookies.
4. You can now execute protected endpoints directly in the UI.

## 🧪 Testing

Run endpoints locally and verify using the Swagger UI.
