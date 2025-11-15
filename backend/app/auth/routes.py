from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from app.auth.models import LoginRequest, Token, SuccessResponse, ErrorResponse
from app.auth.service import AuthService
from app.middleware.auth import get_current_user
from app.database import get_session
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_session),
    request: Request = None
):
    ip_address = request.client.host if request else None
    auth_service = AuthService(db)
    return auth_service.authenticate_user(login_data, ip_address=ip_address)

@router.post("/logout", response_model=SuccessResponse)
async def logout(
    current_user: User = Depends(get_current_user)
):
    return SuccessResponse(message="Logout successful")