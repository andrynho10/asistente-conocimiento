# Documentación API - Gestión del Conocimiento

Esta documentación describe los endpoints disponibles para la gestión de documentos en el sistema de asistente de conocimiento.

## Autenticación

Todos los endpoints requieren autenticación mediante token JWT en el header:
```
Authorization: Bearer <token_jwt>
```

## Endpoints de Documentos

### GET /api/knowledge/documents
Listar documentos con filtros y paginación.

**Headers:**
- Authorization: Bearer {token_jwt}

**Query Parameters:**
- category (string, opcional): Filtrar por categoría
- limit (int, opcional, default=20): Número máximo de resultados
- offset (int, opcional, default=0): Offset para paginación
- sort_by (string, opcional, default="upload_date"): Campo de ordenamiento (upload_date, title, file_size_bytes)
- order (string, opcional, default="desc"): Dirección de ordenamiento (asc, desc)

**Response:**
```json
[
  {
    "id": 1,
    "title": "Políticas de RRHH",
    "description": "Documento con políticas internas",
    "category": "recursos-humanos",
    "file_type": "pdf",
    "file_size_bytes": 1024000,
    "upload_date": "2025-01-15T10:30:00Z",
    "uploaded_by": "admin_user",
    "is_indexed": true,
    "indexed_at": "2025-01-15T10:35:00Z"
  }
]
```

### GET /api/knowledge/documents/{document_id}
Obtener detalles de un documento específico.

**Headers:**
- Authorization: Bearer {token_jwt}

**Path Parameters:**
- document_id (int): ID del documento

**Response:**
```json
{
  "id": 1,
  "title": "Políticas de RRHH",
  "description": "Documento con políticas internas",
  "category": "recursos-humanos",
  "file_type": "pdf",
  "file_size_bytes": 1024000,
  "upload_date": "2025-01-15T10:30:00Z",
  "uploaded_by": "admin_user",
  "is_indexed": true,
  "indexed_at": "2025-01-15T10:35:00Z"
}
```

**Error Responses:**
- 404 Not Found: El documento no existe
- 500 Internal Server Error: Error del servidor

### GET /api/knowledge/documents/{document_id}/download
Descargar un documento.

**Headers:**
- Authorization: Bearer {token_jwt}

**Path Parameters:**
- document_id (int): ID del documento

**Response:**
Archivo binario con headers apropiados:
- Content-Type: application/pdf o text/plain
- Content-Disposition: attachment; filename="nombre_seguro.pdf"

**Error Responses:**
- 404 Not Found: El documento no existe o archivo huérfano
- 500 Internal Server Error: Error del servidor

### GET /api/knowledge/documents/{document_id}/preview
Obtener vista previa del documento (primeros 500 caracteres).

**Headers:**
- Authorization: Bearer {token_jwt}

**Path Parameters:**
- document_id (int): ID del documento

**Response:**
```json
{
  "document_id": 1,
  "preview": "Primeros 500 caracteres del contenido del documento...",
  "preview_length": 500,
  "message": "Preview del documento"
}
```

**Error Responses:**
- 404 Not Found: El documento no existe o no tiene contenido extraído
- 500 Internal Server Error: Error del servidor

### DELETE /api/knowledge/documents/{document_id}
**⚠️ Solo administradores**

Eliminar un documento del repositorio con auditoría completa.

**Headers:**
- Authorization: Bearer {token_jwt} (requiere rol de admin)

**Path Parameters:**
- document_id (int): ID del documento a eliminar

**Response (200 OK):**
```json
{
  "document_id": 1,
  "deleted": true,
  "message": "Documento eliminado exitosamente",
  "deleted_by": "admin_user"
}
```

**Error Responses:**

**403 Forbidden** - Usuario no tiene permisos de administrador:
```json
{
  "detail": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "Permisos insuficientes"
  }
}
```

**404 Not Found** - El documento no existe:
```json
{
  "detail": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "El documento solicitado no existe"
  }
}
```

