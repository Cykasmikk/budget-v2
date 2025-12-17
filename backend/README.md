# Budget Dashboard Backend

A Hexagonal Architecture-based Python backend for the AI-powered Budget Dashboard. Built with FastAPI, SQLAlchemy (Async), and Pydantic V2.

## 🏛️ Architecture

The backend follows the **Hexagonal Architecture** (Ports & Adapters) pattern to ensure separation of concerns and testability.

### Layer Structure (`src/`)

*   **`domain/`**: The core business logic and entities. Pure Python code with zero external dependencies (except Pydantic).
    *   *Entities*: `BudgetEntry`, `User`, `Tenant`, `Rule`.
*   **`application/`**: Application-specific business rules (Use Cases). Orchestrates the domain objects.
    *   *Use Cases*: `AnalyzeBudgetUseCase`, `UploadBudgetUseCase`, `AIChatService`.
    *   *DTOs*: Data Transfer Objects for strictly typed inter-layer communication.
*   **`infrastructure/`**: Adapters that interface with external systems (Database, File System, External APIs).
    *   *Adapters*: `SQLBudgetRepository`, `PandasExcelParser`, `AuthService`.
    *   *Models*: SQLAlchemy ORM models mapping to the database tables.
*   **`interface/`**: The entry points into the application (API).
    *   *Routers*: FastAPI routers handling HTTP requests and responses.
    *   *Envelope*: Standardized API response format (`ResponseEnvelope`).

## 🚀 Key Features

*   **Secure Authentication**: Session-based auth with HTTPOnly cookies, non-root container execution, and configurable SSO support.
*   **AI-Powered Analysis**: Natural language querying of budget data and intelligent category suggestions.
*   **Performance**: Fully async I/O for database and file operations. Optimized bulk inserts with de-duplication.
*   **Observability**: Structured JSON logging via `structlog`.
*   **Strict Validation**: Pydantic V2 Strict Mode enabled for all data models.

## 🛠️ Tech Stack

*   **Language**: Python 3.12+
*   **Framework**: FastAPI
*   **Database**: PostgreSQL (Production) / SQLite (Dev/Test)
*   **ORM**: SQLAlchemy (Async) + Alembic (Migrations)
*   **Validation**: Pydantic V2
*   **Logging**: Structlog

## 🏁 Getting Started

### Prerequisites
*   Python 3.12+
*   Docker & Docker Compose (optional but recommended)

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Connection string for the database | `postgresql+asyncpg://...` |
| `AUTH_SECRET_KEY` | Secret key for signing sessions | **REQUIRED** |
| `INITIAL_ADMIN_PASSWORD` | Password for the default admin user | `admin` (Change in prod!) |
| `SECURE_COOKIES` | Set to `True` in production (requires HTTPS) | `False` |
| `GUEST_RATE_LIMIT` | Rate limit for guest access endpoint | `20/hour` |

### Local Development

1.  **Create Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/Mac
    # .venv\Scripts\activate   # Windows
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -e .[dev]
    ```

3.  **Run Tests**:
    ```bash
    pytest
    ```

4.  **Start Server**:
    ```bash
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
    ```

## 📝 API Documentation

Once the server is running, interactive API documentation is available at:
*   **Swagger UI**: `http://localhost:8000/docs`
*   **ReDoc**: `http://localhost:8000/redoc`

All API endpoints return a standardized envelope:
```json
{
  "data": { ... },
  "meta": { ... },
  "errors": []
}
```
