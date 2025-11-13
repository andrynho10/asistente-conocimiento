"""
Tests unitarios para DocumentService - enfocados en la lógica de negocio.
Tests que no dependen de la infraestructura HTTP y evitan problemas de encoding.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from sqlmodel import Session

from app.services.document_service import DocumentService
from app.models.document import Document


class TestDocumentServiceDownload:
    """Tests unitarios para el método download_document"""

    @pytest.mark.asyncio
    async def test_download_success_pdf(self):
        """AC1: Descarga exitosa de PDF"""
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b"PDF test content for download")
            tmp_path = tmp.name

        try:
            # Mock documento
            doc = Document(
                id=1,
                title="Políticas de RRHH",
                file_type="pdf",
                file_size_bytes=25,
                file_path=tmp_path
            )

            # Mock DB session
            mock_db = Mock(spec=Session)
            mock_query = Mock()
            mock_query.first.return_value = doc
            mock_db.exec.return_value = mock_query

            # Test
            result = await DocumentService.download_document(1, mock_db)

            # Assertions
            assert result is not None
            file_path, file_type, safe_filename, file_size = result

            assert file_path == tmp_path
            assert file_type == "pdf"
            assert safe_filename == "Políticas_de_RRHH.pdf"
            assert file_size == 25

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_download_success_txt(self):
        """AC1: Descarga exitosa de TXT"""
        content = "Contenido de texto para pruebas de descarga."

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w', encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Mock documento
            doc = Document(
                id=2,
                title="Manual de Empleado",
                file_type="txt",
                file_size_bytes=len(content.encode('utf-8')),
                file_path=tmp_path
            )

            # Mock DB session
            mock_db = Mock(spec=Session)
            mock_query = Mock()
            mock_query.first.return_value = doc
            mock_db.exec.return_value = mock_query

            # Test
            result = await DocumentService.download_document(2, mock_db)

            # Assertions
            assert result is not None
            file_path, file_type, safe_filename, file_size = result

            assert file_path == tmp_path
            assert file_type == "txt"
            assert safe_filename == "Manual_de_Empleado.txt"
            assert file_size == len(content.encode('utf-8'))

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_download_document_not_found(self):
        """AC2: Documento no existe retorna None"""
        # Mock DB session returning None
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db.exec.return_value = mock_query

        # Test
        result = await DocumentService.download_document(999, mock_db)

        # Assertions
        assert result is None

    @pytest.mark.asyncio
    async def test_download_orphaned_file_cleanup(self):
        """AC3: Archivo huérfano elimina registro y retorna None"""
        # Mock documento con archivo inexistente
        doc = Document(
            id=1,
            title="Orphaned Document",
            file_type="pdf",
            file_size_bytes=1024,
            file_path="/uploads/nonexistent_file.pdf"
        )

        # Mock DB session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.first.return_value = doc
        mock_db.exec.return_value = mock_query

        # Test
        result = await DocumentService.download_document(1, mock_db)

        # Assertions
        assert result is None
        # Verificar que se llamó a delete y commit para cleanup
        mock_db.delete.assert_called_once_with(doc)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_filename_sanitization(self):
        """AC3: Sanitización de filename"""
        # Test con caracteres especiales en el título
        doc = Document(
            id=1,
                title="Título con <script>alert('xss')</script> & chars especiales!",
            file_type="pdf",
            file_size_bytes=1024,
            file_path="/uploads/test.pdf"
        )

        # Mock de os.path.exists para simular archivo existente
        with patch('os.path.exists', return_value=True):
            # Mock DB session
            mock_db = Mock(spec=Session)
            mock_query = Mock()
            mock_query.first.return_value = doc
            mock_db.exec.return_value = mock_query

            # Test
            result = await DocumentService.download_document(1, mock_db)

            # Verificar sanitización del filename
            assert result is not None
            _, _, safe_filename, _ = result

            # No debe contener caracteres peligrosos
            assert "<script>" not in safe_filename
            assert "&" not in safe_filename
            assert "!" not in safe_filename
            assert "_" in safe_filename  # Debe tener underscores en lugar de espacios
            assert safe_filename.endswith(".pdf")

    @pytest.mark.asyncio
    async def test_download_with_special_characters(self):
        """Test sanitización con caracteres especiales comunes"""
        doc = Document(
            id=1,
            title="Políticas/Reglas 2023 - Versión Final",
            file_type="pdf",
            file_size_bytes=2048,
            file_path="/uploads/test.pdf"
        )

        with patch('os.path.exists', return_value=True):
            mock_db = Mock(spec=Session)
            mock_query = Mock()
            mock_query.first.return_value = doc
            mock_db.exec.return_value = mock_query

            result = await DocumentService.download_document(1, mock_db)

            assert result is not None
            _, _, safe_filename, _ = result

            # Los caracteres especiales deben ser reemplazados
            assert "/" not in safe_filename
            assert safe_filename == "PolíticasReglas_2023_Versión_Final.pdf"


class TestDocumentServicePreview:
    """Tests unitarios para el método get_document_preview"""

    @pytest.mark.asyncio
    async def test_preview_success_long_content(self):
        """AC5: Preview exitoso con contenido largo"""
        # Crear contenido largo (> 500 caracteres)
        long_content = "Este es el contenido del manual de empleados. " * 50

        doc = Document(
            id=1,
            title="Manual Completo",
            content_text=long_content
        )

        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.first.return_value = doc
        mock_db.exec.return_value = mock_query

        # Test
        result = await DocumentService.get_document_preview(1, mock_db)

        # Assertions
        assert result is not None
        assert len(result) == 500  # Exactamente 500 caracteres
        assert result == long_content[:500]

    @pytest.mark.asyncio
    async def test_preview_success_short_content(self):
        """AC5: Preview exitoso con contenido corto (< 500 chars)"""
        short_content = "Este es un contenido corto."

        doc = Document(
            id=2,
            title="Documento Corto",
            content_text=short_content
        )

        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.first.return_value = doc
        mock_db.exec.return_value = mock_query

        # Test
        result = await DocumentService.get_document_preview(2, mock_db)

        # Assertions
        assert result is not None
        assert len(result) <= 500
        assert result == short_content

    @pytest.mark.asyncio
    async def test_preview_document_not_found(self):
        """AC5: Documento no existe retorna None"""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db.exec.return_value = mock_query

        result = await DocumentService.get_document_preview(999, mock_db)

        assert result is None

    @pytest.mark.asyncio
    async def test_preview_no_content_extracted(self):
        """AC5: Documento sin contenido extraído retorna None"""
        doc = Document(
            id=1,
            title="Sin Contenido",
            content_text=None  # No hay contenido extraído
        )

        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.first.return_value = doc
        mock_db.exec.return_value = mock_query

        result = await DocumentService.get_document_preview(1, mock_db)

        assert result is None

    @pytest.mark.asyncio
    async def test_preview_empty_content(self):
        """AC5: Documento con contenido vacío retorna None"""
        doc = Document(
            id=1,
            title="Contenido Vacío",
            content_text=""  # String vacío
        )

        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.first.return_value = doc
        mock_db.exec.return_value = mock_query

        result = await DocumentService.get_document_preview(1, mock_db)

        assert result is None


class TestDocumentServiceSecurity:
    """Tests unitarios para características de seguridad"""

    @pytest.mark.asyncio
    async def test_filename_sanitization_security(self):
        """Test sanitización de filename para seguridad"""
        # Casos de prueba con caracteres potencialmente peligrosos
        test_cases = [
            ("../../../etc/passwd", "etc_passwd"),
            ("file<script>alert('xss')</script>.pdf", "filealertxss.pdf"),
            ("file|rm -rf /", "filerm__rf_"),
            ("normal-file-name.pdf", "normal-file-name.pdf"),  # Normal no debe cambiar
            ("file with spaces.doc", "file_with_spaces.doc"),
        ]

        for original_title, expected_safe in test_cases:
            doc = Document(
                id=1,
                title=original_title,
                file_type="pdf",
                file_size_bytes=1024,
                file_path="/uploads/test.pdf"
            )

            with patch('os.path.exists', return_value=True):
                mock_db = Mock(spec=Session)
                mock_query = Mock()
                mock_query.first.return_value = doc
                mock_db.exec.return_value = mock_query

                result = await DocumentService.download_document(1, mock_db)
                assert result is not None

                _, _, safe_filename, _ = result

                # Verificar que no contenga caracteres peligrosos
                assert "../" not in safe_filename  # Directory traversal
                assert "<" not in safe_filename   # HTML injection
                assert ">" not in safe_filename
                assert "|" not in safe_filename   # Command injection
                assert "'" not in safe_filename   # SQL injection attempt

                # Para nombres normales, debe mantenerse similar
                if " " in original_title:
                    assert "_" in safe_filename or "-" in safe_filename

    @pytest.mark.asyncio
    async def test_logging_structured_format(self):
        """Test que los logs sigan formato estructurado"""
        doc = Document(
            id=1,
            title="Test Document",
            file_type="pdf",
            file_size_bytes=1024,
            file_path="/uploads/test.pdf"
        )

        with patch('os.path.exists', return_value=True), \
             patch('app.services.document_service.logger') as mock_logger:

            mock_db = Mock(spec=Session)
            mock_query = Mock()
            mock_query.first.return_value = doc
            mock_db.exec.return_value = mock_query

            # Test
            result = await DocumentService.download_document(1, mock_db)

            # Verificar que se llamó al logger con formato estructurado
            assert mock_logger.info.called
            call_args = mock_logger.info.call_args[0][0]

            # Debe ser JSON string
            import json
            log_data = json.loads(call_args)

            # Verificar campos requeridos en el log
            assert "event" in log_data
            assert "document_id" in log_data
            assert "success" in log_data
            assert "timestamp" in log_data
            assert log_data["event"] == "download_prepared"
            assert log_data["document_id"] == 1
            assert log_data["success"] is True


class TestDocumentServiceErrorHandling:
    """Tests unitarios para manejo de errores"""

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test manejo de errores de base de datos"""
        mock_db = Mock(spec=Session)
        mock_db.exec.side_effect = Exception("Database connection error")

        with pytest.raises(Exception):
            await DocumentService.download_document(1, mock_db)

    @pytest.mark.asyncio
    async def test_filesystem_error_handling(self):
        """Test manejo de errores de filesystem"""
        doc = Document(
            id=1,
            title="Test Document",
            file_type="pdf",
            file_size_bytes=1024,
            file_path="/uploads/test.pdf"
        )

        with patch('os.path.exists', side_effect=OSError("Permission denied")):
            mock_db = Mock(spec=Session)
            mock_query = Mock()
            mock_query.first.return_value = doc
            mock_db.exec.return_value = mock_query

            # Should raise exception but be handled gracefully
            with pytest.raises(Exception):
                await DocumentService.download_document(1, mock_db)

    @pytest.mark.asyncio
    async def test_preview_database_error(self):
        """Test manejo de errores en preview"""
        mock_db = Mock(spec=Session)
        mock_db.exec.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await DocumentService.get_document_preview(1, mock_db)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])