# OAuth Integration Plan — Google Sign-In

This document describes all changes required to replace the hardcoded client-side authentication with real OAuth 2.0 login via Google. No code has been changed yet.

---

## Overview of the New Flow

1. User clicks **Sign in with Google** on the login page.
2. Frontend redirects the browser to `GET /api/auth/google`.
3. Backend generates a short-lived `state` token (CSRF protection), stores it in a cookie, and redirects the browser to Google's authorization URL.
4. User approves on Google. Google redirects to `GET /api/auth/google/callback?code=...&state=...`.
5. Backend validates the `state`, exchanges the `code` for a Google access token, and fetches the user's profile (email, name, Google ID).
6. Backend finds or creates the user in the database. If the user is new, a default Kanban board is created for them.
7. Backend issues a signed JWT (24 h expiry), sets it as an `HttpOnly; SameSite=Lax` cookie, and redirects to `/`.
8. On every page load, the frontend calls `GET /api/auth/me` to check the session; the cookie is sent automatically.
9. All protected endpoints validate the JWT via a `get_current_user` dependency. A missing or expired token returns 401.
10. Logout calls `POST /api/auth/logout`, which clears the cookie.

---

## Step 1 — New environment variables

Add these to `.env` and `.env.template`:

| Variable | Description |
|---|---|
| `GOOGLE_CLIENT_ID` | OAuth 2.0 client ID from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 client secret |
| `JWT_SECRET` | Random 32-byte secret for signing JWTs (e.g. `openssl rand -hex 32`) |
| `APP_BASE_URL` | Public base URL used as the OAuth redirect URI (e.g. `http://localhost:8000`) |

The Google Cloud Console must have `{APP_BASE_URL}/api/auth/google/callback` registered as an authorised redirect URI.

---

## Step 2 — New backend dependencies (`backend/pyproject.toml`)

Add:
- `authlib` — handles the OAuth 2.0 authorisation code flow with Google
- `python-jose[cryptography]` — JWT creation and validation
- `itsdangerous` — signed `state` cookie for CSRF protection (already common in Python web stacks)

---

## Step 3 — Database model changes (`backend/app/models.py`)

Update the `User` model:

| Column | Change |
|---|---|
| `username` | Remove (replaced by `email`) |
| `password_hash` | Remove |
| `email` | Add — unique, indexed, not null |
| `google_id` | Add — unique, indexed, not null |
| `display_name` | Add — string, nullable (from Google profile `name`) |
| `avatar_url` | Add — string, nullable (from Google profile `picture`) |
| `created_at` | Keep |

Provide an Alembic migration or drop-and-recreate logic (acceptable for SQLite MVP since there is no production data to preserve).

---

## Step 4 — New CRUD functions (`backend/app/crud.py`)

Add:
- `get_user_by_google_id(db, google_id) -> User | None`
- `get_user_by_email(db, email) -> User | None`
- `create_oauth_user(db, google_id, email, display_name, avatar_url) -> User`

Update:
- `seed_default_data()` — remove the hardcoded `create_user(db, "user", "password")` call. The function now only ensures schema exists; user + board creation happens at first login.

Remove:
- `create_user(db, username, password)` — no longer needed once the old login is gone.

---

## Step 5 — JWT utility module (`backend/app/auth.py`) — new file

Create `backend/app/auth.py` with:

- `create_access_token(user_id: int) -> str` — signs a JWT with `sub=<user_id>`, `exp=now+24h`, using `JWT_SECRET`.
- `decode_access_token(token: str) -> int` — validates and returns `user_id`, raises `HTTPException(401)` on failure.

---

## Step 6 — Auth dependency (`backend/app/deps.py`)

Add a new dependency:

