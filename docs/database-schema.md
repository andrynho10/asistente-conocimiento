# Esquema de Base de Datos - Asistente de Conocimiento

## Overview

Base de datos SQLite local para el prototipo del Asistente de Conocimiento. Ubicación: `database/asistente_conocimiento.db`

## Diagrama Entidad-Relación (texto)

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────────┐
│      User       │       │    Document      │       │ DocumentCategory│
├─────────────────┤       ├──────────────────┤       ├─────────────────┤
│ id (PK)         │───┐   │ id (PK)          │       │ id (PK)         │
│ username (UQ)   │   │   │ title (IDX)      │       │ name (UQ)       │
│ email (UQ)      │   │   │ description      │       │ description     │
│ hashed_password │   └───│ category (IDX)   │       │ created_at      │
│ full_name       │       │ file_path (UQ)   │       └─────────────────┘
│ role            │       │ file_type        │               ▲
│ is_active       │       │ file_size_bytes  │               │
│ created_at      │       │ upload_date (IDX)│
│ updated_at      │       │ uploaded_by (FK) │
│ documents[]     │       │ content_text     │
│ audit_logs[]    │       │ is_indexed       │
└─────────────────┘       │ indexed_at       │
          │               └──────────────────┘
          │                       │
          │              ┌─────────────────┐
          │              │    AuditLog     │
          └──────────────┤ user_id (FK)    │
                         ├─────────────────┤
                         │ id (PK)         │
                         │ action          │
                         │ resource_type   │
                         │ resource_id     │
                         │ details         │
                         │ ip_address      │
                         │ timestamp       │
                         └─────────────────┘
