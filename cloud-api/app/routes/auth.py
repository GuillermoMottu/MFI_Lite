from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from auth.middleware import get_current_user
from auth.tokens import create_token, delete_token
from auth.users import get_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])
_security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(request: LoginRequest):
    user = get_user(request.username)
    if not user or not user.verify_password(request.password):
        raise HTTPException(
            status_code=401,
            detail="Credenciales invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_token(user)
    return {
        "token": token,
        "user": {
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
        },
    }


@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Security(_security)):
    if credentials:
        delete_token(credentials.credentials)
    return {"status": "logged_out"}


@router.get("/me")
def me(current_user: dict = Security(get_current_user)):
    return {"user": current_user}
