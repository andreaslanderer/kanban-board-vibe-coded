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
  app/
    __init__.py
    main.py              # FastAPI application entrypoint
    models.py            # (future) SQLAlchemy ORM models
    schemas.py           # (future) Pydantic schemas
    deps.py              # (future) dependency helpers
  tests/
    test_main.py         # Basic tests for hello endpoints
```


## Dependency Management

All Python dependencies are managed with the [uv](https://github.com/astral-sh/uv) package manager. Do not use pip or requirements.txt.

### Installing dependencies

```bash
cd backend
uv sync --no-editable
```

### Adding a new dependency

```bash
cd backend
uv pip install <package-name>
```

This will update `pyproject.toml` automatically.

### Running the backend

```bash
uv run backend.app.main:app --reload
```

In Docker, the build will use uv to install dependencies and then run the backend with the compiled static assets copied into the image.

The `/` route currently returns a simple HTML string; `/api/hello` returns a JSON health-check.
