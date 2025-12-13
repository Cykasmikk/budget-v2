# Container vs Codebase Delta Report

## Analysis Date
**December 13, 2025**

## Status Summary
| Service | Status | Delta | Action Required |
|---------|--------|-------|-----------------|
| **Frontend** | ⚠️ **Out of Sync** | `package.json` version is `0.0.0` (Container) vs `0.1.0` (Host). Volume mount only covers `src/`, so root config changes are missed. | **Rebuild** |
| **Backend** | ✅ **Synced** | Source code is live-mounted (`/app`). New files like `envelope.py` are present. | None |
| **Database** | ✅ **Synced** | Data volume persists. | None |

## Detailed Findings

### 1. Frontend (`test-global-rules-frontend-1`)
*   **Running Image Age:** 4 hours
*   **Delta:** The `package.json` file inside the container lists version `"0.0.0"`. The host file was updated to `"0.1.0"` in the latest commit.
*   **Reason:** The `docker-compose.yml` mounts `./frontend/src:/app/src`. It does **not** mount `package.json` or `vite.config.ts`. These are copied only during `docker build`.
*   **Impact:** The application is running with metadata that doesn't match the released tag `v0.1.0`.

### 2. Backend (`test-global-rules-backend-1`)
*   **Running Image Age:** 29 hours
*   **Delta:** None in logic.
*   **Verification:** Confirmed presence of new file `src/interface/envelope.py` inside the container.
*   **Note:** Dependencies in `pyproject.toml` have not changed since the last build, so no rebuild is strictly necessary for dependencies.

## Recommended Command
To synchronize the running environment with the codebase:

```bash
docker-compose up -d --build frontend
```
