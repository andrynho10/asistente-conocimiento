# Esquema de Base de Datos - Asistente de Conocimiento

## Overview

Base de datos SQLite local para el prototipo del Asistente de Conocimiento. Ubicación: `database/asistente_conocimiento.db`

## Diagrama Entidad-Relación (texto)

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│      User       │       │    Document     │       │    AuditLog     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │───┐   │ id (PK)         │       │ id (PK)         │
│ username (UQ)   │   │   │ title           │       │ user_id (FK)    │───┐
│ email (UQ)      │   └───│ category        │       │ action          │   │
│ hashed_password │       │ file_path (UQ)  │       │ resource_type   │   │
│ full_name       │       │ file_size       │       │ resource_id     │   │
│ role            │       │ upload_date     │       │ details         │   │
│ is_active       │       │ user_id (FK)    │───────┤ ip_address      │   │
│ created_at      │       │ status          │       │ timestamp       │   │
│ updated_at      │       └─────────────────┘       └─────────────────┘   │
└─────────────────┘                                                        │
          │                                                             │
          └─────────────────────────────────────────────────────────────┘
```

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

### 2. Document

Tabla para almacenar información de documentos cargados en el sistema.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único del documento |
| title | VARCHAR(255) | NOT NULL | Título del documento |
| category | VARCHAR(100) | NOT NULL, DEFAULT 'General' | Categoría del documento |
| file_path | VARCHAR(500) | UNIQUE, NOT NULL | Ruta única del archivo |
| file_size | INTEGER | NOT NULL, >= 0 | Tamaño del archivo en bytes |
| upload_date | DATETIME | NOT NULL | Fecha de carga del documento |
| user_id | INTEGER | FOREIGN KEY, NOT NULL | ID del usuario que cargó el documento |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | Estado del documento |

#### Relaciones
- `user_id` referencia `user(id)` (ManyToOne)

#### Constraints
- `file_path` debe ser único
- `file_size` debe ser >= 0

### 3. AuditLog

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
-- Categorías base para el sistema
INSERT INTO document (title, category, file_path, file_size, upload_date, user_id, status)
VALUES
  ('Categoría: Políticas RRHH', 'Políticas RRHH', '/categories/politicas_rrhh.md', 0, datetime('now'), 1, 'active'),
  ('Categoría: Procedimientos Operativos', 'Procedimientos Operativos', '/categories/procedimientos_operativos.md', 0, datetime('now'), 1, 'active'),
  ('Categoría: Manuales Técnicos', 'Manuales Técnicos', '/categories/manuales_tecnicos.md', 0, datetime('now'), 1, 'active');
```

## Queries de Verificación

### Verificar usuarios
```sql
SELECT id, username, email, role, is_active FROM user;
```

### Verificar documentos por categoría
```sql
SELECT category, COUNT(*) as count
FROM document
GROUP BY category;
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
LEFT JOIN document d ON u.id = d.user_id
GROUP BY u.id, u.username;
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

- **23b7d269978c_initial_schema.py**: Creación inicial de tablas user, document, auditlog

Para ver historial de migraciones:
```bash
cd backend && poetry run alembic history
```

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