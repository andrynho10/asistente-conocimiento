"""
Audit Logging Service for tracking user actions and system events.

Provides asynchronous audit logging without blocking request processing.
AC#7: Audit Logging - Logs all AI queries for compliance and monitoring.

Usage:
    await audit_service.log_action(
        action="AI_QUERY",
        user_id=user.id,
        metadata={"query": "...", "response_time_ms": 1245.5}
    )
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Session

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for audit logging of user actions and system events.

    Logs are recorded asynchronously to prevent blocking request processing.
    """

    # Action types
    ACTION_AI_QUERY = "AI_QUERY"
    ACTION_DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    ACTION_DOCUMENT_DELETE = "DOCUMENT_DELETE"
    ACTION_LOGIN = "LOGIN"
    ACTION_LOGOUT = "LOGOUT"
    ACTION_PERMISSION_DENIED = "PERMISSION_DENIED"
    ACTION_ERROR = "ERROR"

    @staticmethod
    async def log_action(
        action: str,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> None:
        """
        Log an audit action asynchronously.

        AC#7: Audit Logging for compliance and monitoring.

        Args:
            action: Action type (e.g., "AI_QUERY", "DOCUMENT_UPLOAD")
            user_id: ID of user performing action
            metadata: Optional metadata dict (query, response_time_ms, etc)
            db: Optional database session for persistence

        Example:
            await audit_service.log_action(
                action="AI_QUERY",
                user_id=123,
                metadata={
                    "query_preview": "¿Cuál es...",
                    "response_time_ms": 1245.5,
                    "documents_retrieved": 3,
                    "status": "success"
                },
                db=session
            )
        """
        try:
            # Build audit log entry
            timestamp = datetime.utcnow()
            metadata = metadata or {}

            audit_entry = {
                "timestamp": timestamp.isoformat(),
                "action": action,
                "user_id": user_id,
                "metadata": metadata
            }

            # Log to application logger (structured logging)
            logger.info(
                json.dumps({
                    "event": "audit_log",
                    **audit_entry
                })
            )

            # Optionally persist to database if session provided
            if db:
                await AuditService._persist_to_db(
                    action=action,
                    user_id=user_id,
                    metadata=metadata,
                    timestamp=timestamp,
                    db=db
                )

        except Exception as e:
            # Log error but don't raise - audit failures shouldn't break requests
            logger.error(
                f"Audit logging failed for action '{action}' user_id={user_id}: {str(e)}"
            )

    @staticmethod
    async def _persist_to_db(
        action: str,
        user_id: int,
        metadata: Dict[str, Any],
        timestamp: datetime,
        db: Session
    ) -> None:
        """
        Persist audit log to database.

        Args:
            action: Action type
            user_id: User ID
            metadata: Metadata dict
            timestamp: Timestamp
            db: Database session
        """
        try:
            # Import model here to avoid circular imports
            from app.models.audit import AuditLog

            audit_log = AuditLog(
                action=action,
                user_id=user_id,
                metadata_json=json.dumps(metadata),
                created_at=timestamp
            )

            db.add(audit_log)
            db.commit()

            logger.debug(
                f"Audit log {action} for user {user_id} persisted to database"
            )

        except Exception as e:
            logger.error(f"Failed to persist audit log to database: {str(e)}")


# Convenience function for quick audit logging
async def log_ai_query(
    user_id: int,
    query_preview: str,
    response_time_ms: float,
    documents_retrieved: int,
    status: str = "success",
    error_message: Optional[str] = None,
    db: Optional[Session] = None
) -> None:
    """
    Log an AI query action.

    AC#7: Audit Logging - Logs all AI queries.

    Args:
        user_id: User ID
        query_preview: First 100 chars of query (for logging)
        response_time_ms: Total response time
        documents_retrieved: Number of documents returned
        status: "success" or "error"
        error_message: Optional error message
        db: Optional database session

    Example:
        await log_ai_query(
            user_id=user.id,
            query_preview="¿Cuál es la política de vacaciones?",
            response_time_ms=1245.5,
            documents_retrieved=3,
            db=session
        )
    """
    metadata = {
        "query_preview": query_preview[:100],
        "response_time_ms": response_time_ms,
        "documents_retrieved": documents_retrieved,
        "status": status
    }

    if error_message:
        metadata["error_message"] = error_message

    await AuditService.log_action(
        action=AuditService.ACTION_AI_QUERY,
        user_id=user_id,
        metadata=metadata,
        db=db
    )


async def log_document_upload(
    user_id: int,
    filename: str,
    file_size_bytes: int,
    status: str = "success",
    db: Optional[Session] = None
) -> None:
    """
    Log a document upload action.

    Args:
        user_id: User ID
        filename: Uploaded filename
        file_size_bytes: File size in bytes
        status: "success" or "error"
        db: Optional database session
    """
    await AuditService.log_action(
        action=AuditService.ACTION_DOCUMENT_UPLOAD,
        user_id=user_id,
        metadata={
            "filename": filename,
            "file_size_bytes": file_size_bytes,
            "status": status
        },
        db=db
    )


async def log_permission_denied(
    user_id: int,
    resource: str,
    reason: str,
    db: Optional[Session] = None
) -> None:
    """
    Log a permission denied event.

    Args:
        user_id: User ID
        resource: Resource being accessed
        reason: Reason for denial
        db: Optional database session
    """
    await AuditService.log_action(
        action=AuditService.ACTION_PERMISSION_DENIED,
        user_id=user_id,
        metadata={
            "resource": resource,
            "reason": reason
        },
        db=db
    )
