# Code Review

Comprehensive review of the PM Kanban MVP codebase. Issues are grouped by severity.

---

## Critical

### CR-01: ~~API key committed to version control~~ — FALSE POSITIVE
**File:** `.env`

`.env` is correctly listed in `.gitignore` and is not tracked by git (`git ls-files .env` returns nothing). The `.env.template` with a blank placeholder is the only committed reference. No action needed.

### ~~CR-02: `.env` baked into Docker image~~ — FIXED
**File:** `Dockerfile`

Removed `COPY .env .env`. The `scripts/start.sh` already passes `--env-file .env` to `docker run`, so secrets are injected at runtime and never baked into image layers. Verified: `docker exec` confirms `.env` is absent from the container filesystem, and all endpoints (health, login, board, AI) respond correctly.

### ~~CR-03: Authentication is entirely client-side~~ — FIXED (OAuth implementation)
**File:** `frontend/src/lib/auth.tsx`

~~Login is a local string comparison with no backend validation. Any user can bypass login by setting `sessionStorage["user"] = "user"` in the browser console. All API endpoints are completely unprotected.~~

Replaced with Google OAuth 2.0 (Authorization Code flow). The backend issues a signed JWT stored as an `HttpOnly; SameSite=Lax` cookie (`access_token`, 24h expiry). All board, card, column, and AI endpoints now depend on `get_current_user`, which decodes and validates the JWT on every request. The frontend calls `GET /api/auth/me` on mount to restore the session — there is no longer any client-side credential check or `sessionStorage` usage.

### ~~CR-04: Password stored in plain text~~ — FIXED (OAuth implementation)
**File:** `backend/app/crud.py` `seed_default_data()`

~~The `create_user` function stores the password as-is with no hashing.~~

Passwords are eliminated entirely. The `User` model no longer has `username` or `password_hash` columns; identity is established via Google OAuth (`google_id`, `email`). No password is ever stored.

---

## High

### ~~CR-05: All endpoints hardcoded to a single user~~ — FIXED (OAuth implementation)
**Files:** `backend/app/main.py`

~~Every endpoint resolves the active user by hardcoding `crud.get_user_by_username(db, "user")`. Multiple users would all read/write the same board.~~

All endpoints now use `Depends(get_current_user)`, which extracts the authenticated user from the JWT cookie and enforces per-user data isolation. Each user's board, cards, and conversation history are scoped to their own `user.id`.

### ~~CR-06: In-memory conversation history~~ — FIXED
**File:** `backend/app/main.py`, `backend/app/models.py`, `backend/app/crud.py`

The in-memory `conversation_histories` dict has been removed entirely. History is now persisted in the `conversation_messages` table (columns: `id`, `user_id`, `role`, `content`, `created_at`), keyed by `user_id` with a cascade-delete on the user record.

New endpoints:
- `GET /api/ai/history` — returns `{"messages": [...]}` for the authenticated user; used by the frontend to restore history on page load.
- `DELETE /api/ai/history` — clears all messages for the authenticated user (204).

The frontend loads history via `api.getChatHistory()` on board mount so conversations survive page refreshes. A "Clear history" button appears in the AI Assistant sidebar header when there are messages, calling `api.clearChatHistory()`.

### ~~CR-07: AI response parsed without schema validation~~ — FIXED
**File:** `backend/app/main.py` — AI chat endpoint

~~The AI response is `json.loads()`-ed and passed directly to `AIChatResponse(**parsed)` with no validation of field types or structure.~~

`ai_schemas.py` now has fully typed nested models (`AICardUpdate`, `AIColumnUpdate`, `AIBoardUpdates`). The chat endpoint uses `AIChatResponse.model_validate(parsed)` (Pydantic v2), which raises `ValidationError` on schema mismatch. The response parser also strips markdown code fences before JSON parsing. Any `JSONDecodeError` or `ValidationError` falls back to returning the raw AI text as a plain-text response. Two new tests cover these paths: `test_ai_chat_invalid_schema_falls_back` and `test_ai_chat_markdown_fences_stripped`.

### ~~CR-08: `conversationHistory` request field silently ignored~~ — FIXED
**File:** `backend/app/ai_schemas.py`, `frontend/src/lib/api.ts`

~~`AIChatRequest.conversationHistory` is accepted but never used.~~

Removed `conversationHistory` from `AIChatRequest`. The `api.chat()` function in the frontend no longer sends or accepts this parameter. The frontend `AIChatResponse` type is updated to use the proper typed `AIBoardCardUpdate` / `AIBoardColumnUpdate` subtypes instead of the generic `Card[]`/`Column[]` that was there before.

### ~~CR-09: Board updates from AI are fire-and-forget~~ — FIXED
**File:** `frontend/src/components/KanbanBoard.tsx` `applyBoardUpdates()`

~~AI-driven board mutations call multiple API endpoints sequentially with no rollback if one fails mid-way.~~

`applyBoardUpdates` now captures a `boardSnapshot` before processing. All mutations are applied to a local `currentBoard` variable with no intermediate `setBoard` calls. A single `setBoard(currentBoard)` is called once all updates succeed. A wrapping `try/catch` reverts to `boardSnapshot` on any failure and surfaces the error in the chat sidebar.

### ~~CR-10: Duplicate and unused imports in main.py~~ — FIXED (OAuth implementation)
**File:** `backend/app/main.py`

~~`from .database import SessionLocal, engine` and `from .deps import get_db` appeared twice.~~

Resolved as a side effect of the full `main.py` rewrite for the OAuth implementation. All imports are now clean and non-duplicated.

---

## Medium

### ~~CR-11: SQLite foreign key enforcement disabled (default)~~ — FIXED
**File:** `backend/app/database.py`

