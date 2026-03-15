import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt

_ALGORITHM = "HS256"
_EXPIRY_HOURS = 24
# Fallback secret used in tests when JWT_SECRET is not set.
# Never use this value in production.
_FALLBACK_SECRET = "test-secret-do-not-use-in-production"


def _secret() -> str:
    return os.getenv("JWT_SECRET", _FALLBACK_SECRET)


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=_EXPIRY_HOURS),
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, _secret(), algorithms=[_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return int(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
