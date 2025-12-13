# Enterprise AI Budget Architect

A local-first, AI-powered personal finance dashboard designed for privacy, speed, and intelligent analysis. Built with a modern "Clean Architecture" stack.

## 🚀 Features

### Phase 1: The Cleaner (Frictionless Ingestion)
*   **Universal Drag-and-Drop Parser**: Automatically detects headers and maps columns from any Excel/CSV file.
*   **Smart De-Duplication**: Hashes transaction data (Date + Amount + Description) to prevent duplicates during multi-file uploads.
*   **"Gap" Detection**: Automatically flags missing periods in your financial history (e.g., >7 days without transactions).
*   **Multi-Source Merging**: Seamlessly stitches together data from local files, OneDrive, or SharePoint.

### Phase 2: The Analyst (Analysis & Enrichment)
*   **Natural Language Query (NLQ)**: Ask questions in plain English (e.g., *"How much did I spend on Uber?"*) and get instant answers.
*   **Flash Fill Categorization**: AI suggests categories based on your history (e.g., auto-categorizing "Netflix" as "Entertainment").
*   **Recurring Subscription Detector**: Identifies regular monthly payments and highlights them.
*   **Spending Anomaly Highlighting**: Flags transactions that are >2x your average spending for a specific merchant.
*   **Regex Rule Generator**: Create custom regex rules (e.g., `^AMZN.*` -> "Shopping") for automated categorization.

### Phase 3: The Vault (Privacy & Output)
*   **Local-First Architecture**: All data lives in a local SQLite database. No data leaves your machine.
*   **Sandbox Simulator**: Run "What If?" scenarios (e.g., *"Reduce Dining by 20%"*) to see projected savings without altering real data.
*   **Clean Export**: Export your cleaned, enriched "Golden Record" dataset to CSV.
*   **Security Gates**: All API endpoints secured with Authentication Middleware.

## 🛠️ Technology Stack

### Backend
*   **Language**: Python 3.12+
*   **Framework**: FastAPI
*   **Architecture**: Clean Architecture / Hexagonal
*   **Validation**: Pydantic V2
*   **Logging**: Structlog (JSON)

### Frontend
*   **Language**: TypeScript 5.4+
*   **Framework**: Lit (Web Components)
*   **State Management**: TanStack Store
*   **Design System**: Custom "2025 Metallic/Minimalist" (CSS Variables, Shadow DOM)

### Infrastructure
*   **Containerization**: Docker (Multi-stage builds, non-root users)
*   **Orchestration**: Kubernetes (Kustomize)
*   **Proxy**: Nginx

## 🏁 Getting Started

### Prerequisites
*   Docker & Docker Compose

### Run Locally
1.  Clone the repository.
3.  Set the required environment variable:
    ```bash
    export AUTH_SECRET_KEY="your-secure-secret-key"
    ```
4.  Start the application:
    ```bash
    docker-compose up --build
    ```
5.  Access the dashboard at `http://localhost:3000`.

## 🔒 Security
*   **Non-Root Containers**: All services run as non-root users for security.
*   **Auth Middleware**: Extensible authentication provider pattern (Mock for local, OIDC ready for prod).
*   **Input Sanitization**: Strict Pydantic validation on all inputs.
