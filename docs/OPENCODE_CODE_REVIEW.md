# Code Review: Project Management MVP

**Review Date:** March 15, 2026  
**Reviewer:** OpenCode Analysis

---

## Executive Summary

This is a well-structured MVP with a Next.js frontend and FastAPI backend. However, there are several security vulnerabilities that must be addressed before production deployment, particularly around authorization and the dev login endpoint.

---

## Critical Issues (Must Fix Before Production)

### 1. Missing Authorization Checks
**Severity:** Critical  
**Files:** `backend/app/main.py`

The board/card endpoints don't verify that the authenticated user owns the requested board:

```python
# Line 181-189 - No ownership check
@app.get("/api/boards", response_model=schemas.BoardOut)
def api_get_board(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    board = crud.get_board_for_user(db, current_user.id)
```

While `get_board_for_user` filters by `user_id`, endpoints like `api_update_card`, `api_delete_card`, and `api_move_card` don't verify the card belongs to the user's board before allowing modifications.

**Recommendation:** Add ownership verification in CRUD functions or endpoints:
- `crud.get_card()` should verify the card's column belongs to user's board
- Or add explicit `crud.verify_card_ownership(db, card_id, user_id)`

### 2. Dev Login Endpoint Exposed in Production
**Severity:** Critical  
**File:** `backend/app/main.py:153-174`

```python
@app.post("/api/auth/dev-login", response_model=schemas.UserOut)
def api_dev_login(...):
    """Development-only login bypass. Disabled when APP_ENV=production."""
    if os.getenv("APP_ENV") == "production":
        raise HTTPException(status_code=404)
```

This relies on an environment variable that could be misconfigured. The `/api/auth/dev-login` endpoint should be completely removed or excluded from the production build.

**Recommendation:** Remove the endpoint entirely for production, or use build-time exclusion.

### 3. JWT Fallback Secret
**Severity:** Critical  
**File:** `backend/app/auth.py:10-15`

```python
_FALLBACK_SECRET = "test-secret-do-not-use-in-production"

def _secret() -> str:
    return os.getenv("JWT_SECRET", _FALLBACK_SECRET)
```

If `JWT_SECRET` is not set, the app uses a well-known insecure secret.

**Recommendation:** Fail fast if `JWT_SECRET` is not set:
```python
def _secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is required")
    return secret
```

### 4. AI Prompt Injection
**Severity:** High  
**File:** `backend/app/main.py:288-333`

User input is directly concatenated into the AI prompt without sanitization:

```python
prompt = f"""
...
User message:
{payload.question}
"""
```

A malicious user could craft messages to manipulate the AI's behavior or extract information.

**Recommendation:** Sanitize user input before including in prompts, or use structured input validation.

---

## Security Issues

### 5. No Rate Limiting on AI Endpoints
**Severity:** Medium  
**File:** `backend/app/main.py:268-356`

The `/api/ai/chat` endpoint calls an external API (OpenRouter) with no rate limiting. This could lead to:
- Excessive API costs
- Service abuse

**Recommendation:** Add rate limiting using FastAPI-limiter or similar.

### 6. Cookie Security Settings
**Severity:** Medium  
**File:** `backend/app/main.py:78, 137, 173`

```python
redirect.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=86400)
```

Missing `secure=True` for production (should only be set when not on localhost).

**Recommendation:**
```python
is_prod = os.getenv("APP_ENV") == "production"
redirect.set_cookie(
    "access_token", token,
    httponly=True,
    samesite="lax",
    max_age=86400,
    secure=is_prod,  # Only enable in production
)
```

---

## Backend Issues

### 7. Database Session Management
**Severity:** Medium  
**File:** `backend/app/crud.py:145-190`

In `move_card`, there are multiple separate `db.commit()` calls:

```python
db.query(models.Card).filter(...).update(...)
db.commit()  # First commit

db.query(models.Card).filter(...).update(...)
db.commit()  # Second commit

card.column_id = target_column_id
card.position = target_position
db.commit()  # Third commit
```

If a later commit fails, earlier changes have already been persisted.

**Recommendation:** Use a single transaction:
```python
try:
    # All operations
    db.commit()
except:
    db.rollback()
    raise
```

