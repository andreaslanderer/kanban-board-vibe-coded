# Project Management MVP

A Kanban board application with AI integration, built as a full-stack MVP.

## Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS, dnd-kit
- **Backend**: FastAPI, SQLAlchemy, SQLite
- **AI**: OpenRouter API (for future AI features)
- **Containerization**: Docker

## Features

- User authentication (hardcoded: user/password)
- Kanban board with drag-and-drop cards
- Persistent data storage
- AI chat integration (planned)

## Quick Start

### Prerequisites

- Docker
- Node.js 18+ (for local development)
- Python 3.12+ (for local development)

### Running with Docker

1. Clone the repository
2. Build and run the container:
   ```bash
   ./scripts/start.sh
   ```
3. Open http://localhost:8000 in your browser
4. Log in with username "user" and password "password"

### Local Development

#### Backend

```bash
cd backend
uv sync --no-editable
uv run -m uvicorn backend.app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000, but for full integration, run the backend and access via the backend's served frontend.

### Testing

#### Unit Tests
```bash
cd frontend && npm run test:unit
cd backend && python -m pytest
```

#### E2E Tests
```bash
cd frontend && npm run test:e2e
```
(Note: Requires the backend running on localhost:8000)

## Project Structure

- `backend/` - FastAPI backend with SQLAlchemy models
- `frontend/` - Next.js frontend with React components
- `docs/` - Documentation and planning
- `scripts/` - Start/stop scripts for Docker

## Development Notes

- The app uses SQLite for simplicity; data persists in the container.
- Authentication is client-side only for MVP.
- AI features are planned for future parts.