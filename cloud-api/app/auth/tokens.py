import time
import uuid
from typing import Optional

from .users import User

_TOKENS: dict[str, dict] = {}


def create_token(user: User) -> str:
    token = str(uuid.uuid4())
    _TOKENS[token] = {
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
        "created_at": time.time(),
    }
    return token


def get_token_user(token: str) -> Optional[dict]:
    return _TOKENS.get(token)


def delete_token(token: str) -> None:
    _TOKENS.pop(token, None)


def clear_all_tokens() -> None:
    """Solo para tests."""
    _TOKENS.clear()