```

## Relaciones

- `User` ←→ `Document` (OneToMany): Un usuario puede cargar múltiples documentos
- `DocumentCategory` ← `Document` (String Reference): Document.category referencia DocumentCategory.name
- `User` ←→ `AuditLog` (OneToMany): Un usuario tiene múltiples registros de auditoría

## Tablas

### 1. User

Tabla de usuarios del sistema con autenticación y autorización basada en roles.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único del usuario |
| username | VARCHAR(50) | UNIQUE, INDEX | Nombre de usuario único para login |
| email | VARCHAR(255) | UNIQUE, INDEX | Email único del usuario |
| hashed_password | VARCHAR(255) | NOT NULL | Password hasheado con bcrypt |
| full_name | VARCHAR(255) | NOT NULL | Nombre completo del usuario |
| role | VARCHAR(5) | NOT NULL | Rol: 'admin' o 'user' (enum UserRole) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Estado activo/inactivo del usuario |
| created_at | DATETIME | NOT NULL | Fecha de creación del registro |
| updated_at | DATETIME | NOT NULL | Fecha de última actualización |

#### Índices
- `ix_user_username` (único) en username
- `ix_user_email` (único) en email

#### Constraints
- `username` debe ser único
- `email` debe ser único
- `role` debe ser 'admin' o 'user'

### 2. DocumentCategory

Tabla para categorías predefinidas de documentos (Story 2.1).

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único de la categoría |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Nombre único de la categoría |
| description | TEXT | NULL | Descripción detallada de la categoría |
| created_at | DATETIME | NOT NULL, DEFAULT now() | Fecha de creación de la categoría |

#### Índices
- `uq_document_categories_name` (único) en name

#### Constraints
- `name` debe ser único

#### Datos Iniciales (seed data)
Las siguientes categorías se insertan automáticamente durante la migración:
1. **Políticas RRHH** - Documentos de políticas de recursos humanos, beneficios, contratación y gestión de personal
2. **Procedimientos Operativos** - Manuales de procedimientos estándar, guías operativas y procesos de negocio
3. **Manuales Técnicos** - Documentación técnica, especificaciones, manuales de usuario y guías de sistemas
4. **FAQs** - Preguntas frecuentes, guías de solución de problemas y respuestas a consultas comunes
5. **Normativas** - Regulaciones, normativas legales, estándares de cumplimiento y requerimientos regulatorios

### 3. Document

Tabla para almacenar metadatos de documentos y contenido extraído (Story 2.1).

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único del documento |
| title | VARCHAR(200) | NOT NULL, INDEX | Título del documento, indexado para búsquedas |
| description | TEXT | NULL | Descripción opcional del documento |
| category | VARCHAR(100) | NOT NULL, INDEX | Categoría del documento (referencia string a DocumentCategory.name) |
| file_type | VARCHAR(10) | NOT NULL | Tipo de archivo: 'pdf' o 'txt' |
| file_size_bytes | INTEGER | NOT NULL | Tamaño del archivo en bytes |
| file_path | VARCHAR(500) | UNIQUE, NOT NULL | Ruta única del archivo en sistema |
| upload_date | DATETIME | NOT NULL, INDEX, DEFAULT now() | Fecha de carga del documento |
| uploaded_by | INTEGER | FOREIGN KEY, NOT NULL | ID del usuario que cargó el documento |
| content_text | TEXT | NULL | Texto extraído del documento (para Story 2.3) |
| is_indexed | BOOLEAN | NOT NULL, DEFAULT FALSE | Indica si el documento está indexado para búsqueda |
| indexed_at | DATETIME | NULL | Fecha cuando se indexó el documento (Story 2.4) |

#### Índices
- `ix_documents_title` en title (para búsquedas rápidas por título)
- `ix_documents_category` en category (para filtrar por categoría)
- `ix_documents_upload_date` en upload_date (para ordenamiento por fecha)

#### Relaciones
- `uploaded_by` referencia `user(id)` (ManyToOne)
- `category` referencia string a `DocumentCategory.name` (sin FK por simplicidad MVP)

#### Constraints
- `file_path` debe ser único
- `file_type` debe ser 'pdf' o 'txt'
- `category` debe corresponder a una categoría válida (validación a nivel de aplicación)
- `uploaded_by` debe referenciar un usuario existente

### 4. AuditLog

Tabla para auditoría de acciones en el sistema (cumplimiento Ley 19.628).

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único del registro |
| user_id | INTEGER | FOREIGN KEY, NOT NULL | ID del usuario que realiza la acción |
| action | VARCHAR(100) | NOT NULL | Acción realizada (create, read, update, delete, etc.) |
| resource_type | VARCHAR(50) | NOT NULL | Tipo de recurso afectado (user, document, etc.) |
| resource_id | INTEGER | NULL | ID del recurso afectado (opcional) |
| details | VARCHAR(1000) | NULL | Detalles adicionales de la acción |
| ip_address | VARCHAR(45) | NULL | Dirección IP del cliente |
| timestamp | DATETIME | NOT NULL | Fecha y hora del evento |

#### Relaciones
- `user_id` referencia `user(id)` (ManyToOne)

## Datos Iniciales

### Usuario Administrador

```sql
-- Credenciales por defecto (cambiar en producción)
-- Username: admin
-- Password: admin123
INSERT INTO user (username, email, full_name, hashed_password, role, is_active, created_at, updated_at)
VALUES ('admin', 'admin@example.com', 'Administrador del Sistema', '$2b$12$nApyQyJSNw3FlTxiFHxcq.rb6mBaaGddmR.ODi4Q/2.qenNWw.m3i', 'admin', 1, datetime('now'), datetime('now'));
```

### Categorías Predefinidas

```sql
-- Ver categorías disponibles
SELECT id, name, description FROM document_categories ORDER BY name;

