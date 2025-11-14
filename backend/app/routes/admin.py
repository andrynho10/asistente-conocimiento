"""
Admin Routes for Generated Content Management

FastAPI router for admin dashboard functionality.
Provides endpoints to view, filter, validate, delete, and export AI-generated content.
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from io import BytesIO, StringIO
import csv

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlmodel import Session, select, func, or_, and_
from sqlalchemy import desc, asc
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from app.database import get_session
from app.middleware.auth import get_current_user
from app.models import (
    User,
    GeneratedContent,
    Document,
    UserRole,
    AuditLog,
    LearningPathProgress
)
from app.models.generated_content import ContentType, GeneratedContentRead
from app.models.quiz import QuizAttempt
from app.schemas.admin import GeneratedContentValidateRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"]
)

# Response models for admin endpoints


class GeneratedContentResponse(GeneratedContentRead):
    """Extended response with document and user info"""
    document_name: Optional[str] = None
    user_username: Optional[str] = None


class GeneratedContentListResponse:
    """Paginated list response"""
    total: int
    items: list[GeneratedContentResponse]
    limit: int
    offset: int


# Helper function to check admin role
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Check if current user has admin role"""
    if current_user.role.value != UserRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INSUFFICIENT_PERMISSIONS",
                "message": "Solo administradores pueden acceder a este endpoint"
            }
        )
    return current_user


# GET /api/admin/generated-content - List with filters
@router.get("/generated-content", response_model=dict)
async def list_generated_content(
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin),
    type: Optional[str] = Query(None, description="Filter by content type: summary, quiz, learning_path"),
    document_id: Optional[int] = Query(None, description="Filter by document ID"),
    user_id: Optional[int] = Query(None, description="Filter by creator user ID"),
    date_from: Optional[datetime] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO format)"),
    search: Optional[str] = Query(None, description="Search in ID, document name, user username"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("created_at", description="Sort field: id, created_at, content_type"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """
    List all generated content with advanced filtering, sorting, and pagination.

    Only accessible to admin users.
    """
    try:
        # Build query with joins
        query = (
            select(
                GeneratedContent.id,
                GeneratedContent.document_id,
                GeneratedContent.user_id,
                GeneratedContent.content_type,
                GeneratedContent.created_at,
                GeneratedContent.is_validated,
                GeneratedContent.validated_by,
                GeneratedContent.validated_at,
                Document.filename.label("document_name"),
                User.username.label("user_username")
            )
            .join(Document, GeneratedContent.document_id == Document.id, isouter=True)
            .join(User, GeneratedContent.user_id == User.id, isouter=True)
            .where(GeneratedContent.deleted_at.is_(None))  # Exclude soft-deleted
        )

        # Apply filters
        if type:
            try:
                content_type = ContentType(type.lower())
                query = query.where(GeneratedContent.content_type == content_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_TYPE", "message": f"Invalid content type: {type}"}
                )

        if document_id:
            query = query.where(GeneratedContent.document_id == document_id)

        if user_id:
            query = query.where(GeneratedContent.user_id == user_id)

        if date_from:
            # Ensure date_from is naive datetime in UTC
            if date_from.tzinfo is not None:
                date_from = date_from.replace(tzinfo=None)
            query = query.where(GeneratedContent.created_at >= date_from)

        if date_to:
            # Ensure date_to is naive datetime in UTC
            if date_to.tzinfo is not None:
                date_to = date_to.replace(tzinfo=None)
            query = query.where(GeneratedContent.created_at <= date_to)

        # Search filter (ID, document name, username)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    GeneratedContent.id.like(search_term),
                    Document.filename.like(search_term),
                    User.username.like(search_term)
                )
            )

        # Apply sorting
        sort_column = {
            "id": GeneratedContent.id,
            "created_at": GeneratedContent.created_at,
            "content_type": GeneratedContent.content_type
        }.get(sort_by, GeneratedContent.created_at)

        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Get total count before pagination
        count_query = select(func.count()).select_from(GeneratedContent).where(GeneratedContent.deleted_at.is_(None))

        # Apply same filters to count query
        if type:
            count_query = count_query.where(GeneratedContent.content_type == ContentType(type.lower()))
        if document_id:
            count_query = count_query.where(GeneratedContent.document_id == document_id)
        if user_id:
            count_query = count_query.where(GeneratedContent.user_id == user_id)
        if date_from:
            count_query = count_query.where(GeneratedContent.created_at >= date_from)
        if date_to:
            count_query = count_query.where(GeneratedContent.created_at <= date_to)
        if search:
            count_query = count_query.where(
                or_(
                    GeneratedContent.id.like(f"%{search}%"),
                    Document.filename.like(f"%{search}%"),
                    User.username.like(f"%{search}%")
                )
            )

        total = db.exec(count_query).one()

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute query
        results = db.exec(query).all()

        # Format response
        items = [
            {
                "id": row[0],
                "document_id": row[1],
                "user_id": row[2],
                "content_type": row[3].value if row[3] else None,
                "created_at": row[4].isoformat() if row[4] else None,
                "is_validated": row[5],
                "validated_by": row[6],
                "validated_at": row[7].isoformat() if row[7] else None,
                "document_name": row[8],
                "user_username": row[9]
            }
            for row in results
        ]

        logger.info(json.dumps({
            "event": "admin_list_generated_content",
            "total": total,
            "returned": len(items),
            "filters_applied": {
                "type": type,
                "document_id": document_id,
                "user_id": user_id,
                "has_date_range": date_from is not None or date_to is not None,
                "has_search": search is not None
            },
            "admin_id": admin_user.id
        }))

        return {
            "total": total,
            "items": items,
            "limit": limit,
            "offset": offset
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(json.dumps({
            "event": "admin_list_generated_content_error",
            "error": str(e),
            "admin_id": admin_user.id
        }))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Error listing generated content"}
        )


