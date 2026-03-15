# Code Review Report

_Reviewed: 2026-03-15_

---

## CRITICAL

### 1. Horizontal Privilege Escalation — `backend/app/main.py:208-261`

`PATCH /api/cards/{card_id}`, `DELETE /api/cards/{card_id}`, `PUT /api/cards/{card_id}/move`, and `PATCH /api/columns/{column_id}` all require authentication but **never verify the resource belongs to the current user**. Any authenticated user can modify or delete another user's cards/columns by guessing numeric IDs.

**Fix:** Before any mutation, walk the `card → column → board → user_id` chain and raise `403` if it doesn't match `current_user.id`.

### 2. Missing Board Ownership Check on Card Creation — `backend/app/main.py:192-205`

`POST /api/boards/{board_id}/columns/{column_id}/cards` validates that the column belongs to the given board, but never checks that the board belongs to the current user. An attacker who knows another user's `board_id` and `column_id` can create cards there.

**Fix:** Add a check that the board's `user_id` matches `current_user.id` before creating the card.

---

## HIGH

### 3. Detailed Exceptions Leaked to Client — `backend/app/main.py:356, 389`

```python
raise HTTPException(status_code=500, detail=f"AI call failed: {str(e)}")
```

Raw exception messages (including OpenRouter errors) are returned to the client. Log the exception server-side and return a generic message instead.

### 4. No Rate Limiting on `/api/ai/chat`

No throttling on the AI endpoint means a single authenticated user can exhaust OpenRouter credits or degrade performance for all users.

**Fix:** Add rate limiting (e.g. `slowapi`) — 5 requests/minute per user is a reasonable starting point.

### 5. No Input Length Constraints — `backend/app/schemas.py`

`title: str` and `description: Optional[str]` have no `max_length`. Multi-MB payloads are accepted, risking DB bloat and potential DoS.

**Fix:**
```python
from pydantic import Field
title: str = Field(..., min_length=1, max_length=255)
description: Optional[str] = Field(None, max_length=2000)
```

### 6. Fallback JWT Secret Fails Silently in Production — `backend/app/auth.py:9-15`

If `JWT_SECRET` is unset in production, the app silently falls back to a hardcoded public string (`"test-secret-do-not-use-in-production"`), making all JWTs forgeable.

**Fix:** Raise `RuntimeError` at startup if `JWT_SECRET` is not set and `APP_ENV=production`.

---

## MEDIUM

### 7. No Rate Limiting on Other Endpoints

`/api/auth/dev-login` and card mutation endpoints are also unthrottled, enabling brute-force and database flooding.

### 8. Weak Temporary ID Generation — `frontend/src/lib/kanban.ts:166-170`

`Math.random()` provides ~24 bits of entropy for temporary card IDs. While these are replaced by server IDs, collisions are more likely than necessary.

**Fix:** Use `crypto.getRandomValues()` instead.

### 9. No Business Logic Validation on AI Board Updates — `backend/app/main.py:268-329`

AI-returned `boardUpdates` are applied after schema validation only. There are no checks that referenced column IDs belong to the current user's board.

### 10. Dev Login Accepts Malformed Emails — `backend/app/schemas.py`

`DevLoginRequest.email: str` accepts any string. Should use `EmailStr` from pydantic.

---

## LOW

| # | Issue | Location |
|---|-------|----------|
| 11 | Silent AI response parse failures with no logging | `backend/app/main.py:343-354` |
| 12 | Unnecessary int↔string ID conversion adds confusion | `frontend/src/lib/api.ts:78-91` |
| 13 | No logging of auth events (login/logout) | `backend/app/main.py:62-175` |
| 14 | Test fixtures write to real `frontend/out/` and are not cleaned up | `backend/tests/conftest.py:17-18` |
| 15 | Inconsistent HTTP status code style (raw ints vs `status.HTTP_*` constants) | `backend/app/main.py` scattered |
| 16 | No API versioning (`/api/v1/`) | all routes |
| 17 | No SQLite connection pool configuration | `backend/app/database.py:11-12` |

---

## Priority Fix Order

1. Add ownership checks to all card/column mutation endpoints _(Critical)_
2. Add board ownership check to card creation _(Critical)_
3. Add `max_length` constraints to all Pydantic schemas _(High)_
4. Fail loudly at startup if `JWT_SECRET` is missing in production _(High)_
5. Add rate limiting to `/api/ai/chat` _(High)_
6. Return generic error messages instead of raw exceptions _(High)_
