from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlmodel import Session, select
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.auth.models import LoginRequest, Token

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, login_data: LoginRequest) -> Token:
        statement = select(User).where(User.username == login_data.username)
        user = self.db.exec(statement).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Usuario o contraseña incorrectos"
                }
            )

        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Usuario o contraseña incorrectos"
                }
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "USER_INACTIVE",
                    "message": "Usuario inactivo"
                }
            )

        token_data = {
            "sub": str(user.id),
            "user_id": user.id,
            "role": user.role.value
        }

        access_token = create_access_token(data=token_data)

        return Token(
            token=access_token,
            user_id=user.id,
            role=user.role.value
        )