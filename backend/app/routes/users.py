"""
User Management Routes

FastAPI router for user management endpoints.
Provides endpoints for users to change password and admins to manage user accounts.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select

from app.database import get_session
from app.middleware.auth import get_current_user
from app.models import User, UserRole, AuditLog
from app.core.security import verify_password, get_password_hash
from app.utils.validators import validate_password

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)


# Request/Response models
class ChangePasswordRequest:
    """Request body for change password endpoint"""
    current_password: str
    new_password: str

    def __init__(self, current_password: str, new_password: str):
        self.current_password = current_password
        self.new_password = new_password


class ChangePasswordResponse:
    """Response for change password endpoint"""
    message: str

    def __init__(self, message: str = "Password changed successfully"):
        self.message = message


# Helper function to check admin role
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Check if current user has admin role"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INSUFFICIENT_PERMISSIONS",
                "message": "Only administrators can access this endpoint"
            }
        )
    return current_user


# POST /api/users/change-password - Change password for authenticated user
@router.post("/change-password", response_model=dict, status_code=status.HTTP_200_OK)
async def change_password(
    current_password: str,
    new_password: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """
    Change password for the authenticated user.

    Request body:
    {
        "current_password": "OldPass123!",
        "new_password": "NewPass123!"
    }

    Returns 200 with success message if password changed successfully.
    Returns 400 if validation fails.
    """
    try:
        # Verify current password
        if not verify_password(current_password, current_user.hashed_password):
            # Create audit log for failed password change attempt
            audit_log = AuditLog(
                user_id=current_user.id,
                action="PASSWORD_CHANGE_FAILED",
                resource_type="user",
                resource_id=current_user.id,
                details=json.dumps({
                    "reason": "Invalid current password"
                }),
                ip_address=request.client.host if request else None
            )
            db.add(audit_log)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_PASSWORD",
                    "message": "Current password is incorrect"
                }
            )

        # Validate new password
        is_valid, error_msg = validate_password(new_password, current_user.username)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "WEAK_PASSWORD",
                    "message": error_msg
                }
            )

        # Update password
        current_user.hashed_password = get_password_hash(new_password)
        current_user.updated_at = datetime.now(timezone.utc)

        db.add(current_user)
        db.commit()
        db.refresh(current_user)

        # Create audit log for successful password change
        audit_log = AuditLog(
            user_id=current_user.id,
            action="PASSWORD_CHANGED",
            resource_type="user",
            resource_id=current_user.id,
            details=json.dumps({}),
            ip_address=request.client.host if request else None
        )
        db.add(audit_log)
        db.commit()

        logger.info(json.dumps({
            "event": "user_password_changed",
            "user_id": current_user.id,
            "username": current_user.username
        }))

        return {
            "message": "Password changed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(json.dumps({
            "event": "user_change_password_error",
            "user_id": current_user.id,
            "error": str(e)
        }))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Error changing password"
            }
        )