```python
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = decode_access_token(token)
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

Keep the existing `get_db()` unchanged.

---

## Step 7 — New auth endpoints (`backend/app/main.py`)

Add:

### `GET /api/auth/google`
- Generates a random `state` value.
- Stores `state` in a short-lived signed cookie (`state_token`, 5 min expiry).
- Redirects browser to Google's OAuth authorization URL with `client_id`, `redirect_uri`, `scope=openid email profile`, and `state`.

### `GET /api/auth/google/callback`
- Validates `state` parameter against the `state_token` cookie (returns 400 on mismatch).
- Exchanges `code` for a Google access token using `authlib`.
- Fetches user profile from Google (`/oauth2/v3/userinfo`).
- Calls `get_user_by_google_id` — if not found, calls `create_oauth_user` and then creates a default board + 5 columns for the new user.
- Issues a JWT via `create_access_token`.
- Sets the JWT as an `HttpOnly; SameSite=Lax; Path=/` cookie named `access_token`.
- Clears the `state_token` cookie.
- Redirects to `/`.

### `GET /api/auth/me`
- Depends on `get_current_user`.
- Returns the current user's `id`, `email`, `display_name`, `avatar_url`.
- Returns 401 if no valid session.

### `POST /api/auth/logout`
- Clears the `access_token` cookie.
- Returns `{"success": true}`.

Remove or disable:
- `POST /api/auth/login` — the username/password endpoint. During the transition this can be kept behind an `APP_ENV != production` guard for local dev without Google credentials (see Step 9).

---

## Step 8 — Protect all existing endpoints (`backend/app/main.py`)

Replace every occurrence of:
```python
user = crud.get_user_by_username(db, "user")
```
with:
```python
user: User = Depends(get_current_user)
```

This affects: `GET /api/boards`, `POST /api/boards/.../cards`, `PATCH /api/cards/...`, `DELETE /api/cards/...`, `PUT /api/cards/.../move`, `PATCH /api/columns/...`, `POST /api/ai/chat`, `GET /api/ai/test`.

Each endpoint now receives the authenticated user and uses `user.id` for all DB queries — enforcing per-user data isolation.

---

## Step 9 — Dev-only login bypass (for local dev and testing)

When `APP_ENV=development` (default if unset), expose:

### `POST /api/auth/dev-login`
```json
{ "email": "test@example.com" }
```
- Finds or creates a user by email (no Google ID required — set `google_id` to `"dev-<email>"`).
- Issues and sets the JWT cookie.
- Returns the user object.
- **Blocked unconditionally in production** (`APP_ENV=production` → 404).

This allows backend unit tests and E2E tests to authenticate without real Google credentials.

---

## Step 10 — Schemas (`backend/app/schemas.py`)

Add:
- `UserOut` — update to include `email`, `display_name`, `avatar_url` (remove `username`).
- `MeResponse` — alias for `UserOut`, returned by `/api/auth/me`.

Remove:
- `LoginRequest` (username + password).
- `LoginResponse` — replace with the new `MeResponse`.

---

## Step 11 — Frontend: auth context (`frontend/src/lib/auth.tsx`)

Replace the entire module. New behaviour:

- **On mount:** call `GET /api/auth/me`.
  - If 200 → set `user` state (email, displayName, avatarUrl).
  - If 401 → set `user` to `null` (shows login page).
- **`loginWithGoogle()`** — redirects `window.location.href` to `/api/auth/google`.
- **`logout()`** — calls `POST /api/auth/logout`, then sets `user` to `null`.

Remove:
- Hardcoded credential check (`username === "user" && password === "password"`).
- `sessionStorage` usage.
- The `login(username, password)` function.

The `api.ts` client does not need to change — cookies are sent automatically for same-origin requests.

---

## Step 12 — Frontend: login page (`frontend/src/components/Login.tsx`)

Replace the username/password form with a single **Sign in with Google** button:

```tsx
<button onClick={() => loginWithGoogle()}>
  Sign in with Google
