import hashlib
from dataclasses import dataclass
from typing import Optional


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@dataclass
class User:
    username: str
    display_name: str
    role: str
    password_hash: str

    def verify_password(self, password: str) -> bool:
        return self.password_hash == _hash(password)


_USERS: dict[str, User] = {
    "carlos": User("carlos", "Carlos Mendoza", "pa", _hash("demo123")),
    "maria": User("maria", "María Torres", "supervisor", _hash("demo123")),
    "admin": User("admin", "Administrador", "admin", _hash("admin123")),
}


def get_user(username: str) -> Optional[User]:
    return _USERS.get(username)