# PUT /api/admin/generated-content/{content_id}/validate
@router.put("/generated-content/{content_id}/validate", response_model=dict)
async def validate_content(
    content_id: int,
    payload: GeneratedContentValidateRequest,
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin),
    request: Request = None
):
    """
    Mark generated content as validated or unvalidated by admin.

    Body: {"is_validated": true/false}
    """
    try:
        is_validated = payload.is_validated

        # Get content
        statement = select(GeneratedContent).where(GeneratedContent.id == content_id)
        content = db.exec(statement).first()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "Content not found"}
            )

        # Update validation fields
        content.is_validated = is_validated
        content.validated_by = admin_user.id if is_validated else None
        content.validated_at = datetime.now(timezone.utc) if is_validated else None

        db.add(content)
        db.commit()
        db.refresh(content)

        # Create audit log
        audit_log = AuditLog(
            user_id=admin_user.id,
            action="VALIDATE_CONTENT",
            resource_type="generated_content",
            resource_id=content_id,
            details=json.dumps({
                "is_validated": is_validated,
                "content_type": content.content_type.value if content.content_type else None
            }),
            ip_address=request.client.host if request else None
        )
        db.add(audit_log)
        db.commit()

        logger.info(json.dumps({
            "event": "admin_validate_content",
            "content_id": content_id,
            "is_validated": is_validated,
            "admin_id": admin_user.id
        }))

        return {
            "id": content.id,
            "is_validated": content.is_validated,
            "validated_at": content.validated_at.isoformat() if content.validated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(json.dumps({
            "event": "admin_validate_content_error",
            "content_id": content_id,
            "error": str(e),
            "admin_id": admin_user.id
        }))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Error validating content"}
        )


