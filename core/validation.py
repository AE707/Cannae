"""Shared input-validation helpers."""

import re

from fastapi import HTTPException, status

# user_id must be 1-64 alphanumeric chars, hyphens, or underscores.
_USER_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def validate_user_id(user_id: str) -> str:
    """Raise 422 if *user_id* doesn't match the allowed pattern."""
    if not _USER_ID_RE.match(user_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="user_id must be 1\u201364 alphanumeric, hyphen, or underscore characters.",
        )
    return user_id