</button>
```

Remove all username/password input fields, the `handleSubmit` function, and the error state for invalid credentials (the new error state would cover OAuth failures, e.g. a query param `?error=oauth_failed` set by the callback on failure).

---

## Step 13 — Frontend: API client (`frontend/src/lib/api.ts`)

- Remove the `login(username, password)` function — authentication is now handled by browser redirects, not fetch calls.
- Add a `getMe()` function: `GET /api/auth/me` → `UserOut`.
- Add `logout()`: `POST /api/auth/logout`.
- Add `fetch` option `credentials: 'include'` to `apiRequest` if the app is ever served cross-origin. (Not required for the current same-origin Docker setup but good practice.)

---

## Step 14 — Update backend tests (`backend/tests/`)

### `conftest.py`
- Add a `auth_client` fixture that calls `POST /api/auth/dev-login` after creating the test client, storing the returned cookie on subsequent requests.
- Alternatively, generate a valid JWT directly via `create_access_token` and inject it into the test client's cookies.

### `test_main.py`
- Replace `test_auth_login_success` / `test_auth_login_failure` with:
  - `test_dev_login_creates_user_and_board` — verifies a new user gets a board on first login.
  - `test_dev_login_reuses_existing_user` — verifies a returning user keeps their data.
  - `test_me_authenticated` — verifies `/api/auth/me` returns user when cookie is set.
  - `test_me_unauthenticated` — verifies `/api/auth/me` returns 401 when no cookie.
  - `test_protected_endpoint_requires_auth` — verifies `/api/boards` returns 401 without cookie.
- Update all existing board/card/AI tests to use the `auth_client` fixture.

### `test_ai_chat.py`
- Update to use `auth_client` fixture.

---

## Step 15 — Update E2E tests (`frontend/tests/kanban.spec.ts`)

Replace the `doLogin` helper:
```typescript
async function doLogin(page) {
  await page.request.post("/api/auth/dev-login", {
    data: { email: "e2e@test.com" }
  });
  await page.goto("/");
}
```
The page now loads directly onto the Kanban board (no login form needed when the cookie is set).

Update:
- `"shows login form when not authenticated"` — still valid, just verify the Google button is shown.
- `"rejects invalid credentials"` — remove (no longer applicable).
- `"allows user to log in and then log out"` — update to click the new "Log out" button and check the Google sign-in screen appears.

---

## Step 16 — Cleanup checklist

Once all the above is implemented and tests pass, delete/remove:

- [ ] `User.username` column and all references
- [ ] `User.password_hash` column and all references
- [ ] `crud.create_user(db, username, password)` function
- [ ] `schemas.LoginRequest` and `schemas.LoginResponse`
- [ ] `POST /api/auth/login` endpoint
- [ ] Hardcoded `get_user_by_username(db, "user")` calls (all 6+ occurrences)
- [ ] Client-side credential check in `frontend/src/lib/auth.tsx`
- [ ] Username/password form in `frontend/src/components/Login.tsx`
- [ ] `api.login(username, password)` in `frontend/src/lib/api.ts`
- [ ] `sessionStorage` usage in auth context

---

## Step 17 — Docker and deployment notes

- `start.sh` passes `--env-file .env` already — just ensure the three new variables (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `JWT_SECRET`) are present.
- The Google Cloud Console project must add `http://localhost:8000/api/auth/google/callback` to **Authorised redirect URIs**.
- For any non-localhost deployment, `APP_BASE_URL` must be updated and the new URL registered in Google Cloud Console.
- `APP_ENV=production` must be set in production to disable the dev-login bypass.

---

## Files changed summary

| File | Change |
|---|---|
| `.env` / `.env.template` | Add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `JWT_SECRET`, `APP_BASE_URL` |
| `backend/pyproject.toml` | Add `authlib`, `python-jose[cryptography]`, `itsdangerous` |
| `backend/app/models.py` | Replace `username`/`password_hash` with `email`, `google_id`, `display_name`, `avatar_url` |
| `backend/app/crud.py` | Add OAuth user functions; remove `create_user`; update `seed_default_data` |
| `backend/app/auth.py` | **New file** — JWT creation and validation |
| `backend/app/deps.py` | Add `get_current_user` dependency |
| `backend/app/schemas.py` | Update `UserOut`; remove `LoginRequest`/`LoginResponse`; add `MeResponse` |
| `backend/app/main.py` | Add 4 auth endpoints; protect all existing endpoints; remove old login |
| `backend/tests/conftest.py` | Add `auth_client` fixture |
| `backend/tests/test_main.py` | Replace credential tests; add auth coverage |
| `backend/tests/test_ai_chat.py` | Use `auth_client` fixture |
| `frontend/src/lib/auth.tsx` | Rewrite — remove hardcoded check; use `/api/auth/me` + redirect flow |
| `frontend/src/lib/api.ts` | Remove `login()`; add `getMe()` and `logout()` |
| `frontend/src/components/Login.tsx` | Replace form with Google sign-in button |
| `frontend/tests/kanban.spec.ts` | Update `doLogin` to use dev-login API; update auth-related tests |
