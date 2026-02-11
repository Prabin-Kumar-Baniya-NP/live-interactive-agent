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

## 🧪 Testing

Run endpoints locally and verify using the Swagger UI.
