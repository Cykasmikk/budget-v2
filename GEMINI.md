# Enterprise AI Budget Dashboard - Context & Instructions

## 1. Project Overview
**Name:** Enterprise AI Budget Architect
**Description:** A local-first, AI-powered personal finance dashboard designed for privacy, speed, and intelligent analysis.
**Core Philosophy:** "Clean Architecture" / Hexagonal Architecture with strict Type Safety and Security Gates.

## 2. Technology Stack (Immutable)

### Backend (Service Layer)
*   **Language:** Python 3.12+ (Strict `mypy` typing required)
*   **Framework:** FastAPI (Latest Stable)
*   **Pattern:** Hexagonal / Clean Architecture
    *   `src/domain/`: Pure business logic (No external deps)
    *   `src/application/`: Use cases & orchestration
    *   `src/infrastructure/`: Drivers, DB adapters, External APIs
    *   `src/interface/`: API Routers, DTOs
*   **Database:** PostgreSQL (Production) / SQLite (Local/Testing) via SQLAlchemy (Async)
*   **Validation:** Pydantic V2 (Strict Mode)
*   **Logging:** `structlog` (JSON format only)

### Frontend (Client Layer)
*   **Language:** TypeScript 5.4+ (Strict Mode)
*   **Framework:** Lit (Web Components)
    *   **FORBIDDEN:** React, Vue, Angular, Svelte (unless explicitly migrating)
*   **State Management:** TanStack Store (Signal-based)
*   **Build Tool:** Vite
*   **Design System:** "2025 Metallic/Minimalist" (Shadow DOM, CSS Variables)

### Infrastructure
*   **Containerization:** Docker (Multi-stage, non-root users)
*   **Orchestration:** Kubernetes (Kustomize)
*   **CI/CD:** GitOps (ArgoCD pattern implied)

## 3. Architecture & Directory Structure

```text
/
├── backend/
│   ├── src/
│   │   ├── domain/         # Core entities (Budget, User, Rule) - NO deps
│   │   ├── application/    # Business logic (Services, Use Cases)
│   │   ├── infrastructure/ # DB impl, File parsers, LLM adapters
│   │   ├── interface/      # FastAPI routers (API definition)
│   │   └── main.py         # Entry point
│   ├── tests/              # Pytest suite
│   ├── alembic/            # DB Migrations
│   └── pyproject.toml      # Dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # Lit components
│   │   ├── store/          # TanStack Store state
│   │   └── services/       # API clients
│   └── package.json
├── k8s/                    # Kubernetes manifests (Kustomize)
├── docker-compose.yml      # Local development orchestration
└── scripts/                # Utility scripts
```

## 4. Building & Running

### Local Development
The project uses Docker Compose for a unified dev environment.

**Start all services:**
```bash
# Requires AUTH_SECRET_KEY env var
export AUTH_SECRET_KEY="dev-secret-key"
docker-compose up --build
```

**Access Points:**
*   Frontend: `http://localhost:3000`
*   Backend API: `http://localhost:8000/docs`

### Testing
**Backend:**
```bash
cd backend
# Create venv if not exists
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

**Frontend:**
```bash
cd frontend
npm install
npm test
```

## 5. Development Conventions & Rules

**Strict TDD Cycle (Red-Green-Refactor):**
1.  **Red:** Write a failing test first.
2.  **Green:** Write minimal code to pass.
3.  **Refactor:** Optimize and Type-Check.

**Security Gates (Blocking):**
*   **Secrets:** NEVER hardcode secrets. Use `os.getenv` or `.env` files.
*   **Least Privilege:** Dockerfiles must end with `USER nonroot`.
*   **Sanitization:** All inputs validatd via Pydantic/Zod.

**Code Quality:**
*   **Python:** Black formatter, isort, Google-style docstrings.
*   **TypeScript:** Prettier, ESLint.
*   **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`).

## 6. Key Workflows
*   **Budget Upload:** Handled via `application/upload_budget.py` -> `infrastructure/excel_parser.py`.
*   **Analysis:** AI Logic resides in `application/ai_chat_service.py` calling `infrastructure/llm/`.
*   **Database:** Async SQLAlchemy interactions in `infrastructure/db.py`.
