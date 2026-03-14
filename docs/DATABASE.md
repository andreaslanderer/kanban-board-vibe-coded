# Database Schema Design

This document defines the data model for the Kanban app. The goals are:

- Support multiple users and one board per user (MVP constraint: only one board is used in the UI, but the schema supports more)
- Represent columns and cards in a way that is easy to query and update
- Keep the schema SQLite-friendly and compatible with other relational DBs
- Allow simple migrations in the future

---

## Core Entities

### `users`
Stores user accounts. For the MVP, authentication remains hardcoded (username "user" / password "password"), but the schema supports real users.

| Column     | Type    | Notes |
|-----------|---------|-------|
| `id`      | INTEGER PRIMARY KEY AUTOINCREMENT | Unique user identifier |
| `username`| TEXT NOT NULL UNIQUE | Login name |
| `password_hash` | TEXT NOT NULL | Hashed password (future use) |
| `created_at` | TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP | Creation timestamp |


### `boards`
A board belongs to a user. For MVP, each user will have at most one board, but the schema allows multiple.

| Column      | Type    | Notes |
|-------------|---------|-------|
| `id`        | INTEGER PRIMARY KEY AUTOINCREMENT | Unique board identifier |
| `user_id`   | INTEGER NOT NULL | FK → users(id) |
| `name`      | TEXT NOT NULL | E.g., "My Project" |
| `created_at`| TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP | Creation timestamp |


### `columns`
A board contains ordered columns (e.g., "To Do", "In Progress", "Done").

| Column       | Type    | Notes |
|--------------|---------|-------|
| `id`         | INTEGER PRIMARY KEY AUTOINCREMENT | Unique column identifier |
| `board_id`   | INTEGER NOT NULL | FK → boards(id) |
| `title`      | TEXT NOT NULL | Column name |
| `position`   | INTEGER NOT NULL | Order in board (0-based or 1-based) |
| `created_at` | TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP | Creation timestamp |


### `cards`
Cards belong to a column and can be reordered within it.

| Column       | Type    | Notes |
|--------------|---------|-------|
| `id`         | INTEGER PRIMARY KEY AUTOINCREMENT | Unique card identifier |
| `column_id`  | INTEGER NOT NULL | FK → columns(id) |
| `title`      | TEXT NOT NULL | Card title |
| `description`| TEXT | Optional longer description |
| `position`   | INTEGER NOT NULL | Order within the column (0-based or 1-based) |
| `created_at` | TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP | Updated on change |


## Example JSON Representation

This JSON shows a complete board object including columns and cards.

```json
{
  "id": 1,
  "userId": 1,
  "name": "My Project",
  "columns": [
    {
      "id": 10,
      "boardId": 1,
      "title": "To Do",
      "position": 0,
      "cards": [
        {
          "id": 100,
          "columnId": 10,
          "title": "Set up project",
          "description": "Create repo, initialize backend and frontend",
          "position": 0
        },
        {
          "id": 101,
          "columnId": 10,
          "title": "Create schema design",
          "description": "Draft database schema and document it",
          "position": 1
        }
      ]
    },
    {
      "id": 11,
      "boardId": 1,
      "title": "In Progress",
      "position": 1,
      "cards": [
        {
          "id": 102,
          "columnId": 11,
          "title": "Implement auth",
          "description": "Add login page and protected routes",
          "position": 0
        }
      ]
    },
    {
      "id": 12,
      "boardId": 1,
      "title": "Done",
      "position": 2,
      "cards": []
    }
  ]
}
```


## Rationale & Design Notes

### Why separate tables for columns and cards?
- It keeps the schema normalized and allows efficient queries (e.g., load all columns for a board, then load cards for those columns).
- It supports reordering by storing a `position` field instead of relying on an array index in JSON.

### Why `position` instead of `order_index`?
- `position` is a simple integer field that makes ordering explicit and easy to update when cards/columns move.

### Handling multiple users (future-proofing)
- The `users` table is included so the backend can later switch from hardcoded auth to real authentication.
- Boards are scoped to `user_id`, so each user can have their own board.

### Migrations
- Since we use SQLite for MVP, migrations can be handled via a simple versioned migration table or by using SQLAlchemy + Alembic if needed.
- For MVP, the app can create tables on startup if they do not exist (idempotent `CREATE TABLE IF NOT EXISTS ...`).

---

## Next Steps

- Implement the schema in the backend using SQLAlchemy models.
- Seed the DB with a default user (`username="user"`) and a default board with the standard 3 columns.
- Implement API routes to read/write this structure (Part 6).
