"""
Tests para Story 2.7: Eliminación de Documentos con Auditoría

Tests completos para validación de endpoint DELETE /api/knowledge/documents/{document_id}
cubriendo todos los criterios de aceptación (AC1-AC5).
"""

import pytest
import tempfile
import os
from sqlmodel import Session, select
from unittest.mock import patch, MagicMock

from app.models.user import User, UserRole
from app.models.document import Document, DocumentCategory
from app.models.audit import AuditLog, AuditAction, AuditResourceType
from app.services.document_service import DocumentService


@pytest.fixture
def sample_document(test_db_session, admin_user, test_category):
    """Fixture para documento de prueba"""
    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    temp_file.write(b"Contenido de prueba del documento")
    temp_file.close()

    document = Document(
        title="Documento de Prueba",
        description="Descripción del documento de prueba",
        category=test_category.name,
        file_type="txt",
        file_size_bytes=len(b"Contenido de prueba del documento"),
        file_path=temp_file.name,
        uploaded_by=admin_user.id,
        is_indexed=True,
        content_text="Contenido de prueba del documento"
    )
    test_db_session.add(document)
    test_db_session.commit()
    test_db_session.refresh(document)
    return document


class TestDocumentDeletion:
    """Tests para eliminación de documentos"""

    def test_ac1_successful_deletion_by_admin(self, test_client, test_db_session, admin_user, admin_token, sample_document):
        """
        AC1: Given autenticado como admin, When elimino documento existente,
        Then documento y archivo físico son eliminados, And se registra auditoría
        """
        document_id = sample_document.id
        file_path = sample_document.file_path

        # Verificar que el archivo existe antes de eliminación
        assert os.path.exists(file_path)

        # Verificar que el documento existe en DB
        doc_before = test_db_session.get(Document, document_id)
        assert doc_before is not None

        # Realizar DELETE request con token de admin
        response = test_client.delete(
            f"/api/knowledge/documents/{document_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Verificar respuesta exitosa
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == document_id
        assert data["deleted"] is True
        assert data["message"] == "Documento eliminado exitosamente"
        assert data["deleted_by"] == admin_user.username

        # Verificar que el documento fue eliminado de la DB
        doc_after = test_db_session.get(Document, document_id)
        assert doc_after is None

        # Verificar que el archivo físico fue eliminado
        assert not os.path.exists(file_path)

        # Verificar entrada de auditoría
        audit_entry = test_db_session.exec(
            select(AuditLog).where(
                AuditLog.user_id == admin_user.id,
                AuditLog.action == AuditAction.DOCUMENT_DELETED,
                AuditLog.resource_type == "document",
                AuditLog.resource_id == document_id
            )
        ).first()

        assert audit_entry is not None
        assert f"Documento {document_id} eliminado exitosamente" in audit_entry.details
        assert admin_user.username in audit_entry.details

    def test_ac2_forbidden_access_for_regular_user(self, test_client, test_db_session, normal_user, user_token, sample_document):
        """
        AC2: Given usuario regular, When intenta eliminar documento,
        Then recibo error 403, And no se realiza ninguna modificación
        """
        document_id = sample_document.id
        file_path = sample_document.file_path

        # Realizar DELETE request con token de usuario regular
        response = test_client.delete(
            f"/api/knowledge/documents/{document_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Verificar error 403 Forbidden
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "INSUFFICIENT_PERMISSIONS"
        assert "Permisos insuficientes" in data["detail"]["message"]

        # Verificar que el documento aún existe en DB
        doc_after = test_db_session.get(Document, document_id)
        assert doc_after is not None

        # Verificar que el archivo físico aún existe
        assert os.path.exists(file_path)

        # Verificar que no hay auditoría de eliminación
        audit_entry = test_db_session.exec(
            select(AuditLog).where(
                AuditLog.user_id == normal_user.id,
                AuditLog.action == AuditAction.DOCUMENT_DELETED,
                AuditLog.resource_id == document_id
            )
        ).first()

        assert audit_entry is None

    def test_ac3_document_not_found(self, test_client, test_db_session, admin_user, admin_token):
        """
        AC3: Given intento eliminar documento inexistente,
        When envío DELETE request, Then recibo error 404, And se registra intento en auditoría
        """
        non_existent_id = 99999

        # Realizar DELETE request con ID inexistente
        response = test_client.delete(
            f"/api/knowledge/documents/{non_existent_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Verificar error 404 Not Found
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"
        assert "El documento solicitado no existe" in data["detail"]["message"]

        # Verificar que se registró intento en auditoría
        audit_entry = test_db_session.exec(
            select(AuditLog).where(
                AuditLog.user_id == admin_user.id,
                AuditLog.action == AuditAction.DELETE_ATTEMPT,
                AuditLog.resource_type == "document",
                AuditLog.resource_id == non_existent_id
            )
        ).first()

        assert audit_entry is not None
        assert f"Intento de eliminación de documento inexistente: {non_existent_id}" in audit_entry.details

    def test_ac4_orphaned_file_handling(self, test_client, test_db_session, admin_user, admin_token, sample_document):
        """
        AC4: Given archivo físico eliminado manualmente (huérfano),
        When elimino documento de DB, Then operación se completa exitosamente, And se loggea warning
        """
        document_id = sample_document.id
        file_path = sample_document.file_path

        # Eliminar archivo físicamente (simular archivo huérfano)
        os.remove(file_path)
        assert not os.path.exists(file_path)

        # Realizar DELETE request
        response = test_client.delete(
            f"/api/knowledge/documents/{document_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Verificar respuesta exitosa (a pesar de archivo huérfano)
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True

        # Verificar que el registro fue eliminado de DB
        doc_after = test_db_session.get(Document, document_id)
        assert doc_after is None

        # Verificar auditoría de eliminación exitosa
        audit_entry = test_db_session.exec(
            select(AuditLog).where(
                AuditLog.user_id == admin_user.id,
                AuditLog.action == AuditAction.DOCUMENT_DELETED,
                AuditLog.resource_id == document_id
            )
        ).first()

        assert audit_entry is not None

    def test_ac5_full_text_index_removal(self, test_client, test_db_session, admin_user, admin_token, sample_document):
        """
        AC5: Given documento indexado, When se completa eliminación,
        Then entrada FTS es eliminada, And documento no aparece en búsqueda
        """
        document_id = sample_document.id

        # Verificar que existe en FTS (simulado)
        # En implementación real, esto verificaría tabla documents_fts

        # Realizar búsqueda antes de eliminación para que aparezca
        search_response = test_client.get(
            f"/api/knowledge/search?q=Contenido",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        search_results_before = search_response.json()

        # Verificar que el documento aparece en búsqueda
        # SearchResponse retorna "results" no "documents"
        found_before = any(
            result.get("document_id") == document_id
            for result in search_results_before.get("results", [])
        )
        assert found_before, f"El documento {document_id} debería aparecer en búsqueda antes de eliminación. Respuesta: {search_results_before}"

        # Realizar DELETE request
        response = test_client.delete(
            f"/api/knowledge/documents/{document_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Verificar respuesta exitosa
        assert response.status_code == 200

        # Verificar que el documento ya no aparece en búsqueda
        search_response_after = test_client.get(
            f"/api/knowledge/search?q=Contenido",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        search_results_after = search_response_after.json()

        found_after = any(
            result.get("document_id") == document_id
            for result in search_results_after.get("results", [])
        )
        assert not found_after, "El documento eliminado no debería aparecer en búsqueda"


class TestDocumentServiceDeletion:
    """Tests unitarios para DocumentService.delete_document()"""

    @pytest.mark.asyncio
    async def test_service_successful_deletion(self, test_db_session, admin_user, sample_document):
        """Test unitario de eliminación exitosa via DocumentService"""
        document_id = sample_document.id
        file_path = sample_document.file_path

        # Verificar precondiciones
        assert os.path.exists(file_path)
        doc_before = test_db_session.get(Document, document_id)
        assert doc_before is not None

        # Ejecutar método del servicio
        result = await DocumentService.delete_document(document_id, test_db_session, admin_user)

        # Verificar resultado
        assert result is True

        # Verificar postcondiciones
        doc_after = test_db_session.get(Document, document_id)
        assert doc_after is None
        assert not os.path.exists(file_path)

    @pytest.mark.asyncio
    async def test_service_document_not_found(self, test_db_session, admin_user):
        """Test unitario de documento no encontrado via DocumentService"""
        non_existent_id = 99999

        # Ejecutar método del servicio
        result = await DocumentService.delete_document(non_existent_id, test_db_session, admin_user)

        # Verificar resultado
        assert result is False

    @pytest.mark.asyncio
    async def test_service_orphaned_file_handling(self, test_db_session, admin_user, sample_document):
        """Test unitario de manejo de archivo huérfano"""
        document_id = sample_document.id
        file_path = sample_document.file_path

        # Eliminar archivo físicamente
        os.remove(file_path)
        assert not os.path.exists(file_path)

        # Ejecutar método del servicio
        result = await DocumentService.delete_document(document_id, test_db_session, admin_user)

        # Verificar que la operación se completa exitosamente
        assert result is True

        # Verificar que el registro de DB fue eliminado
        doc_after = test_db_session.get(Document, document_id)
        assert doc_after is None


class TestPathValidationSecurity:
    """Tests de seguridad para validación de paths"""

    def test_path_validation_prevents_traversal(self, test_client, admin_token):
        """
        Test de seguridad: previene directory traversal attacks
        """
        # Intentar acceso con path traversal
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM"
        ]

        for malicious_path in malicious_paths:
            response = test_client.delete(
                f"/api/knowledge/documents/{malicious_path}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            # Debería retornar 404 o 422, no 500
            assert response.status_code in [404, 422]


class TestErrorHandling:
    """Tests para manejo robusto de errores"""

    def test_unauthorized_access(self, test_client, sample_document):
        """Test para acceso sin autenticación"""
        document_id = sample_document.id

        # Intentar DELETE sin token
        response = test_client.delete(f"/api/knowledge/documents/{document_id}")

        # Verificar error 401 Unauthorized
        assert response.status_code == 401

    def test_invalid_document_id_format(self, test_client, admin_token):
        """Test para formato de ID inválido"""
        invalid_ids = [
            "abc",      # string no numerico -> 422 (validation error)
            "-1",       # numero negativo -> 404 (not found)
            "0",        # cero -> 404 (not found)
        ]

        for invalid_id in invalid_ids:
            response = test_client.delete(
                f"/api/knowledge/documents/{invalid_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            # Debería manejar gracefully (404 o 422)
            assert response.status_code in [404, 422], \
                f"Invalid ID '{invalid_id}' returned {response.status_code}, expected 404 or 422"

    @pytest.mark.asyncio
    async def test_database_rollback_on_error(self, test_db_session, admin_user, sample_document):
        """Test para graceful degradation cuando el archivo físico no se puede eliminar.

        El servicio está diseñado para eliminar el documento de la DB incluso si
        el archivo físico no se puede eliminar (ej: archivo huérfano). Esto evita
        que errores del filesystem bloqueen la limpieza de la DB.

        Behavior:
        - Error al eliminar archivo físico → loguea pero continúa
        - Documento se elimina de la DB
        - Retorna True (eliminación exitosa)
        """
        document_id = sample_document.id
        original_doc = test_db_session.get(Document, document_id)

        # Simular error en eliminación de archivo físico
        # El código debe continuar y eliminar el documento de la DB anyway
        with patch('os.remove', side_effect=Exception("Simulated file system error")):
            # Esto NO debería fallar - debe manejar gracefully
            result = await DocumentService.delete_document(document_id, test_db_session, admin_user)

            # Debe retornar True (documento fue eliminado de DB)
            assert result is True

        # Verificar que el documento fue eliminado de la DB (a pesar del error del archivo)
        doc_after = test_db_session.get(Document, document_id)
        assert doc_after is None, "Document should be deleted from DB even if physical file deletion fails"


if __name__ == "__main__":
    pytest.main([__file__])