# DELETE /api/admin/generated-content/{content_id}
@router.delete("/generated-content/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin),
    request: Request = None
):
    """
    Soft delete generated content (mark as deleted, don't physically remove).
    """
    try:
        # Get content
        statement = select(GeneratedContent).where(GeneratedContent.id == content_id)
        content = db.exec(statement).first()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "Content not found"}
            )

        # Soft delete
        content.deleted_at = datetime.now(timezone.utc)
        db.add(content)
        db.commit()

        # Create audit log
        audit_log = AuditLog(
            user_id=admin_user.id,
            action="DELETE_CONTENT",
            resource_type="generated_content",
            resource_id=content_id,
            details=json.dumps({
                "content_type": content.content_type.value if content.content_type else None,
                "document_id": content.document_id
            }),
            ip_address=request.client.host if request else None
        )
        db.add(audit_log)
        db.commit()

        logger.info(json.dumps({
            "event": "admin_delete_content",
            "content_id": content_id,
            "admin_id": admin_user.id
        }))

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(json.dumps({
            "event": "admin_delete_content_error",
            "content_id": content_id,
            "error": str(e),
            "admin_id": admin_user.id
        }))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Error deleting content"}
        )


# GET /api/admin/quiz/{quiz_id}/stats
@router.get("/quiz/{quiz_id}/stats", response_model=dict)
async def get_quiz_stats(
    quiz_id: int,
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin)
):
    """
    Get statistics for a specific quiz.
    Returns: total attempts, average score, pass rate (>=70%), most difficult question.
    """
    try:
        # Check if quiz exists
        statement = select(GeneratedContent).where(
            and_(
                GeneratedContent.id == quiz_id,
                GeneratedContent.content_type == ContentType.QUIZ
            )
        )
        quiz = db.exec(statement).first()

        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "Quiz not found"}
            )

        # Get quiz attempts stats
        attempts_query = select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id)
        attempts = db.exec(attempts_query).all()

        if not attempts:
            return {
                "quiz_id": quiz_id,
                "total_attempts": 0,
                "avg_score_percentage": 0,
                "pass_rate": 0,
                "most_difficult_question": None
            }

        total_attempts = len(attempts)
        scores = [att.score for att in attempts if att.score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        pass_count = sum(1 for s in scores if s >= 70)
        pass_rate = pass_count / total_attempts if total_attempts > 0 else 0

        logger.info(json.dumps({
            "event": "admin_get_quiz_stats",
            "quiz_id": quiz_id,
            "total_attempts": total_attempts,
            "admin_id": admin_user.id
        }))

        return {
            "quiz_id": quiz_id,
            "total_attempts": total_attempts,
            "avg_score_percentage": round(avg_score, 2),
            "pass_rate": round(pass_rate, 2),
            "most_difficult_question": None  # Can be extended
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(json.dumps({
            "event": "admin_get_quiz_stats_error",
            "quiz_id": quiz_id,
            "error": str(e),
            "admin_id": admin_user.id
        }))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Error getting quiz statistics"}
        )


# GET /api/admin/learning-path/{path_id}/stats
@router.get("/learning-path/{path_id}/stats", response_model=dict)
async def get_learning_path_stats(
    path_id: int,
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin)
):
    """
    Get statistics for a specific learning path.
    Returns: total views, completed count, completion rate, most skipped step.
    """
    try:
        # Check if learning path exists
        statement = select(GeneratedContent).where(
            and_(
                GeneratedContent.id == path_id,
                GeneratedContent.content_type == ContentType.LEARNING_PATH
            )
        )
        path = db.exec(statement).first()

        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "Learning path not found"}
            )

        # Get learning path progress stats
        progress_query = select(LearningPathProgress).where(
            LearningPathProgress.path_id == path_id
        )
        progress_records = db.exec(progress_query).all()

        if not progress_records:
            # No progress data yet
            logger.info(json.dumps({
                "event": "admin_get_learning_path_stats",
                "path_id": path_id,
                "total_views": 0,
                "admin_id": admin_user.id
            }))

            return {
                "path_id": path_id,
                "total_views": 0,
                "completed_count": 0,
                "completion_rate": 0.0,
                "most_skipped_step": None
            }

        # Calculate stats from progress records
        total_views = len(progress_records)
        completed_count = sum(
            1 for p in progress_records
            if p.completed_steps > 0 and p.last_step > 0
        )
        completion_rate = (completed_count / total_views * 100) if total_views > 0 else 0.0

        # Most skipped step: find the last_step with lowest value (most users stopped here)
        # This is a simplification; in reality, would need more detailed step tracking
        most_skipped_step = None
        if progress_records:
            last_steps = [p.last_step for p in progress_records if p.last_step > 0]
            if last_steps:
                # Find the step number where most users got stuck (lowest max step reached)
                step_counts = {}
                for step in last_steps:
                    step_counts[step] = step_counts.get(step, 0) + 1
                most_common_last_step = min(step_counts.keys())
                if most_common_last_step < max(last_steps):
                    most_skipped_step = most_common_last_step + 1

        logger.info(json.dumps({
            "event": "admin_get_learning_path_stats",
            "path_id": path_id,
            "total_views": total_views,
            "completed_count": completed_count,
            "admin_id": admin_user.id
        }))

        return {
            "path_id": path_id,
            "total_views": total_views,
            "completed_count": completed_count,
            "completion_rate": round(completion_rate, 2),
            "most_skipped_step": most_skipped_step
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(json.dumps({
            "event": "admin_get_learning_path_stats_error",
            "path_id": path_id,
            "error": str(e),
            "admin_id": admin_user.id
        }))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Error getting learning path statistics"}
        )


