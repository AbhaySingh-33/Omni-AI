from fastapi import APIRouter
from pydantic import BaseModel
from app.auth import register_user, login_user, create_token

router = APIRouter()


class AuthRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/register")
def register(req: AuthRequest):
    user_id = register_user(req.email, req.password)
    token = create_token(user_id, req.email)
    return {"token": token, "email": req.email}


@router.post("/auth/login")
def login(req: AuthRequest):
    user_id = login_user(req.email, req.password)
    token = create_token(user_id, req.email)
    return {"token": token, "email": req.email}
