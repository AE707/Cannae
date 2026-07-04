"""JWT authentication helpers and FastAPI dependencies."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from jose import JWTError, jwt

from core.config import get_settings

_bearer_scheme = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"


def create_access_token(payload: dict) -> str:
    """Create a signed JWT from *payload*."""
    settings = get_settings()
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    """FastAPI dependency that enforces a valid Bearer JWT.

    Returns the decoded token payload (dict) on success.
    Raises 401 otherwise.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = _decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