### 8. Missing Input Validation
**Severity:** Medium  
**Files:** `backend/app/schemas.py`, `backend/app/main.py`

No length limits on `title` or `description` fields:

```python
class CardBase(BaseModel):
    title: str
    description: Optional[str] = None
```

**Recommendation:** Add validation:
```python
class CardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
```

### 9. OAuth State Not Validated Properly
**Severity:** Low  
**File:** `backend/app/main.py:82-91`

The OAuth state cookie is validated, but there's no expiry validation - it only checks if the state matches.

---

## Frontend Issues

### 10. Type Duplication
**Severity:** Low  
**Files:** `frontend/src/lib/api.ts`, `frontend/src/lib/kanban.ts`

The frontend has duplicated type definitions:
- `api.ts:59-74` defines `Card`, `Column`, `BoardData`
- `kanban.ts:1-16` defines the same types

**Recommendation:** Export types from one location and import in the other.

### 11. Inconsistent Field Names
**Severity:** Low  
**Files:** `frontend/src/lib/api.ts`, `frontend/src/lib/kanban.ts`

- API uses `description`
- Kanban utilities use `details`

This requires conversion functions (which exist at lines 78-103 in api.ts).

**Recommendation:** Standardize on one field name across the codebase.

### 12. Missing Loading State in Login
**Severity:** Low  
**File:** `frontend/src/components/Login.tsx`

The login button doesn't show a loading state while the OAuth redirect is happening.

### 13. Potential Race Condition in KanbanBoard
**Severity:** Low  
**File:** `frontend/src/components/KanbanBoard.tsx:224-329`

The `applyBoardUpdates` function processes AI updates sequentially. If multiple updates are received, and one fails, the rollback to `boardSnapshot` loses all intermediate successful updates.

---

## Code Quality

### 14. Dead Code
**Severity:** Low  
**File:** `frontend/src/lib/kanban.ts:18-72`

`initialData` with mock board data is never used - the app now fetches from API.

**Recommendation:** Remove or keep as fallback for offline mode.

### 15. Unused Imports
**Severity:** Low  
**Files:** Multiple

- `backend/app/main.py:1-4`: `json`, `logging`, `os`, `secrets` are used, but some may be removable after cleanup

### 16. Magic Numbers
**Severity:** Low  
**Files:** `frontend/src/components/KanbanBoard.tsx`

```python
highlightTimeoutRef.current = setTimeout(() => setHighlightedCardIds([]), 3000);
```

**Recommendation:** Extract to named constants.

---

## Positive Findings

1. **Good Architecture:** Clean separation of concerns (models, schemas, crud, deps)
2. **Proper Error Handling:** Most endpoints return appropriate HTTP status codes
3. **Optimistic Updates:** Frontend provides good UX with optimistic updates and rollback
4. **SQLite Foreign Keys:** Proper foreign key enforcement enabled (database.py:17-21)
5. **Type Safety:** Good use of TypeScript and Pydantic for type safety
6. **Loading States:** Proper loading and error states in UI components
7. **Accessible:** Good use of aria-labels and semantic HTML
8. **Tests:** Unit tests exist for key components

---

## Recommendations Summary

| Priority | Issue | Action |
|----------|-------|--------|
| P0 | Missing authorization checks | Add ownership verification to all board/card operations |
| P0 | Dev login in production | Remove or conditionally compile out dev-login endpoint |
| P0 | JWT fallback secret | Fail if JWT_SECRET not set |
| P1 | AI prompt injection | Sanitize user input in prompts |
| P1 | Cookie security | Add secure flag for production |
| P1 | Rate limiting | Add rate limiting to AI endpoints |
| P2 | Input validation | Add field length constraints |
| P2 | DB transactions | Consolidate multi-commit operations |
| P3 | Type deduplication | Remove duplicate type definitions |
| P3 | Dead code | Remove unused initialData |

---

## Testing Recommendations

1. Add integration tests for auth flow (OAuth + JWT)
2. Add authorization tests - verify users cannot access other users' boards
3. Add API endpoint tests for all CRUD operations
4. Add e2e tests for complete user flows
5. Test edge cases in AI chat (empty messages, very long messages, special characters)
