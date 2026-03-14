# syntax=docker/dockerfile:1

# Stage 1: build frontend using Node
FROM node:20 AS frontend-build
WORKDIR /workspace/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend .
RUN npm run build

# Stage 2: build backend using Python
FROM python:3.12-slim AS backend-build
WORKDIR /workspace


# copy project files
COPY backend/pyproject.toml ./
# install python dependencies using uv
RUN uv sync --no-editable

# copy backend source
COPY backend ./backend

# copy built frontend static export for later serving
COPY --from=frontend-build /workspace/frontend/out ./frontend/out
COPY --from=frontend-build /workspace/frontend/public ./frontend/public

# Copy .env file
COPY .env .env

EXPOSE 8000

# run uvicorn application from package
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]