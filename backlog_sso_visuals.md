# Backlog: Enhanced SSO Visuals & Provider Discovery

## Overview
**Objective:** Improve the user experience for Single Sign-On (SSO) login by implementing visual provider recognition and domain-based discovery.
**Current State:** Generic "Sign in with SSO" button with a lock emoji.
**Target State:** Provider-branded buttons (Google, Microsoft) or Domain-based Home Realm Discovery.

---

## 1. Feature: Provider-Branded Login Buttons (Phase 1)

### User Story
As a user belonging to an organization using Google Workspace or Microsoft Entra ID, I want to see a recognizable logo on the login button so that I can quickly identify my login method.

### Technical Implementation

#### Frontend (`frontend/src/views/login-view.ts`)
*   **Logic:**
    *   Parse `ssoProviderName` from `auth_config`.
    *   Map keywords ("Google", "Microsoft", "Entra", "Azure") to specific icon assets or SVG paths.
    *   Fallback to generic "Key/Lock" icon if no match found.
*   **Assets:**
    *   Add SVG icons for Google ('G' logo) and Microsoft (Windows flag) to `frontend/src/assets/` or inline in `shared.ts`.
*   **Component Update:**
    *   Refactor the SSO button rendering in `render()` to use a helper method `getProviderIcon(name)`.

#### Backend (`backend/src/interface/settings_router.py`)
*   **No Schema Changes Required:** `provider_name` is already exposed via `/api/v1/settings`.

### Acceptance Criteria
- [ ] If provider name contains "Google", show Google 'G' logo.
- [ ] If provider name contains "Microsoft" or "Entra", show Microsoft logo.
- [ ] If provider name is unknown, show generic lock icon.
- [ ] Button text remains "Sign in with {Provider Name}".

---

## 2. Feature: Domain-Based Home Realm Discovery (Phase 2 - Advanced)

### User Story
As an enterprise user, I want to enter my email address and be automatically redirected to my company's SSO page without needing to select a specific button or see a password field if it's not required.

### Technical Implementation

#### Frontend (`frontend/src/views/login-view.ts`)
*   **State:** Add `isCheckingDomain` (boolean) and `ssoRedirectUrl` (string).
*   **Interaction:**
    *   On email input blur (loss of focus) or "Next" click, call backend API.
    *   API Endpoint: `GET /api/v1/auth/discovery?email={email}`.
*   **UI Logic:**
    *   **If SSO Required:** Hide password field. Change "Sign In" button text to "Continue to {Provider}". Action becomes redirection.
    *   **If Password Required:** Show password field. Action remains standard login.

#### Backend (`backend/src/interface/auth_router.py`)
*   **New Endpoint:** `GET /auth/discovery`
*   **Logic:**
    1.  Parse domain from email (e.g., `user@acme.com` -> `acme.com`).
    2.  Lookup `Tenant` by domain.
    3.  Return JSON:
        ```json
        {
          "sso_enabled": true,
          "provider_name": "Okta",
          "login_url": "..." 
        }
        ```

### Acceptance Criteria
- [ ] Typing an email belonging to an SSO-enabled tenant hides the password input.
- [ ] Typing a non-SSO email shows the password input.
- [ ] "Sign In" button creates seamless redirection for SSO users.

---

## 3. Security & Compliance
*   **Security Gate:** Do not fetch logos from external URLs (prevents tracking/leakage). Use local SVG assets.
*   **Accessibility:** Ensure all icon buttons have `aria-label` describing the provider (e.g., "Sign in with Google").
*   **Testing:** Add unit tests for the icon mapping logic and domain discovery state transitions.
