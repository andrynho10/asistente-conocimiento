import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlmodel import Session, select
from app.models.user import User
from app.models.audit import AuditLog, AuditAction, AuditResourceType
from app.core.security import verify_password, create_access_token, check_account_locked
from app.core.config import get_settings
from app.auth.models import LoginRequest, Token

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, login_data: LoginRequest, ip_address: Optional[str] = None) -> Token:
        """
        Autentica un usuario verificando credenciales y manejo de bloqueo de cuenta.

        Flujo:
        1. Buscar usuario por username
        2. Si no existe, responder 401 sin revelar si usuario existe
        3. Verificar si cuenta está bloqueada
        4. Validar credenciales
        5. Si credenciales inválidas, incrementar failed_login_attempts
        6. Si se alcanza máximo, bloquear cuenta por ACCOUNT_LOCKOUT_MINUTES
        7. Si credenciales válidas, resetear intentos y generar token
        """
        settings = get_settings()

        # AC1: Buscar usuario por username
        statement = select(User).where(User.username == login_data.username)
        user = self.db.exec(statement).first()

        if not user:
            # No revelar si usuario existe (seguridad contra enumeración)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Usuario o contraseña incorrectos"
                }
            )

        # AC3: Verificar si cuenta está bloqueada ANTES de validar credenciales
        # Esto previene timing attacks
        is_locked = check_account_locked(user)

        if is_locked:
            # Cuenta está bloqueada - responder 403 sin validar password
            now_utc = datetime.now(timezone.utc)
            # Compatibilidad con datetimes offset-naive de SQLite
            if user.locked_until.tzinfo is None:
                now_utc = now_utc.replace(tzinfo=None)
            remaining_time = (user.locked_until - now_utc).total_seconds() / 60

            # Auditoría: intento en cuenta bloqueada
            audit_log = AuditLog(
                user_id=user.id,
                action="LOGIN_ATTEMPT_BLOCKED",
                resource_type=AuditResourceType.USER,
                resource_id=user.id,
                details=json.dumps({
                    "reason": "Account locked",
                    "remaining_minutes": round(remaining_time, 2)
                }),
                ip_address=ip_address
            )
            self.db.add(audit_log)
            self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ACCOUNT_LOCKED",
                    "message": f"Cuenta bloqueada por múltiples intentos fallidos. Intenta en {int(remaining_time + 1)} minutos.",
                    "locked_until": user.locked_until.isoformat()
                }
            )

        # AC2: Verificar si usuario está activo
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "USER_INACTIVE",
                    "message": "Usuario inactivo"
                }
            )

        # AC1: Validar credenciales
        password_valid = verify_password(login_data.password, user.hashed_password)

        if not password_valid:
            # Credenciales inválidas: incrementar failed_login_attempts
            user.failed_login_attempts += 1

            # Determinar si se alcanzó el máximo de intentos
            if user.failed_login_attempts >= settings.max_failed_login_attempts:
                # AC1 + AC3: Bloquear cuenta por ACCOUNT_LOCKOUT_MINUTES
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.account_lockout_minutes)
                self.db.add(user)
                self.db.commit()

                # Auditoría: ACCOUNT_LOCKED
                audit_log = AuditLog(
                    user_id=user.id,
                    action="ACCOUNT_LOCKED",
                    resource_type=AuditResourceType.USER,
                    resource_id=user.id,
                    details=json.dumps({
                        "reason": "Max failed attempts exceeded",
                        "failed_attempts": user.failed_login_attempts,
                        "lockout_minutes": settings.account_lockout_minutes
                    }),
                    ip_address=ip_address
                )
                self.db.add(audit_log)
                self.db.commit()

                # Responder 403 - cuenta bloqueada
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "ACCOUNT_LOCKED",
                        "message": f"Cuenta bloqueada por múltiples intentos fallidos. Intenta en {settings.account_lockout_minutes} minutos.",
                        "locked_until": user.locked_until.isoformat()
                    }
                )
            else:
                # AC1: Intentos fallidos < MAX: responder 401 con remaining_attempts
                self.db.add(user)
                self.db.commit()

                remaining_attempts = settings.max_failed_login_attempts - user.failed_login_attempts

                # Auditoría: LOGIN_FAILED
                audit_log = AuditLog(
                    user_id=user.id,
                    action="LOGIN_FAILED",
                    resource_type=AuditResourceType.USER,
                    resource_id=user.id,
                    details=json.dumps({
                        "reason": "Invalid password",
                        "failed_attempts": user.failed_login_attempts,
                        "remaining_attempts": remaining_attempts
                    }),
                    ip_address=ip_address
                )
                self.db.add(audit_log)
                self.db.commit()

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "INVALID_CREDENTIALS",
                        "message": "Usuario o contraseña incorrectos",
                        "remaining_attempts": remaining_attempts
                    }
                )

        # AC2: Credenciales correctas
        # Resetear failed_login_attempts y actualizar last_login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Auditoría: LOGIN_SUCCESS
        audit_log = AuditLog(
            user_id=user.id,
            action="LOGIN",
            resource_type=AuditResourceType.USER,
            resource_id=user.id,
            details=json.dumps({
                "success": True
            }),
            ip_address=ip_address
        )
        self.db.add(audit_log)
        self.db.commit()

        # Generar token JWT
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