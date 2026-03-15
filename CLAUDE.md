# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack Kanban board MVP with AI chat integration. The backend (FastAPI) serves the frontend (Next.js static export) and exposes a REST API. The app runs in Docker as a single container on port 8000.

**Auth:** Google OAuth 2.0 (Authorization Code flow). JWT stored as `HttpOnly` cookie (`access_token`, 24h). In non-production environments a `POST /api/auth/dev-login` bypass is available (disabled when `APP_ENV=production`).

## Commands

### Docker (primary way to run the app)
```bash
./scripts/start.sh   # Build image and start container at http://localhost:8000
./scripts/stop.sh    # Stop the container
```

### Backend (FastAPI + uv)
```bash
cd backend
uv sync                                        # Install dependencies (from backend/)
uv run pytest tests/                           # Run all backend tests (must run from backend/)
uv run pytest tests/test_auth.py::test_me_authenticated  # Run single test
```

To start the dev server, run from the **project root**:
```bash
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev          # Dev server (port 3000) — API calls won't work without the backend
npm run build        # Build + static export to frontend/out/
npm run test:unit    # Vitest unit tests
```

For e2e tests, start the backend first, then run:
```bash
cd frontend
PLAYWRIGHT_BASE_URL=http://127.0.0.1:8000 npx playwright test
```
This runs tests against the FastAPI server (port 8000) which serves both the built frontend and the API. The `frontend/out/` directory must be up to date (`npm run build`) before running e2e tests.

> **Important:** Use `uv` (not `pip`) for all Python dependency management. Never use pip directly.
> **Important:** Backend tests must be run from the `backend/` directory (not the project root), so that `app` is on the Python path.

## Architecture

### How it fits together

The Dockerfile uses a two-stage build: Node 20 builds the frontend static export (`frontend/out/`), then Python 3.12 runs the FastAPI backend which serves those static files at `/` via `StaticFiles`. All API routes are prefixed with `/api`.

In development, the frontend dev server proxies API calls to the FastAPI backend. In production (Docker), everything goes through port 8000.

### Backend (`backend/app/`)

| File | Purpose |
|------|---------|
| `main.py` | All FastAPI routes, OAuth flow, AI logic, static file mounting |
| `models.py` | SQLAlchemy ORM: `User`, `Board`, `KanbanColumn`, `Card` |
| `schemas.py` | Pydantic request/response schemas |
| `crud.py` | All database operations including card position reordering |
| `database.py` | SQLite config, session factory |
| `auth.py` | JWT creation/decoding (`python-jose`, HS256, 24h expiry) |
| `deps.py` | `get_db()` and `get_current_user()` dependency injection |
| `ai_schemas.py` | `AIChatRequest` / `AIChatResponse` schemas |

The SQLite file is `backend/data.db`. On startup, `on_startup` auto-migrates stale schemas (drops/recreates tables if `username` column is detected). User boards are created on first login, not via seeding.

**Auth flow:**
1. `GET /api/auth/google` → redirects to Google, sets `oauth_state` cookie (CSRF).
2. `GET /api/auth/google/callback` → exchanges code, validates state, upserts user, sets `access_token` JWT cookie, redirects to `/`.
3. All `/api/boards`, `/api/cards`, `/api/columns`, `/api/ai/chat` require a valid `access_token` cookie (enforced via `Depends(get_current_user)`).
4. `POST /api/auth/dev-login` — dev/test only (404 in production): creates or fetches a user by email, issues JWT.

**AI integration:** `POST /api/ai/chat` uses the OpenAI client pointed at OpenRouter (`openai/gpt-oss-120b` model). It sends the full board state as JSON context plus conversation history. The AI returns structured JSON with an optional `boardUpdates` field that the frontend applies as card/column mutations. Per-user conversation history is stored in-memory (lost on restart).

### Frontend (`frontend/src/`)

| Layer | Files |
|-------|-------|
| Pages | `app/page.tsx` — shows nothing while auth loads, then `<Login>` or `<KanbanBoard>` |
| State | `KanbanBoard.tsx` — owns all board state, drag-drop, AI chat, optimistic updates |
| API client | `lib/api.ts` — typed wrappers for all backend endpoints; converts numeric backend IDs to string frontend IDs |
| Auth | `lib/auth.tsx` — `AuthContext` with `useAuth()` hook; calls `GET /api/auth/me` on mount to restore session |
| Types | `lib/kanban.ts` — `Card`, `Column`, `BoardData` types and `moveCard()` logic |

**Frontend auth flow:**
- On mount, `AuthProvider` calls `api.getMe()` (`GET /api/auth/me`). If 200, sets `user`; if 401, sets `user=null`. A `loading` flag prevents flashing the login page.
- `loginWithGoogle()` — sets `window.location.href = '/api/auth/google'` (full redirect, not a fetch).
- `logout()` — calls `api.logout()` (`POST /api/auth/logout`), then sets `user=null`.
- `Login.tsx` shows a single "Sign in with Google" button. Displays an error message when `?error=oauth_failed` is in the URL (set by the backend on OAuth failure).
- `api.getMe()` is the only API function that does not throw on 401; it returns `null` instead.

Drag-and-drop uses `@dnd-kit`. All mutations are optimistic: the UI updates immediately, with rollback on API failure.

**AI board updates:** When the AI returns a `boardUpdates` payload, `KanbanBoard.applyBoardUpdates()` parses it and applies card creation/movement/deletion. Updated cards are briefly highlighted via `highlightedCardIds` state.

### Styling

CSS custom properties defined in `globals.css`:
- `--accent-yellow: #ecad0a`, `--primary-blue: #209dd7`, `--secondary-purple: #753991`, `--navy-dark: #032147`
- Fonts: Space Grotesk (display), Manrope (body)

No emojis in code or UI per project conventions.

## Environment

Copy `.env.template` to `.env` and fill in required values:
```
OPENROUTER_API_KEY=<your_key>
GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from Google Cloud Console>
APP_BASE_URL=http://localhost:8000   # used to build OAuth redirect URI
JWT_SECRET=<random secret>           # signs access_token cookies
APP_ENV=development                  # set to "production" to disable dev-login
```

The `.env` file is **not** baked into the Docker image; it is mounted at runtime via `--env-file .env` in `start.sh`.