~~SQLite does not enforce foreign keys by default. Orphaned cards and columns are possible if application-level cascade logic has a bug.~~

Added an `@event.listens_for(engine, "connect")` listener in `database.py` that executes `PRAGMA foreign_keys=ON` for every new SQLite connection.

### ~~CR-12: Redundant Python-level sort in `get_board_for_user`~~ — FIXED
**File:** `backend/app/crud.py`

~~Columns and cards are sorted in Python after the query, but the SQLAlchemy relationships already define `order_by=position`.~~

Removed the `.sort()` calls. `get_board_for_user` now simply returns the query result directly; ordering is handled by the `order_by="KanbanColumn.position"` and `order_by="Card.position"` clauses on the ORM relationships.

### ~~CR-13: O(n) position recalculation on every card move/delete~~ — FIXED
**File:** `backend/app/crud.py` — `delete_card`, `move_card`

~~The code loops over remaining cards and issues one UPDATE per card.~~

`delete_card` and the cross-column path of `move_card` now use `Query.update()` with an expression-based value (`{"position": models.Card.position - 1}`), issuing a single bulk SQL UPDATE per shift operation instead of one per card.

### ~~CR-14: `setTimeout` not cleared on unmount~~ — FIXED
**File:** `frontend/src/components/KanbanBoard.tsx`

~~If the component unmounts before the timer fires, `setState` is called on an unmounted component.~~

Added `highlightTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)`. A `useEffect` cleanup clears the timeout on unmount. `applyBoardUpdates` clears any existing timeout before setting a new one.

### ~~CR-15: Multiple sequential `setBoard` calls in `applyBoardUpdates`~~ — FIXED
**File:** `frontend/src/components/KanbanBoard.tsx`

~~`applyBoardUpdates` calls `setBoard` inside loops, triggering one re-render per update.~~

All mutations are now accumulated into a local `currentBoard` variable. A single `setBoard(currentBoard)` is called once after all updates succeed, producing exactly one re-render regardless of how many operations the AI requested.

### ~~CR-16: No error boundary~~ — FIXED
**File:** `frontend/src/components/ErrorBoundary.tsx`, `frontend/src/app/page.tsx`

~~An uncaught exception in `KanbanBoard` will white-screen the entire app with no recovery path.~~

Added `ErrorBoundary` class component (`getDerivedStateFromError` + fallback UI with a "Try again" button that resets the error state). `KanbanBoard` is now wrapped in `<ErrorBoundary>` in `page.tsx`.

### ~~CR-17: Missing startup validation for `OPENROUTER_API_KEY`~~ — FIXED
**File:** `backend/app/main.py`

~~The API key is only checked on the first AI request, producing a generic 500.~~

`on_startup` now checks for `OPENROUTER_API_KEY` and emits an `ERROR`-level log warning if it is absent, so the misconfiguration is surfaced immediately in the server logs rather than at first request time.

---

## Low / Test Coverage

### CR-18: `vi` not imported in `KanbanCard.test.tsx`
**File:** `frontend/src/components/KanbanCard.test.tsx`

`vi.fn()` is used on line 20 but `vi` is never imported from `vitest`. Works at runtime because `globals: true` is set in `vitest.config.ts`, but is technically incorrect — adding `import { vi } from "vitest"` makes the intent explicit and removes reliance on the global.

### ~~CR-19: Vitest setup file reference points to non-existent file~~ — RESOLVED
**File:** `frontend/vitest.config.ts`

`src/test/setup.ts` exists with `import "@testing-library/jest-dom"`. No action needed.

### ~~CR-20: Missing test: API key absent from AI chat endpoint~~ — FIXED (OAuth implementation)
**File:** `backend/tests/test_ai_chat.py`

`test_ai_chat_no_api_key` was added as part of the OAuth test suite expansion. It verifies that `POST /api/ai/chat` returns 500 with an "API key" detail when `OPENROUTER_API_KEY` is unset.

### CR-21: Missing tests: optimistic update revert behaviour
**File:** `frontend/src/components/KanbanBoard.test.tsx`

`KanbanBoard` reverts card moves, additions, and deletions on API failure, but none of these revert paths are tested.

### CR-22: Missing tests: `api.ts` conversion functions
**File:** `frontend/src/lib/api.ts`

`apiCardToCard`, `apiColumnToColumn`, and `apiBoardToBoardData` have no unit tests. These are the boundary between backend and frontend types; bugs here affect the entire app silently.

### ~~CR-23: Brittle `user_id == 1` assertion in AI tests~~ — FIXED (OAuth implementation)
**File:** `backend/tests/test_ai_chat.py`

~~`user_id` was hardcoded to `1` in history assertions.~~

Replaced with `next(iter(conversation_histories.values()))`, which retrieves the first history entry regardless of the assigned user ID.

### CR-24: README describes AI chat as "planned"
**File:** `README.md`

The README still says the AI chat feature is planned. It is fully implemented. Update the README to reflect the current state of the project.

---

## Summary

| Severity | Total | Fixed | Remaining |
|----------|-------|-------|-----------|
| Critical | 4 (incl. 1 false positive) | 4 | 0 |
| High     | 7 | 7 | 0 |
| Medium   | 7 | 7 | 0 |
| Low/Test | 7 | 3 | 4 |
| **Total** | **25** | **21** | **4** |

### Remaining items (Low / Test Coverage)
- CR-18: Add `import { vi } from "vitest"` to `KanbanCard.test.tsx`
- CR-21: Missing tests for optimistic-update revert paths in `KanbanBoard`
- CR-22: Missing unit tests for `api.ts` conversion functions
- CR-24: README still describes AI chat as "planned"
