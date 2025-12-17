# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enterprise AI Budget Architect - a local-first, AI-powered personal finance dashboard. Features universal file parsing, AI-powered categorization, natural language queries, and "What If?" simulations.

## Commands

### Run Full Stack (Docker)
```bash
export AUTH_SECRET_KEY="dev-secret-key"
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

### Backend Development
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

# Run all tests
pytest

# Run single test file
pytest tests/domain/test_budget.py

# Run with verbose output
pytest -v tests/application/test_upload_budget.py

# Type checking
mypy src/

# Formatting
black src/ tests/
isort src/ tests/
```

### Frontend Development
```bash
cd frontend
npm install

# Run tests
npm test

# Run single test file
npx vitest run src/components/budget-chart.test.ts

# Dev server (standalone)
npm run dev

# Build
npm run build
```

## Architecture

### Backend (Clean/Hexagonal Architecture)
Python 3.12+ with FastAPI. Strict layering with dependency inversion:

- **`src/domain/`** - Pure business entities (Budget, User, Rule, Tenant). Zero external dependencies.
- **`src/application/`** - Use cases and services. Key files:
  - `upload_budget.py` - File ingestion orchestration
  - `ai_chat_service.py` - Natural language query handling
  - `analyze_budget.py` - Spending analysis logic
  - `simulate_budget.py` - "What If?" scenarios
- **`src/infrastructure/`** - External adapters:
  - `excel_parser.py` - Universal Excel/CSV parsing with header detection
  - `db.py` - Async SQLAlchemy (PostgreSQL prod / SQLite test)
  - `repository.py` - Data access implementations
  - `auth/` - Auth providers (mock_auth.py, oidc_auth.py)
- **`src/interface/`** - FastAPI routers and DTOs. Protected routes require auth via `RequireAuth` dependency.

### Frontend (Lit Web Components)
TypeScript 5.4+ with Lit framework. **Do not use React/Vue/Angular.**

- **`src/components/`** - Lit web components (Shadow DOM)
- **`src/store/`** - TanStack Store for state management
- **`src/services/`** - API clients
- **`src/views/`** - Page-level components
- **`src/controllers/`** - Business logic controllers

### Key Data Flows
1. **Budget Upload**: `file-upload.ts` → `budget.service.ts` → `/api/v1/budgets` → `upload_budget.py` → `excel_parser.py`
2. **AI Chat**: `ai-chat.ts` → `/api/v1/ai/chat` → `ai_chat_service.py`
3. **Simulation**: `simulation-card.ts` → `/api/v1/simulate` → `simulate_budget.py`

## Development Conventions

### Code Style
- **Python**: Black formatter, isort, Google-style docstrings, strict mypy typing
- **TypeScript**: Prettier, ESLint, strict mode
- **Commits**: Conventional Commits (`feat:`, `fix:`, `chore:`)

### Testing
- TDD required: Red → Green → Refactor
- Backend: pytest with pytest-asyncio for async tests
- Frontend: Vitest with happy-dom

### Security Requirements
- Never hardcode secrets - use environment variables
- Dockerfiles must use non-root users (`USER nonroot`)
- All inputs validated via Pydantic (backend) or Zod (frontend)

### Multi-Tenancy
The app supports multi-tenant isolation. All data operations are scoped by tenant ID from the authenticated session context.
