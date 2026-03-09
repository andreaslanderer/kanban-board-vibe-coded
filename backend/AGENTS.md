# Backend Architecture

The backend is a Python FastAPI application responsible for:

- Serving the React/Next.js frontend static build in the final product
- Exposing a REST API under `/api/*` for authentication, board data, and later AI integration
- Managing persistence via SQLite with SQLAlchemy models (added in later phases)
- Handling AI calls via OpenRouter (also in later phases)

## Project Layout

```
backend/
  pyproject.toml         # Python project metadata and dependencies (uv package manager)
  requirements.txt       # Fallback dependencies list
  app/
    __init__.py
    main.py              # FastAPI application entrypoint
    models.py            # (future) SQLAlchemy ORM models
    schemas.py           # (future) Pydantic schemas
    deps.py              # (future) dependency helpers
  tests/
    test_main.py         # Basic tests for hello endpoints
```

## Dependencies

- **FastAPI** for web framework
- **Uvicorn** as ASGI server
- **SQLAlchemy** for ORM/database access (yet to be implemented)
- **Pydantic** for data validation

## Launching

During development the app can be started with `uv run backend.app.main:app --reload`.
In Docker, a multi-stage build will ensure the frontend is built and then the backend runs with the compiled static assets copied into the image.

The `/` route currently returns a simple HTML string; `/api/hello` returns a JSON health-check.
