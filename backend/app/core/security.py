from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import get_settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(hours=settings.jwt_expiration_hours)

    to_encode.update({
        "exp": expire,
        "iat": now_utc,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt has a 72 byte limit, so we truncate passwords if needed
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    # bcrypt has a 72 byte limit, so we truncate passwords if needed
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def check_account_locked(user: User) -> bool:
    """
    Verifica si una cuenta está actualmente bloqueada.

    Si la cuenta está bloqueada pero el bloqueo ha expirado, resetea automáticamente
    los campos de bloqueo.

    Args:
        user: Objeto User a verificar

    Returns:
        bool: True si la cuenta está actualmente bloqueada, False en caso contrario
    """
    if user.locked_until is None:
        return False

    # Obtener timestamp actual - compatible con datetimes offset-naive y offset-aware
    now_utc = datetime.now(timezone.utc)
    locked_until = user.locked_until

    # Si locked_until es offset-naive, convertir now_utc a offset-naive para comparación
    if locked_until.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=None)

    if locked_until > now_utc:
        # Cuenta aún está bloqueada
        return True
    else:
        # Bloqueo ha expirado - resetear campos (nota: se debe guardar en BD después)
        user.locked_until = None
        user.failed_login_attempts = 0
        return False