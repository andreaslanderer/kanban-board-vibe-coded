# Project Management MVP

A Kanban board application with AI chat integration, built as a full-stack MVP.

## Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS, dnd-kit
- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Auth**: Google OAuth 2.0 (JWT stored as HttpOnly cookie)
- **AI**: OpenRouter API (chat assistant with board mutation support)
- **Containerization**: Docker

## Features

- Google OAuth 2.0 authentication
- Kanban board with drag-and-drop cards
- Persistent data storage (SQLite)
- AI chat assistant — ask questions about your board or instruct it to create, move, or delete cards

## Quick Start

### Prerequisites

- Docker
- A Google OAuth client ID and secret ([Google Cloud Console](https://console.cloud.google.com/))
- An OpenRouter API key ([openrouter.ai](https://openrouter.ai/))
- Node.js 20+ and Python 3.12+ (for local development only)

### Running with Docker

1. Clone the repository
2. Copy `.env.template` to `.env` and fill in all values:
   ```bash
   cp .env.template .env
   ```
   ```
   OPENROUTER_API_KEY=...
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   APP_BASE_URL=http://localhost:8000
   JWT_SECRET=...        # generate with: openssl rand -hex 32
   APP_ENV=development
   ```
   In the Google Cloud Console, register `http://localhost:8000/api/auth/google/callback`
   as an authorised redirect URI for your OAuth client.

3. Build and start the container:
   ```bash
   ./scripts/start.sh
   ```
4. Open http://localhost:8000 and sign in with Google.

To stop the container:
```bash
./scripts/stop.sh
```

### Local Development

#### Backend

Run from the **project root** (not from `backend/`):

```bash
uv sync --no-editable
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on http://localhost:3000. Note: API calls use relative `/api/*` URLs with no proxy configured, so they will only work when accessed through the backend on port 8000. For full integration during development, use the backend URL (port 8000) after running `npm run build`.

### Testing

#### Backend

```bash
cd backend
uv run pytest tests/ -v
```

#### Frontend unit tests

```bash
cd frontend
npm run test:unit
```

#### E2E tests

Requires the backend running on port 8000 with a built frontend (`npm run build`):

```bash
cd frontend
PLAYWRIGHT_BASE_URL=http://127.0.0.1:8000 npx playwright test
```

## Project Structure

```
backend/    FastAPI app, SQLAlchemy models, pytest tests
frontend/   Next.js app, React components, Vitest + Playwright tests
docs/       Documentation and planning
scripts/    start.sh / stop.sh for Docker
```

## Development Notes

- SQLite database is stored inside the container and resets on each `docker run`. Mount a volume if you need persistence across restarts.
- The `APP_ENV=development` setting enables a `POST /api/auth/dev-login` bypass used by the test suite. Set `APP_ENV=production` to disable it.
