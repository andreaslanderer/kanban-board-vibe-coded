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

### CR-03: Authentication is entirely client-side
**File:** `frontend/src/lib/auth.tsx`

Login is a local string comparison with no backend validation:
```typescript
if (username === "user" && password === "password") { ... }
```
The `/api/auth/login` endpoint exists but is never called by the frontend. There are no session tokens, JWTs, or cookies. Any user can bypass login by setting `sessionStorage["user"] = "user"` in the browser console. All API endpoints are completely unprotected.

### CR-04: Password stored in plain text
**File:** `backend/app/crud.py` `seed_default_data()`

```python
user = create_user(db, "user", "password")
```
The `create_user` function stores the password as-is with no hashing. Passwords must be hashed with bcrypt or similar before storage.

---

## High

### CR-05: All endpoints hardcoded to a single user
**Files:** `backend/app/main.py` (lines around `get_user_by_username(db, "user")`)

Every endpoint resolves the active user by hardcoding `"user"`:
```python
user = crud.get_user_by_username(db, "user")
```
The database schema supports multiple users, but no user is extracted from the request. Multiple users would all read/write the same board.

**Action:** Extract user identity from a session token or auth header and validate it on every request.

### CR-06: In-memory conversation history
**File:** `backend/app/main.py` line 16

```python
conversation_histories = {}
```
Conversation history is lost on restart, grows unbounded, and has no per-user isolation (though moot given CR-05). Store it in the database with a reasonable cap or TTL.

### CR-07: AI response parsed without schema validation
**File:** `backend/app/main.py` — AI chat endpoint

The AI response is `json.loads()`-ed and passed directly to `AIChatResponse(**parsed)` with no validation of field types or structure. A malformed or adversarial AI response could cause unpredictable behaviour. Validate the parsed dict against the expected schema before using it.

### CR-08: `conversationHistory` request field silently ignored
**File:** `backend/app/ai_schemas.py`

`AIChatRequest.conversationHistory` is accepted but never used — the backend maintains its own history. This is a misleading API contract. Either remove the field or use it to let the client drive history.

### CR-09: Board updates from AI are fire-and-forget
**File:** `frontend/src/components/KanbanBoard.tsx` `applyBoardUpdates()`

AI-driven board mutations call multiple API endpoints sequentially with no rollback if one fails mid-way. A partial failure leaves the board in an inconsistent state. Wrap these in a transaction or revert to the pre-update snapshot on any failure.

### CR-10: Duplicate and unused imports in main.py
**File:** `backend/app/main.py`

`from .database import SessionLocal, engine` and `from .deps import get_db` appear twice. `SessionLocal` and `engine` are only used in the startup event handler and could be imported there instead. Remove the duplicates.

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
**File:** `backend/app/crud.py` lines 25–28

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

`vi.fn()` is used on line 20 but `vi` is never imported from `vitest`. This would cause a `ReferenceError` at runtime if the test file ever exercised that path. Add `import { vi } from "vitest"`.

### CR-19: Vitest setup file reference points to non-existent file
**File:** `frontend/vitest.config.ts`

```typescript
setupFiles: ["./src/test/setup.ts"],
```
`src/test/setup.ts` does not exist. Either create it (even if empty) or remove the reference.

### CR-20: Missing test: API key absent from AI chat endpoint
**File:** `backend/tests/test_ai_chat.py`

`test_main.py` has `test_ai_test_no_api_key` for `/api/ai/test`, but the equivalent case is missing for `/api/ai/chat`.

### CR-21: Missing tests: optimistic update revert behaviour
**File:** `frontend/src/components/KanbanBoard.test.tsx`

`KanbanBoard` reverts card moves, additions, and deletions on API failure, but none of these revert paths are tested.

### CR-22: Missing tests: `api.ts` conversion functions
**File:** `frontend/src/lib/api.ts`

`apiCardToCard`, `apiColumnToColumn`, and `apiBoardToBoardData` have no unit tests. These are the boundary between backend and frontend types; bugs here affect the entire app silently.

### CR-23: Brittle `user_id == 1` assertion in AI tests
**File:** `backend/tests/test_ai_chat.py` lines 38, 72

```python
assert conversation_histories[user_id][-1]["role"] == "assistant"
```
`user_id` is hardcoded to `1`. This test will break if seeding order changes or tests run in isolation. Derive the user ID from the seeded data instead.

### CR-24: README describes AI chat as "planned"
**File:** `README.md`

The README still says the AI chat feature is planned. It is fully implemented. Update the README to reflect the current state of the project.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 3 |
| High     | 7 |
| Medium   | 7 |
| Low/Test | 7 |
| **Total** | **24** |

### Recommended immediate actions (before any production use)
1. Remove `.env` from the Docker build (CR-02)
3. Implement real authentication with tokens and hashed passwords (CR-03, CR-04)
4. Add `vi` import to `KanbanCard.test.tsx` so tests are correct (CR-18)
5. Create or remove `src/test/setup.ts` (CR-19)
