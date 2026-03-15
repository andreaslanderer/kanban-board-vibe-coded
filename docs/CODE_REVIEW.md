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

### CR-07: AI response parsed without schema validation
**File:** `backend/app/main.py` — AI chat endpoint

The AI response is `json.loads()`-ed and passed directly to `AIChatResponse(**parsed)` with no validation of field types or structure. A malformed or adversarial AI response could cause unpredictable behaviour. Validate the parsed dict against the expected schema before using it.

### CR-08: `conversationHistory` request field silently ignored
**File:** `backend/app/ai_schemas.py`

`AIChatRequest.conversationHistory` is accepted but never used — the backend maintains its own history. This is a misleading API contract. Either remove the field or use it to let the client drive history.

### CR-09: Board updates from AI are fire-and-forget
**File:** `frontend/src/components/KanbanBoard.tsx` `applyBoardUpdates()`

AI-driven board mutations call multiple API endpoints sequentially with no rollback if one fails mid-way. A partial failure leaves the board in an inconsistent state. Wrap these in a transaction or revert to the pre-update snapshot on any failure.

### ~~CR-10: Duplicate and unused imports in main.py~~ — FIXED (OAuth implementation)
**File:** `backend/app/main.py`

~~`from .database import SessionLocal, engine` and `from .deps import get_db` appeared twice.~~

Resolved as a side effect of the full `main.py` rewrite for the OAuth implementation. All imports are now clean and non-duplicated.

---

## Medium

### CR-11: SQLite foreign key enforcement disabled (default)
**File:** `backend/app/database.py`

SQLite does not enforce foreign keys by default. Orphaned cards and columns are possible if application-level cascade logic has a bug. Enable it at connection time:

```python
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### CR-12: Redundant Python-level sort in `get_board_for_user`
**File:** `backend/app/crud.py`

Columns and cards are sorted in Python after the query, but the SQLAlchemy relationships already define `order_by=position`. The Python sort is redundant — remove it.

### CR-13: O(n) position recalculation on every card move/delete
**File:** `backend/app/crud.py` — `delete_card`, `move_card`

After removing or moving a card, the code loops over remaining cards and decrements their `position` by 1 in a Python loop, issuing one UPDATE per card. For large boards this is slow. Use a single bulk UPDATE:
```sql
UPDATE cards SET position = position - 1
WHERE column_id = :col AND position > :removed_pos
```

### CR-14: `setTimeout` not cleared on unmount
**File:** `frontend/src/components/KanbanBoard.tsx` — `applyBoardUpdates()`

```typescript
setTimeout(() => setHighlightedCardIds([]), 3000);
```
If the component unmounts before the timer fires, `setState` is called on an unmounted component. Store the timeout ID in a ref and clear it in a `useEffect` cleanup.

### CR-15: Multiple sequential `setBoard` calls in `applyBoardUpdates`
**File:** `frontend/src/components/KanbanBoard.tsx`

`applyBoardUpdates` calls `setBoard` inside loops, triggering one re-render per update. Accumulate all changes into a single state object and call `setBoard` once.

### CR-16: No error boundary
**File:** `frontend/src/app/page.tsx`

An uncaught exception in `KanbanBoard` will white-screen the entire app with no recovery path. Wrap the board in a React Error Boundary component.

### CR-17: Missing startup validation for `OPENROUTER_API_KEY`
**File:** `backend/app/main.py`

The API key is only checked on the first AI request, producing a generic 500. Validate required environment variables at startup and fail fast with a clear message.

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
| High     | 7 | 4 | 3 |
| Medium   | 7 | 0 | 7 |
| Low/Test | 7 | 3 | 4 |
| **Total** | **25** | **11** | **14** |

### Remaining actions (before production use)
1. Validate AI response structure before using it (CR-07)
2. Enable SQLite foreign key enforcement (CR-11)
3. Clear `setTimeout` on unmount in `KanbanBoard` (CR-14)
4. Add React Error Boundary around `KanbanBoard` (CR-16)
