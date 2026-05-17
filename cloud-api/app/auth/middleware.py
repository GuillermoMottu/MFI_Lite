from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security
from auth.tokens import get_token_user

_security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(_security),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="No autenticado")
    user = get_token_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")
    return user


def require_role(*roles: str):
    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Rol insuficiente")
        return current_user
    return Depends(dependency)
