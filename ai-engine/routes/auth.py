from fastapi import APIRouter, Response
from pydantic import BaseModel
from app.auth import register_user, login_user, create_token

router = APIRouter()

AUTH_COOKIE_NAME = "omni_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7


class AuthRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/register")
def register(req: AuthRequest, response: Response):
    user_id = register_user(req.email, req.password)
    token = create_token(user_id, req.email)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return {"token": token, "email": req.email}


@router.post("/auth/login")
def login(req: AuthRequest, response: Response):
    user_id = login_user(req.email, req.password)
    token = create_token(user_id, req.email)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return {"token": token, "email": req.email}


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    return {"status": "ok"}
