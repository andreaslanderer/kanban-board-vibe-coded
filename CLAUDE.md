# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack Kanban board MVP with AI chat integration. The backend (FastAPI) serves the frontend (Next.js static export) and exposes a REST API. The app runs in Docker as a single container on port 8000.

**Auth:** Hardcoded credentials — username: `user`, password: `password`. This is intentional for the MVP.

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
uv run pytest tests/test_main.py::test_auth_login_success  # Run single test
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
| `main.py` | All FastAPI routes, startup seeding, AI logic, static file mounting |
| `models.py` | SQLAlchemy ORM: `User`, `Board`, `KanbanColumn`, `Card` |
| `schemas.py` | Pydantic request/response schemas |
| `crud.py` | All database operations including card position reordering |
| `database.py` | SQLite config, session factory |
| `deps.py` | `get_db()` dependency injection |
| `ai_schemas.py` | `AIChatRequest` / `AIChatResponse` schemas |

The database is seeded on startup with a default user, board, 5 columns, and 2 sample cards (`crud.seed_default_data()`). The SQLite file is `backend/data.db`.

**AI integration:** `POST /api/ai/chat` uses the OpenAI client pointed at OpenRouter (`openai/gpt-oss-120b` model). It sends the full board state as JSON context plus conversation history. The AI returns structured JSON with an optional `boardUpdates` field that the frontend applies as card/column mutations. Per-user conversation history is stored in-memory (lost on restart).

### Frontend (`frontend/src/`)

| Layer | Files |
|-------|-------|
| Pages | `app/page.tsx` — renders `<Login>` or `<KanbanBoard>` based on auth state |
| State | `KanbanBoard.tsx` — owns all board state, drag-drop, AI chat, optimistic updates |
| API client | `lib/api.ts` — typed wrappers for all backend endpoints; converts numeric backend IDs to string frontend IDs |
| Auth | `lib/auth.tsx` — `AuthContext` with `useAuth()` hook; state in `sessionStorage` |
| Types | `lib/kanban.ts` — `Card`, `Column`, `BoardData` types and `moveCard()` logic |

Drag-and-drop uses `@dnd-kit`. All mutations are optimistic: the UI updates immediately, with rollback on API failure.

**AI board updates:** When the AI returns a `boardUpdates` payload, `KanbanBoard.applyBoardUpdates()` parses it and applies card creation/movement/deletion. Updated cards are briefly highlighted via `highlightedCardIds` state.

### Styling

CSS custom properties defined in `globals.css`:
- `--accent-yellow: #ecad0a`, `--primary-blue: #209dd7`, `--secondary-purple: #753991`, `--navy-dark: #032147`
- Fonts: Space Grotesk (display), Manrope (body)

No emojis in code or UI per project conventions.

## Environment

Copy `.env.template` to `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=<your_key>
```

The `.env` file is copied into the Docker image at build time.