# GET /api/admin/generated-content/export
@router.get("/generated-content/export")
async def export_content(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    type: Optional[str] = Query(None),
    document_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin)
):
    """
    Export generated content as CSV or PDF.
    """
    from fastapi.responses import StreamingResponse

    try:
        # Build query
        query = select(
            GeneratedContent.id,
            GeneratedContent.content_type,
            Document.filename,
            User.username,
            GeneratedContent.created_at
        ).join(
            Document, GeneratedContent.document_id == Document.id, isouter=True
        ).join(
            User, GeneratedContent.user_id == User.id, isouter=True
        ).where(
            GeneratedContent.deleted_at.is_(None)
        )

        # Apply filters
        if type:
            query = query.where(GeneratedContent.content_type == ContentType(type.lower()))
        if document_id:
            query = query.where(GeneratedContent.document_id == document_id)
        if user_id:
            query = query.where(GeneratedContent.user_id == user_id)

        results = db.exec(query).all()

        if format == "csv":
            # Generate CSV
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Type", "Document", "User", "Created At"])

            for row in results:
                writer.writerow([
                    row[0],
                    row[1].value if row[1] else "",
                    row[2] or "",
                    row[3] or "",
                    row[4].isoformat() if row[4] else ""
                ])

            logger.info(json.dumps({
                "event": "admin_export_content",
                "format": "csv",
                "rows": len(results),
                "admin_id": admin_user.id
            }))

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=generated_content_{datetime.now().strftime('%Y%m%d')}.csv"}
            )

        else:  # PDF
            # Generate PDF using reportlab
            output = BytesIO()
            doc = SimpleDocTemplate(
                output,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )

            # Create PDF content
            elements = []

            # Title
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=12
            )
            elements.append(Paragraph("Reporte de Contenido Generado por IA", title_style))
            elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))

            # Table data
            table_data = [["ID", "Tipo", "Documento", "Usuario", "Fecha"]]

            for row in results:
                table_data.append([
                    str(row[0]),
                    row[1].value if row[1] else "N/A",
                    row[2] or "N/A",
                    row[3] or "N/A",
                    row[4].strftime('%d/%m/%Y %H:%M') if row[4] else "N/A"
                ])

            # Create table
            table = Table(table_data, colWidths=[0.7*inch, 1*inch, 1.5*inch, 1*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
            ]))

            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph(f"Total registros: {len(results)}", styles['Normal']))

            # Build PDF
            doc.build(elements)
            output.seek(0)

            logger.info(json.dumps({
                "event": "admin_export_content",
                "format": "pdf",
                "rows": len(results),
                "admin_id": admin_user.id
            }))

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=generated_content_{datetime.now().strftime('%Y%m%d')}.pdf"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(json.dumps({
            "event": "admin_export_content_error",
            "error": str(e),
            "admin_id": admin_user.id
        }))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Error exporting content"}
        )