**500 Internal Server Error** - Error interno del servidor:
```json
{
  "detail": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "Error interno del servidor al eliminar el documento"
  }
}
```

**Comportamiento:**
1. **Eliminación atómica**: La operación elimina tanto el registro de la base de datos como el archivo físico
2. **Auditoría completa**: Se registra evento en audit_logs con detalles del usuario, timestamp, IP y resultado
3. **Manejo de archivos huérfanos**: Si el archivo físico no existe, la operación continúa eliminando solo el registro de DB
4. **Eliminación de índice FTS**: Se elimina la entrada correspondiente del índice de búsqueda full-text
5. **Validación de permisos**: Solo usuarios con rol 'admin' pueden eliminar documentos

**Consideraciones de seguridad:**
- Se requiere rol de administrador
- Todas las acciones se registran en audit_logs
- Se previene directory traversal en validación de paths
- Se manejan errores de forma segura sin exponer información sensible

## Endpoints de Búsqueda

### GET /api/knowledge/search
Buscar documentos por contenido full-text.

**Headers:**
- Authorization: Bearer {token_jwt}

**Query Parameters:**
- q (string, requerido): Query de búsqueda (mínimo 2 caracteres)
- limit (int, opcional, default=20): Número máximo de resultados
- offset (int, opcional, default=0): Offset para paginación

**Response:**
```json
{
  "query": "políticas de vacaciones",
  "total": 5,
  "documents": [
    {
      "document_id": 1,
      "title": "Políticas de RRHH",
      "category": "recursos-humanos",
      "snippet": "...políticas de <mark>vacaciones</mark> anuales...",
      "relevance_score": 0.95,
      "upload_date": "2025-01-15T10:30:00Z",
      "uploaded_by": "admin_user"
    }
  ]
}
```

## Endpoints de Categorías

### GET /api/knowledge/categories
Listar categorías disponibles con contador de documentos.

**Headers:**
- Authorization: Bearer {token_jwt}

**Response:**
```json
[
  {
    "name": "recursos-humanos",
    "description": "Documentos de RRHH y políticas internas",
    "document_count": 15
  },
  {
    "name": "seguridad",
    "description": "Políticas de seguridad y procedimientos",
    "document_count": 8
  }
]
```

## Códigos de Error Estándar

La API utiliza códigos de error estandarizados para facilitar el manejo de errores:

| Código | Descripción |
|--------|-------------|
| `INVALID_TOKEN` | Token JWT inválido o expirado |
| `USER_NOT_FOUND` | Usuario no encontrado en base de datos |
| `USER_INACTIVE` | Usuario está inactivo |
| `INSUFFICIENT_PERMISSIONS` | Permisos insuficientes para la operación |
| `DOCUMENT_NOT_FOUND` | Documento no encontrado |
| `INVALID_CATEGORY` | Categoría especificada no existe |
| `INVALID_FILE_FORMAT` | Formato de archivo no permitido |
| `FILE_TOO_LARGE` | Archivo excede tamaño máximo |
| `INVALID_QUERY` | Query de búsqueda inválida |
| `SEARCH_ERROR` | Error en búsqueda full-text |
| `INTERNAL_SERVER_ERROR` | Error interno del servidor |

## Límites y Restricciones

- **Tamaño máximo de archivo**: 10MB
- **Formatos permitidos**: PDF (.pdf), TXT (.txt)
- **Longitud mínima de búsqueda**: 2 caracteres
- **Longitud máxima de búsqueda**: 200 caracteres
- **Resultados por página**: Máximo 100
- **Timeout de operaciones**: 30 segundos

## Auditoría

Todas las operaciones críticas se registran en la tabla `audit_logs` con:
- ID de usuario
- Acción realizada
- Tipo de recurso
- ID del recurso
- Timestamp
- IP address
- Detalles adicionales

Las acciones auditadas incluyen:
- DOCUMENT_UPLOADED
- DOCUMENT_DOWNLOADED
- DOCUMENT_DELETED
- DELETE_ATTEMPT