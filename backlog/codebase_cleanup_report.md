# Codebase Cleanup & Structure Review Report

## Analysis Date
**December 13, 2025**

## Executive Summary
The project structure is generally clean and follows the defined Hexagonal Architecture. However, several temporary artifacts, unused dependencies, and "debug" scripts have accumulated in the root directory.

---

## 1. File Artifacts to Remove
The following files in the root directory appear to be temporary scripts or test data generated during development. They clutter the workspace and should be deleted or moved to `scripts/` or `tests/data/`.

| File | Reason | Action |
|------|--------|--------|
| `check_overlap.py` | One-off debug script | 🗑️ Delete |
| `debug_check_sample.py` | One-off debug script | 🗑️ Delete |
| `debug_third_parse.py` | One-off debug script | 🗑️ Delete |
| `debug_upload_logic.py` | One-off debug script | 🗑️ Delete |
| `generate_multisheet_sample.py` | Test data generator | ➡️ Move to `scripts/` or Delete |
| `generate_second_budget.py` | Test data generator | ➡️ Move to `scripts/` or Delete |
| `generate_third_budget.py` | Test data generator | ➡️ Move to `scripts/` or Delete |
| `sample_budget.xlsx` | Human testing data | ✅ Keep (for human testing) |
| `second_sample_budget.xlsx` | Human testing data | ✅ Keep (for human testing) |
| `third_sample_budget.xlsx` | Human testing data | ✅ Keep (for human testing) |
| `backend_rule_violations_report.md` | Compliance report (Completed) | 🗑️ Delete or Archive |
| `dependency_report.md` | Compliance report (Completed) | 🗑️ Delete or Archive |

---

## 2. Unused Dependencies

### Backend (`backend/pyproject.toml`)
*   **`authlib==1.3.0`**:
    *   **Status:** ❌ **UNUSED**
    *   **Analysis:** The codebase uses `python-jose` for JWT handling and custom OIDC logic in `src/infrastructure/auth/oidc_auth.py` and `src/application/sso_service.py`. There are no imports of `authlib` in `backend/src`.
    *   **Recommendation:** Uninstall to reduce image size and attack surface.

### Frontend (`frontend/package.json`)
*   **`@tanstack/router`**:
    *   **Status:** ⚠️ **UNUSED / OUTDATED**
    *   **Analysis:** The project currently uses manual routing in `app-root.ts` (`window.location.pathname.includes(...)`). The installed version is an outdated beta.
    *   **Recommendation:** Remove if continuing with manual routing, OR upgrade to v1 and fully implement.

---

## 3. Structural Recommendations
*   **`scripts/` Directory:** Currently contains only `update_sample_budget.py`. It is the appropriate home for any reusable data generation scripts.
*   **`backend/tests/`:** Well organized.
*   **`frontend/src/`:** Well organized by feature/type.

## Action Plan
1.  **Cleanup Python Scripts:** Delete `check_overlap.py`, `debug_check_sample.py`, `debug_third_parse.py`, `debug_upload_logic.py`, `generate_multisheet_sample.py`, `generate_second_budget.py`, `generate_third_budget.py`.
2.  **Cleanup Reports:** Delete `backend_rule_violations_report.md`, `dependency_report.md` (or archive).
3.  **Backend:** `pip uninstall authlib` and update `pyproject.toml`.
4.  **Frontend:** `npm uninstall @tanstack/router` (or upgrade/implement).