-- Resultado esperado:
-- 1 | FAQs | Preguntas frecuentes, guías de solución de problemas y respuestas a consultas comunes
-- 2 | Manuales Técnicos | Documentación técnica, especificaciones, manuales de usuario y guías de sistemas
-- 3 | Normativas | Regulaciones, normativas legales, estándares de cumplimiento y requerimientos regulatorios
-- 4 | Políticas RRHH | Documentos de políticas de recursos humanos, beneficios, contratación y gestión de personal
-- 5 | Procedimientos Operativos | Manuales de procedimientos estándar, guías operativas y procesos de negocio
```

## Queries de Verificación

### Verificar usuarios
```sql
SELECT id, username, email, role, is_active FROM user;
```

### Verificar documentos por categoría
```sql
SELECT dc.name, COUNT(d.id) as document_count
FROM document_categories dc
LEFT JOIN documents d ON dc.name = d.category
GROUP BY dc.id, dc.name
ORDER BY dc.name;
```

### Verificar documentos recientes
```sql
SELECT d.title, d.category, d.file_type, d.upload_date, u.username
FROM documents d
JOIN user u ON d.uploaded_by = u.id
ORDER BY d.upload_date DESC
LIMIT 10;
```

### Verificar documentos por tipo de archivo
```sql
SELECT file_type, COUNT(*) as count, SUM(file_size_bytes) as total_size_bytes
FROM documents
GROUP BY file_type;
```

### Verificar documentos indexados
```sql
SELECT
  is_indexed,
  COUNT(*) as count,
  COUNT(CASE WHEN indexed_at IS NOT NULL THEN 1 END) as indexed_count
FROM documents
GROUP BY is_indexed;
```

### Verificar logs de auditoría recientes
```sql
SELECT u.username, a.action, a.resource_type, a.timestamp
FROM auditlog a
JOIN user u ON a.user_id = u.id
ORDER BY a.timestamp DESC
LIMIT 10;
```

### Verificar documentos por usuario
```sql
SELECT u.username, COUNT(d.id) as document_count
FROM user u
LEFT JOIN documents d ON u.id = d.uploaded_by
GROUP BY u.id, u.username
ORDER BY document_count DESC;
```

## Scripts de Mantenimiento

### Backup de base de datos
```bash
sqlite3 database/asistente_conocimiento.db ".backup database/asistente_conocimiento_backup_$(date +%Y%m%d_%H%M%S).db"
```

### Verificar integridad de la base de datos
```bash
sqlite3 database/asistente_conocimiento.db "PRAGMA integrity_check;"
```

### Verificar tamaño de la base de datos
```bash
ls -lh database/asistente_conocimiento.db
```

## Migration History

Las migraciones se gestionan con Alembic en `backend/alembic/`:

- **23b7d269978c_initial_schema.py**: Creación inicial de tablas user, document, auditlog (Epic 1)
- **3336ed844a79_add_documents_models_and_document_.py**: Story 2.1 - Modelos Document y DocumentCategory con índices y seed data

Para ver historial de migraciones:
```bash
cd backend && poetry run alembic history
```

Para ver migración actual:
```bash
cd backend && poetry run alembic current
```

## Cambios Recientes - Story 2.1 (Modelos de Datos para Documentos y Metadatos)

### Novedades principales
- **Nueva tabla**: `document_categories` con 5 categorías predefinidas
- **Tabla actualizada**: `documents` renombrada a `documents` (ya existía pero extendida)
- **Campos nuevos en documents**: description, file_type, file_size_bytes (renombrado), category (indexado), uploaded_by (FK), content_text, is_indexed, indexed_at
- **Índices agregados**: title, category, upload_date para optimizar búsquedas
- **Seed data**: 5 categorías predefinidas insertadas automáticamente

### Impacto en queries existentes
- Los queries a `document` ahora deben usar `documents` (plural)
- `file_size` renombrado a `file_size_bytes`
- `user_id` renombrado a `uploaded_by`
- Se agregaron nuevos campos útiles para búsquedas y filtrado

### Mejoras de performance
- Índices en campos frecuentemente consultados (title, category, upload_date)
- Constraint UNIQUE en file_path mantiene integridad
- FK a user.id asegura consistencia de datos

## Consideraciones de Seguridad

1. **Passwords**: Nunca almacenados en texto plano, siempre hasheados con bcrypt
2. **Auditoría**: Todas las acciones relevantes se registran en `auditlog`
3. **Cumplimiento**: Schema diseñado para cumplimiento Ley 19.628 (protección de datos)
4. **Acceso**: Implementar control de acceso granular a nivel de aplicación

## Próximos Mejoras

1. **Soft Delete**: Considerar añadir `deleted_at` para eliminación lógica
2. **Versioning**: Para documentos, considerar control de versiones
3. **Indexación Adicional**: Índices compuestos para consultas frecuentes
4. **Particionamiento**: Para tablas de auditoría si crecen significativamente