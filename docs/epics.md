# Asistente-Conocimiento - Epic Breakdown

**Author:** Andres Amaya Garces
**Date:** 2025-11-10
**Project Level:** Level 3 (Alta Complejidad - Web App + AI Backend + Cumplimiento Normativo)
**Target Scale:** Prototipo funcional (5-10 usuarios concurrentes, 50-100 documentos)

---

## Overview

This document provides the complete epic and story breakdown for Asistente-Conocimiento, decomposing the requirements from the [PRD](./PRD.md) into implementable stories.

### Resumen Ejecutivo de Épicas

**Épica 1: Fundación e Infraestructura del Proyecto**
- Establecer la base técnica del proyecto (estructura, arquitectura de 3 capas, pipeline básico)
- Historias: 6 historias (configuración inicial → despliegue base)

**Épica 2: Gestión del Conocimiento Corporativo**
- Habilitar captura, almacenamiento y organización del conocimiento organizacional
- Historias: 7 historias (modelos de datos → búsqueda de documentos)

**Épica 3: Motor de IA Generativa y Consultas en Lenguaje Natural**
- Implementar RAG y capacidades conversacionales de IA
- Historias: 6 historias (integración LLM → optimización de rendimiento)

**Épica 4: Generación Automática de Contenido Formativo**
- Crear material de capacitación personalizado automáticamente
- Historias: 5 historias (resúmenes → learning paths)

**Épica 5: Seguridad, Cumplimiento Normativo y Auditoría**
- Garantizar cumplimiento legal chileno y protección de datos
- Historias: 6 historias (autenticación → control de acceso granular)

**Total: 30 historias de usuario**

---

## Epic 1: Fundación e Infraestructura del Proyecto

**Objetivo:** Crear la infraestructura base que habilita todo el desarrollo posterior del prototipo de IA generativa. Esta épica establece la arquitectura de 3 capas, el entorno de desarrollo, las dependencias fundamentales, y el pipeline básico de despliegue.

**Valor de Negocio:** Sin esta fundación técnica, ninguna historia posterior puede ejecutarse. Es el prerequisito crítico para el proyecto greenfield.

**Alineación con PRD:** RNF3 (Arquitectura Escalable), Sprint 0-1.

---

### Story 1.1: Configuración Inicial del Proyecto y Estructura de Carpetas

Como desarrollador del equipo,
Quiero establecer la estructura base del proyecto con todas las carpetas y archivos de configuración necesarios,
Para que el equipo tenga un punto de partida organizado y estándar para el desarrollo.

**Acceptance Criteria:**

**Given** que inicio un nuevo proyecto desde cero
**When** ejecuto el script de inicialización del proyecto
**Then** se crea la estructura de carpetas estándar:
```
asistente-conocimiento/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── config.py
├── frontend/
│   ├── static/
│   ├── templates/
│   └── package.json
├── database/
│   └── migrations/
├── docs/
├── .gitignore
├── README.md
└── docker-compose.yml (opcional)
```

**And** se crea un archivo `pyproject.toml` con Poetry y dependencias iniciales:
- fastapi==0.115.0 (framework web)
- sqlmodel==0.0.14 (ORM: SQLAlchemy + Pydantic)
- python-jose[cryptography]==3.3.0 (autenticación JWT)
- passlib[bcrypt]==1.7.4 (password hashing)
- python-multipart==0.0.9 (file uploads)
- python-dotenv (variables de entorno)
- pytest (testing)

**And** se crea un archivo `.env.example` con variables de entorno template:
```
DATABASE_URL=sqlite:///./asistente_conocimiento.db
SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=24
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
```

**And** el archivo README.md contiene instrucciones básicas de instalación y ejecución

**Prerequisites:** Ninguno (primera historia del proyecto)

**Technical Notes:**
- Usar Python 3.12 (especificado en architecture.md)
- Instalar Poetry 1.8+ para dependency management
- Incluir `.gitignore` para Python (excluir `__pycache__`, `.env`, `*.pyc`, venv)
- Crear repositorio Git local e inicial commit

---

### Story 1.2: Configuración de Base de Datos y Modelos Iniciales

Como desarrollador backend,
Quiero configurar la base de datos relacional con modelos ORM iniciales,
Para que el sistema tenga persistencia de datos desde el inicio del desarrollo.

**Acceptance Criteria:**

**Given** que la estructura del proyecto ya está creada (Story 1.1)
**When** configuro la conexión a la base de datos
**Then** se crea una base de datos SQLite local en `database/asistente_conocimiento.db`

**And** se configuran modelos SQLModel iniciales:
- `User` (id, username, email, hashed_password, full_name, role, is_active, created_at, updated_at)
- `Document` (id, title, category, file_path, file_size, upload_date, user_id, status)
- `AuditLog` (id, user_id, action, resource_type, resource_id, details, ip_address, timestamp)

**And** las migraciones de base de datos se gestionan con Alembic 1.13+

**And** se crea un script `init_db.py` que:
- Crea las tablas
- Inserta usuario admin inicial (username: admin, password: admin123 - solo para desarrollo)
- Inserta categorías predefinidas: "Políticas RRHH", "Procedimientos Operativos", "Manuales Técnicos"

**And** ejecutar `python init_db.py` deja la base de datos operativa

**Prerequisites:** Story 1.1 completada

**Technical Notes:**
- Usar SQLModel ORM (combina SQLAlchemy + Pydantic) para portabilidad futura (fácil migrar a PostgreSQL)
- Passwords NUNCA en texto plano: usar `passlib[bcrypt]` con `pwd_context.hash()`
- Documentar esquema de base de datos en `docs/database-schema.md`
- Considerar constraints: `username` único, `email` único, `role` con enum UserRole ('admin', 'user')

---

### Story 1.3: API REST Base con Autenticación JWT

Como desarrollador backend,
Quiero implementar una API REST básica con autenticación JWT,
Para que el frontend pueda comunicarse de manera segura con el backend desde el inicio.

**Acceptance Criteria:**

**Given** que tengo la base de datos configurada (Story 1.2)
**When** implemento los endpoints básicos de autenticación
**Then** existen los siguientes endpoints operativos:

**POST /api/auth/login**
- Body: `{"username": "string", "password": "string"}`
- Response 200: `{"token": "JWT_STRING", "user_id": 1, "role": "admin"}`
- Response 401: `{"error": {"code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos"}}`

**POST /api/auth/logout** (opcional - JWT es stateless)
- Headers: `Authorization: Bearer {token}`
- Response 200: `{"message": "Logout successful"}`

**GET /api/health** (endpoint público sin autenticación)
- Response 200: `{"status": "ok", "version": "1.0.0"}`

**And** el token JWT contiene payload:
```json
{
  "user_id": 1,
  "role": "admin",
  "exp": 1699999999  // expiration timestamp (24 horas)
}
```

**And** se implementa middleware `@require_auth` que:
- Valida token JWT en header `Authorization: Bearer {token}`
- Extrae `user_id` y `role` del token
- Retorna 401 si token inválido o expirado

**And** se implementa middleware `@require_role('admin')` para endpoints sensibles

**And** las contraseñas se validan con `passlib[bcrypt]` usando `pwd_context.verify()`

**Prerequisites:** Story 1.2 completada

**Technical Notes:**
- Usar biblioteca `python-jose[cryptography]` para generación y validación de tokens JWT
- Secret key debe venir de variable de entorno `SECRET_KEY`
- Token expira en 24 horas (configurable en `.env`)
- Implementar manejo de errores consistente (formato JSON estándar)
- Documentar API en `docs/api-endpoints.md`

---

### Story 1.4: Frontend Base con Sistema de Login

Como usuario del sistema,
Quiero tener una interfaz web básica con login funcional,
Para poder autenticarme y acceder al sistema de manera segura.

**Acceptance Criteria:**

**Given** que la API de autenticación está operativa (Story 1.3)
**When** accedo a la URL raíz del sistema (`http://localhost:5000/`)
**Then** soy redirigido a la página de login si no estoy autenticado

**And** la página de login contiene:
- Logo o título: "Asistente de Conocimiento - Isapre Banmédica"
- Campo de texto: Username (requerido)
- Campo de contraseña: Password (requerido, input type="password")
- Botón: "Iniciar Sesión"
- Mensaje de error visible si login falla

**And** cuando ingreso credenciales válidas y hago click en "Iniciar Sesión":
- Se envía POST a `/api/auth/login`
- El token JWT se almacena en `sessionStorage`
- Soy redirigido a `/dashboard`

**And** cuando ingreso credenciales inválidas:
- Se muestra mensaje de error: "Usuario o contraseña incorrectos"
- Los campos NO se limpian (UX: permitir corregir)

**And** existe una página `/dashboard` protegida que:
- Verifica presencia de token en sessionStorage
- Si no hay token → redirige a `/login`
- Si hay token → muestra mensaje "Bienvenido, [username]" y botón "Cerrar Sesión"

**And** el botón "Cerrar Sesión":
- Elimina token de sessionStorage
- Redirige a `/login`

**Prerequisites:** Story 1.3 completada

**Technical Notes:**
- Frontend: Vite 6.0 + React 18 + TypeScript + shadcn/ui (especificado en architecture.md)
- Almacenar token en `sessionStorage` (se borra al cerrar pestaña) NO en `localStorage` por seguridad
- Implementar validación de campos en frontend (no enviar si vacíos)
- CSS básico: usar framework como Bootstrap o Tailwind para diseño profesional rápido
- Responsive: funciona en desktop (1920x1080) y tablet (1024x768) mínimo

---

### Story 1.5: Configuración de Entorno de Desarrollo con Variables de Entorno

Como desarrollador,
Quiero gestionar configuraciones sensibles (claves API, secrets) mediante variables de entorno,
Para evitar hardcodear secretos en el código y facilitar despliegue en múltiples entornos.

**Acceptance Criteria:**

**Given** que el proyecto tiene dependencias instaladas
**When** creo un archivo `.env` basado en `.env.example`
**Then** el sistema carga variables de entorno automáticamente usando `python-dotenv`

**And** las siguientes variables están configuradas:
```
# Database
DATABASE_URL=sqlite:///./database/asistente_conocimiento.db

# Security
SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_EXPIRATION_HOURS=24

# AI Service (Local LLM)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500
LLM_CONTEXT_SIZE=8192

# Environment
ENVIRONMENT=development
DEBUG=True
```

**And** existe un archivo `config.py` que:
- Carga variables de `.env` usando `load_dotenv()`
- Valida que variables críticas estén presentes (lanza error si faltan)
- Exporta configuración como objeto `Config`

**And** el archivo `.env` está en `.gitignore` (NUNCA commitear secrets)

**And** el archivo `.env.example` está documentado con descripción de cada variable

**And** el README.md incluye sección "Configuración Inicial":
1. Copiar `.env.example` → `.env`
2. Instalar Ollama: `curl https://ollama.ai/install.sh | sh` (Linux/Mac) o descargar desde ollama.ai (Windows)
3. Descargar modelo Llama: `ollama pull llama3.1:8b-instruct-q4_K_M`
4. Generar `SECRET_KEY` único (comando: `python -c "import secrets; print(secrets.token_hex(32))"`)

**Prerequisites:** Story 1.1 completada

**Technical Notes:**
- Usar biblioteca `python-dotenv`
- Validar presencia de variables críticas al inicio (fail-fast)
- Documentar instalación de Ollama en `docs/setup-llama-local.md`
- Modelo cuantizado q4_K_M requiere ~8GB RAM mínimo
- Considerar usar diferentes `.env` para dev/test/prod (`.env.development`, `.env.production`)
- **CRÍTICO:** Educar al equipo sobre NUNCA commitear archivos `.env`

---

### Story 1.6: Pipeline Básico de CI/CD y Documentación de Despliegue

Como miembro del equipo,
Quiero un proceso documentado para ejecutar el proyecto localmente y ejecutar tests,
Para asegurar que cualquier desarrollador pueda levantar el sistema fácilmente.

**Acceptance Criteria:**

**Given** que tengo el código fuente del proyecto
**When** sigo las instrucciones del README.md
**Then** puedo levantar el proyecto localmente en <10 minutos

**And** el README.md contiene secciones claras:
1. **Requisitos previos:** Python 3.9+, pip, virtualenv
2. **Instalación:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Editar .env con configuraciones reales
   python init_db.py
   ```
3. **Ejecución:**
   ```bash
   python run.py  # o uvicorn app.main:app --reload
   # Sistema disponible en http://localhost:8000
   ```
4. **Testing:**
   ```bash
   pytest tests/
   ```

**And** existe un archivo `run.py` que:
- Carga configuración de `.env`
- Inicializa la aplicación FastAPI
- Ejecuta servidor en modo desarrollo usando uvicorn

**And** existe una suite de tests inicial (`tests/test_auth.py`):
- Test: Login con credenciales válidas → retorna token JWT
- Test: Login con credenciales inválidas → retorna 401
- Test: Endpoint protegido sin token → retorna 401
- Test: Endpoint protegido con token válido → retorna 200

**And** ejecutar `pytest` pasa todos los tests (100% passing)

**And** existe archivo `docs/deployment.md` con:
- Instrucciones para ambiente de desarrollo local
- Troubleshooting común (ej. "ModuleNotFoundError", problemas de base de datos)

**Prerequisites:** Stories 1.1 - 1.5 completadas

**Technical Notes:**
- Usar `pytest` como framework de testing
- Configurar pytest con `pytest.ini` o `setup.cfg`
- Tests deben usar base de datos de prueba separada (no sobrescribir desarrollo)
- Opcional: Configurar GitHub Actions para CI automático (ejecutar tests en cada push)
- Documentar arquitectura de 3 capas en `docs/arquitectura.md`

---

## Epic 2: Gestión del Conocimiento Corporativo

**Objetivo:** Habilitar la captura, almacenamiento, procesamiento y organización del conocimiento organizacional. Esta épica implementa el repositorio de conocimiento que será la base de datos para el motor de IA.

**Valor de Negocio:** Resolver el problema de "conocimiento fragmentado" permitiendo centralizar documentos corporativos de manera estructurada, indexada y consultable. Sin esta épica, la IA no tendría fuente de conocimiento corporativo.

**Alineación con PRD:** RF1 (Registro y Almacenamiento de Conocimiento), RF3 (Gestión Documental), Sprint 2.

---

### Story 2.1: Modelos de Datos para Documentos y Metadatos

Como desarrollador backend,
Quiero extender los modelos de datos para soportar documentos con metadatos ricos,
Para que el sistema pueda almacenar y consultar información estructurada sobre cada documento.

**Acceptance Criteria:**

**Given** que tengo la base de datos configurada (Epic 1)
**When** extiendo el modelo `Document` en SQLModel
**Then** el modelo `Document` contiene los siguientes campos:
- `id` (Integer, Primary Key, Auto-increment)
- `title` (String(200), Not Null, Indexado)
- `description` (Text, Nullable)
- `file_path` (String(500), Not Null, Unique)
- `file_type` (String(10), Not Null) // 'pdf', 'txt'
- `file_size_bytes` (Integer, Not Null)
- `category` (String(100), Not Null, Indexado)
- `upload_date` (DateTime, Not Null, Default: now())
- `uploaded_by` (Integer, Foreign Key → User.id)
- `content_text` (Text, Nullable) // Texto extraído del documento
- `is_indexed` (Boolean, Default: False)
- `indexed_at` (DateTime, Nullable)

**And** se crea un modelo `DocumentCategory`:
- `id` (Integer, Primary Key)
- `name` (String(100), Unique, Not Null)
- `description` (Text, Nullable)
- `created_at` (DateTime, Default: now())

**And** la relación entre modelos está definida:
- `Document.uploaded_by` → FK a `User.id` (relación many-to-one)
- `Document.category` → referencia a `DocumentCategory.name`

**And** se crea migración de base de datos que:
- Agrega nuevas columnas a tabla `documents`
- Crea tabla `document_categories`
- Inserta categorías predefinidas: "Políticas RRHH", "Procedimientos Operativos", "Manuales Técnicos", "FAQs", "Normativas"

**And** ejecutar migración actualiza la base de datos sin perder datos existentes

**Prerequisites:** Epic 1 completada (especialmente Story 1.2)

**Technical Notes:**
- Usar Alembic para migraciones (mantener historial de cambios en esquema)
- `content_text` almacena texto extraído de PDF/TXT para indexación full-text
- `is_indexed` flag permite procesar indexación en background sin bloquear carga
- Considerar índices en: `title`, `category`, `upload_date` (para búsquedas rápidas)
- Documentar modelo actualizado en `docs/database-schema.md`

---

### Story 2.2: API de Carga de Documentos con Validación

Como administrador,
Quiero cargar documentos (PDF, TXT) al sistema mediante una API REST,
Para centralizar el conocimiento organizacional de manera segura y validada.

**Acceptance Criteria:**

**Given** que estoy autenticado como administrador (Story 1.3)
**When** implemento el endpoint de carga de documentos
**Then** existe el endpoint:

**POST /api/knowledge/upload**
- Headers: `Authorization: Bearer {admin_token}`, `Content-Type: multipart/form-data`
- Body (form-data):
  - `file` (archivo, requerido)
  - `title` (string, requerido, max 200 chars)
  - `description` (string, opcional, max 1000 chars)
  - `category` (string, requerido, debe existir en `DocumentCategory`)
- Response 201:
  ```json
  {
    "document_id": 1,
    "title": "Manual de Procedimientos",
    "file_path": "/uploads/manual_procedimientos_20251110.pdf",
    "status": "uploaded",
    "message": "Documento cargado exitosamente. Indexación en progreso."
  }
  ```

**And** el sistema valida:
- Formato de archivo: solo PDF y TXT (rechazar otros con error 400)
- Tamaño máximo: 10MB (rechazar mayores con error 413)
- Categoría existe en base de datos (rechazar si no existe con error 400)
- Usuario tiene rol 'admin' (rechazar si 'user' con error 403)

**And** cuando la validación es exitosa:
- Archivo se guarda en directorio `/uploads/` con nombre único: `{sanitized_title}_{timestamp}.{ext}`
- Se crea registro en tabla `documents` con estado `is_indexed=False`
- Se registra en `audit_logs`: evento "DOCUMENT_UPLOADED"

**And** cuando la validación falla:
- Response 400: `{"error": {"code": "INVALID_FILE_TYPE", "message": "Solo se permiten archivos PDF y TXT"}}`
- Response 413: `{"error": {"code": "FILE_TOO_LARGE", "message": "El archivo excede el límite de 10MB"}}`
- Response 400: `{"error": {"code": "INVALID_CATEGORY", "message": "La categoría especificada no existe"}}`

**Prerequisites:** Story 2.1 completada

**Technical Notes:**
- Usar validación Pydantic (dentro de SQLModel) para sanitizar nombres de archivo o `pathlib.Path`
- Crear directorio `/uploads/` si no existe (usar `os.makedirs(exist_ok=True)`)
- Almacenar `file_size_bytes` calculado de archivo subido
- Validar extensión de archivo en backend (no confiar en MIME type del cliente)
- Implementar en `backend/app/routes/knowledge.py`
- Agregar tests: carga exitosa, validación de formato, validación de tamaño, autorización

---

### Story 2.3: Extracción de Texto de Documentos PDF y TXT

Como sistema,
Quiero extraer automáticamente el texto de documentos cargados (PDF y TXT),
Para poder indexar el contenido y hacerlo consultable por la IA.

**Acceptance Criteria:**

**Given** que un documento fue cargado exitosamente (Story 2.2)
**When** el sistema procesa el archivo
**Then** si el archivo es TXT:
- Se lee el contenido completo del archivo
- Se almacena en `Document.content_text`
- Se marca `is_indexed=True`, `indexed_at=now()`

**And** si el archivo es PDF:
- Se usa biblioteca de extracción de texto (PyPDF2 o pdfplumber)
- Se extrae texto de todas las páginas
- Se limpia el texto (eliminar caracteres especiales, normalizar espacios)
- Se almacena en `Document.content_text`
- Se marca `is_indexed=True`, `indexed_at=now()`

**And** si la extracción falla:
- Se registra error en logs
- Se marca `is_indexed=False` (permitir reintento manual)
- Se actualiza `Document.description` agregando nota: "[ERROR: No se pudo extraer texto]"

**And** la extracción ocurre de manera **asíncrona** (no bloquea respuesta de upload):
- Endpoint `/upload` retorna inmediatamente tras guardar archivo
- Proceso de indexación se ejecuta en background (usar threading o task queue)

**And** existe endpoint para verificar estado de indexación:
**GET /api/knowledge/documents/{document_id}/status**
- Response: `{"document_id": 1, "is_indexed": true, "indexed_at": "2025-11-10T10:30:00Z"}`

**Prerequisites:** Story 2.2 completada

**Technical Notes:**
- **Opción 1:** Usar `PyPDF2` (más ligero, puede fallar con PDFs complejos)
- **Opción 2:** Usar `pdfplumber` (más robusto, maneja mejor PDFs escaneados)
- **Opción 3:** Usar `PyMuPDF (fitz)` (más rápido, mejor para PDFs grandes)
- Implementar procesamiento asíncrono con `threading` o librería `celery` (si necesario)
- Limitar `content_text` a primeros 50,000 caracteres (evitar sobrecarga de memoria)
- Loggear tiempo de extracción (métrica de rendimiento)
- Agregar tests: extracción TXT exitosa, extracción PDF exitosa, manejo de error PDF corrupto

---

### Story 2.4: Indexación Full-Text para Búsqueda Rápida

Como sistema,
Quiero crear un índice invertido del contenido de documentos,
Para permitir búsquedas rápidas de palabras clave y relevancia semántica.

**Acceptance Criteria:**

**Given** que los documentos tienen texto extraído (Story 2.3)
**When** implemento el sistema de indexación
**Then** se crea un índice full-text sobre la columna `Document.content_text`

**And** el sistema usa **SQLite FTS5** (Full-Text Search):
- Se crea tabla virtual: `documents_fts` usando FTS5
- Se sincronizan automáticamente cambios de `documents.content_text` a `documents_fts`
- Soporta búsqueda de palabras clave con ranking de relevancia

**And** existe endpoint de búsqueda:
**GET /api/knowledge/search**
- Headers: `Authorization: Bearer {token}`
- Query params: `?q=reembolso&limit=10&offset=0`
- Response 200:
  ```json
  {
    "query": "reembolso",
    "total_results": 5,
    "results": [
      {
        "document_id": 3,
        "title": "Procedimiento de Reembolsos",
        "category": "Procedimientos Operativos",
        "relevance_score": 0.95,
        "snippet": "...proceso de reembolso especial requiere..."
      }
    ]
  }
  ```

**And** la búsqueda soporta:
- Palabras clave individuales: `?q=vacaciones`
- Frases exactas: `?q="políticas de RRHH"`
- Operadores booleanos: `?q=reembolso AND urgente`
- Ranking por relevancia (TF-IDF implícito en FTS5)

**And** los resultados incluyen:
- Snippet de contexto (100 caracteres alrededor de match)
- Score de relevancia normalizado (0.0 - 1.0)
- Paginación (limit/offset)

**Prerequisites:** Story 2.3 completada

**Technical Notes:**
- SQLite FTS5 está disponible desde SQLite 3.9.0+ (verificar versión)
- Crear triggers para sincronizar `documents` → `documents_fts` automáticamente
- Configurar tokenizer en español: `tokenize='unicode61 remove_diacritics 2'`
- Limitar snippet a 150 caracteres (performance)
- Implementar en `backend/app/services/search_service.py`
- Agregar tests: búsqueda por palabra clave, búsqueda por frase, resultados vacíos, paginación

---

### Story 2.5: API de Consulta y Listado de Documentos

Como usuario (admin o user),
Quiero consultar la lista de documentos disponibles con filtros,
Para explorar el repositorio de conocimiento y encontrar información relevante.

**Acceptance Criteria:**

**Given** que estoy autenticado (Story 1.3)
**When** implemento endpoints de consulta de documentos
**Then** existen los siguientes endpoints:

**GET /api/knowledge/documents**
- Headers: `Authorization: Bearer {token}`
- Query params (todos opcionales):
  - `?category=Políticas RRHH` (filtrar por categoría)
  - `?limit=20&offset=0` (paginación)
  - `?sort_by=upload_date&order=desc` (ordenamiento)
- Response 200:
  ```json
  {
    "total": 50,
    "limit": 20,
    "offset": 0,
    "documents": [
      {
        "id": 5,
        "title": "Manual de Vacaciones",
        "description": "Políticas de solicitud de vacaciones",
        "category": "Políticas RRHH",
        "file_type": "pdf",
        "file_size_bytes": 524288,
        "upload_date": "2025-11-01T10:00:00Z",
        "uploaded_by": "admin"
      }
    ]
  }
  ```

**GET /api/knowledge/documents/{document_id}**
- Headers: `Authorization: Bearer {token}`
- Response 200:
  ```json
  {
    "id": 5,
    "title": "Manual de Vacaciones",
    "description": "...",
    "category": "Políticas RRHH",
    "file_type": "pdf",
    "file_size_bytes": 524288,
    "file_path": "/uploads/manual_vacaciones.pdf",
    "upload_date": "2025-11-01T10:00:00Z",
    "uploaded_by": "admin",
    "is_indexed": true,
    "indexed_at": "2025-11-01T10:01:00Z"
  }
  ```
- Response 404 si documento no existe

**GET /api/knowledge/categories**
- Headers: `Authorization: Bearer {token}`
- Response 200:
  ```json
  {
    "categories": [
      {"name": "Políticas RRHH", "document_count": 15},
      {"name": "Procedimientos Operativos", "document_count": 23}
    ]
  }
  ```

**And** la paginación por defecto es: `limit=20, offset=0`

**And** el ordenamiento soporta: `upload_date`, `title`, `file_size_bytes` (order: `asc` o `desc`)

**Prerequisites:** Story 2.4 completada

**Technical Notes:**
- Implementar filtros con query builder de SQLModel (evitar SQL injection)
- Usuario 'user' puede listar documentos (solo lectura)
- Retornar `uploaded_by` como username (no user_id)
- Implementar en `backend/app/routes/knowledge.py`
- Agregar tests: listado sin filtros, filtrado por categoría, paginación, ordenamiento

---

### Story 2.6: Descarga y Visualización de Documentos

Como usuario (admin o user),
Quiero descargar y visualizar documentos del repositorio,
Para acceder al contenido completo y validar información.

**Acceptance Criteria:**

**Given** que estoy autenticado (Story 1.3)
**When** implemento endpoint de descarga
**Then** existe el endpoint:

**GET /api/knowledge/documents/{document_id}/download**
- Headers: `Authorization: Bearer {token}`
- Response 200:
  - Content-Type: `application/pdf` o `text/plain` según `file_type`
  - Content-Disposition: `attachment; filename="manual_vacaciones.pdf"`
  - Body: contenido binario del archivo

**And** si el documento no existe:
- Response 404: `{"error": {"code": "DOCUMENT_NOT_FOUND", "message": "El documento solicitado no existe"}}`

**And** si el usuario no está autenticado:
- Response 401: error de autenticación

**And** la descarga se registra en `audit_logs`:
- Evento: "DOCUMENT_DOWNLOADED"
- Detalles: `{"document_id": 5, "user_id": 2, "timestamp": "..."}`

**And** existe endpoint de previsualización (opcional para MVP):
**GET /api/knowledge/documents/{document_id}/preview**
- Retorna primeros 500 caracteres de `content_text`
- Usado para mostrar preview en UI sin descargar archivo completo

**Prerequisites:** Story 2.5 completada

**Technical Notes:**
- Usar `flask.send_file()` o equivalente en FastAPI para servir archivos
- Validar que `file_path` existe en filesystem antes de servir (manejar archivos huérfanos)
- Sanitizar `filename` en header Content-Disposition (evitar inyección de headers)
- Considerar rate limiting (evitar descarga masiva automatizada)
- Implementar en `backend/app/routes/knowledge.py`
- Agregar tests: descarga exitosa PDF, descarga exitosa TXT, documento no existe, sin autenticación

---

### Story 2.7: Eliminación de Documentos con Auditoría

Como administrador,
Quiero eliminar documentos del repositorio de manera segura con trazabilidad,
Para mantener el repositorio actualizado y cumplir con políticas de retención de datos.

**Acceptance Criteria:**

**Given** que estoy autenticado como administrador (rol 'admin')
**When** implemento endpoint de eliminación
**Then** existe el endpoint:

**DELETE /api/knowledge/documents/{document_id}**
- Headers: `Authorization: Bearer {admin_token}`
- Response 200:
  ```json
  {
    "message": "Documento eliminado exitosamente",
    "document_id": 5,
    "title": "Manual de Vacaciones"
  }
  ```

**And** al eliminar el documento:
1. Se elimina archivo físico del directorio `/uploads/`
2. Se elimina registro de tabla `documents`
3. Se elimina entrada correspondiente en `documents_fts` (índice full-text)
4. Se registra en `audit_logs`:
   - Evento: "DOCUMENT_DELETED"
   - Detalles: `{"document_id": 5, "title": "Manual de Vacaciones", "deleted_by": 1}`

**And** si el usuario no es administrador:
- Response 403: `{"error": {"code": "FORBIDDEN", "message": "Solo administradores pueden eliminar documentos"}}`

**And** si el documento no existe:
- Response 404: `{"error": {"code": "DOCUMENT_NOT_FOUND", "message": "El documento solicitado no existe"}}`

**And** si el archivo físico no existe (huérfano):
- Eliminar registro de base de datos de todos modos
- Loggear warning: "Archivo físico no encontrado durante eliminación"
- Retornar Response 200 (operación exitosa desde perspectiva del usuario)

**And** en el frontend (opcional para esta historia):
- Mostrar confirmación: "¿Estás seguro de eliminar '{title}'?" antes de enviar DELETE
- Mostrar notificación de éxito tras eliminación

**Prerequisites:** Story 2.6 completada

**Technical Notes:**
- Usar `os.remove()` para eliminar archivo físico (manejar exception si no existe)
- Implementar transacción de base de datos (rollback si falla eliminación de archivo)
- Considerar "soft delete" como alternativa: marcar `is_deleted=True` en lugar de eliminar físicamente (mejor para auditoría)
- Implementar en `backend/app/routes/knowledge.py`
- Agregar tests: eliminación exitosa, sin permisos (user intenta eliminar), documento no existe, manejo de archivo huérfano

---

## Epic 3: Motor de IA Generativa y Consultas en Lenguaje Natural

**Objetivo:** Implementar el motor de IA generativa con técnica RAG (Retrieval-Augmented Generation) que permite a los usuarios consultar el conocimiento corporativo en lenguaje natural y recibir respuestas contextualizadas y precisas.

**Valor de Negocio:** Esta es la "magia" del producto. Transforma el conocimiento tácito en explícito mediante IA conversacional que responde en <2 segundos con información verificable y trazable.

**Alineación con PRD:** RF2 (Consultas en Lenguaje Natural), RNF2 (Rendimiento <2s), Sección "Innovation & Novel Patterns" (RAG con cumplimiento normativo).

---

### Story 3.1: Configuración e Integración de Llama 3.1 Local vía Ollama

Como desarrollador backend,
Quiero integrar un modelo de lenguaje local (Llama 3.1) ejecutándose en el servidor,
Para que el sistema genere respuestas de IA sin dependencia de APIs externas y con total soberanía de datos.

**Acceptance Criteria:**

**Given** que necesito un motor de IA generativa local
**When** configuro Ollama y Llama 3.1
**Then** el servidor tiene Ollama instalado y ejecutándose:
- Ollama versión ≥0.1.20
- Servicio corriendo en `http://localhost:11434`
- Modelo `llama3.1:8b-instruct-q4_K_M` descargado (tamaño ~4.7GB)

**And** se valida disponibilidad del modelo:
```bash
$ ollama list
NAME                          SIZE    MODIFIED
llama3.1:8b-instruct-q4_K_M  4.7GB   2 hours ago
```

**And** existe módulo `backend/app/services/llm_service.py`:
```python
import requests
from typing import Dict

class LlamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama3.1:8b-instruct-q4_K_M"

    def generate_response(
        self,
        prompt: str,
        context: str = "",
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> Dict:
        """
        Genera respuesta usando Llama 3.1 local.

        Returns: {"response": str, "tokens_generated": int, "generation_time_ms": float}
        """
        full_prompt = self._build_rag_prompt(context, prompt)

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "temperature": temperature,
                "num_predict": max_tokens,
                "stream": False
            },
            timeout=30
        )

        if response.status_code != 200:
            raise LLMServiceException(f"Ollama error: {response.text}")

        result = response.json()
        return {
            "response": result["response"],
            "tokens_generated": result.get("eval_count", 0),
            "generation_time_ms": result.get("total_duration", 0) / 1e6
        }

    def _build_rag_prompt(self, context: str, query: str) -> str:
        """Construye prompt optimizado para RAG con Llama 3.1"""
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Eres un asistente de conocimiento corporativo. Responde preguntas basándote EXCLUSIVAMENTE en el contexto proporcionado.
Si la información no está en el contexto, responde: "No encuentro información sobre eso en la base de conocimiento."

<|eot_id|><|start_header_id|>user<|end_header_id|>

**Contexto:**
{context}

**Pregunta:** {query}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    def health_check(self) -> bool:
        """Verifica que Ollama esté disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
```

**And** se implementa endpoint de health check:
**GET /api/ia/health**
- Verifica que Ollama esté corriendo
- Verifica que modelo Llama 3.1 esté disponible
- Response 200: `{"status": "ok", "model": "llama3.1:8b-instruct-q4_K_M", "ollama_version": "0.1.20"}`
- Response 503: `{"status": "unavailable", "error": "Ollama service not running"}`

**And** se maneja gracefully si Ollama no está disponible:
- Al iniciar backend: loggea WARNING si Ollama no responde
- En consultas: retorna error claro "Servicio de IA temporalmente no disponible"
- No bloquea inicio de la aplicación (otras funcionalidades siguen operativas)

**And** configuración en `.env`:
```
# Local LLM Service
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500
LLM_CONTEXT_SIZE=8192
```

**And** loggea métricas de inferencia:
- Tiempo de generación (ms)
- Tokens generados
- Errores de conexión con Ollama

**And** existen tests:
```python
def test_llama_service_generates_response():
    service = LlamaService()
    result = service.generate_response(
        prompt="¿Qué es RAG?",
        context="RAG significa Retrieval-Augmented Generation..."
    )
    assert "response" in result
    assert len(result["response"]) > 0
    assert result["generation_time_ms"] < 10000  # <10s

def test_llama_service_health_check():
    service = LlamaService()
    assert service.health_check() == True

def test_llama_service_handles_ollama_down():
    service = LlamaService(base_url="http://localhost:9999")  # puerto incorrecto
    with pytest.raises(LLMServiceException):
        service.generate_response("test", "")
```

**Prerequisites:** Story 1.5 (variables de entorno) completada

**Technical Notes:**
- **Instalación Ollama:**
  - Linux/Mac: `curl https://ollama.ai/install.sh | sh`
  - Windows: Descargar instalador desde ollama.ai
- **Pull modelo:** `ollama pull llama3.1:8b-instruct-q4_K_M` (~4.7GB download)
- **Requerimientos hardware:**
  - Mínimo: 8GB RAM (modelo cuantizado q4)
  - Recomendado: 16GB RAM + GPU (NVIDIA con CUDA)
  - Rendimiento CPU: ~10-15 tokens/s
  - Rendimiento GPU: ~40-60 tokens/s
- **Formato de prompt:** Usar template Llama 3.1 oficial con tags `<|start_header_id|>`
- **Alternativa a Ollama:** llama.cpp si necesitas más control fino (más complejo)
- **Documentar en:** `docs/setup-llama-local.md`
- **Fallback:** Si rendimiento es insuficiente, considerar modelo más pequeño: `llama3.1:3b` o `phi3:mini`

---

### Story 3.2: Implementación de Retrieval (Búsqueda de Documentos Relevantes)

Como sistema,
Quiero recuperar los documentos más relevantes del repositorio para una consulta de usuario,
Para proporcionar contexto preciso al LLM y evitar alucinaciones.

**Acceptance Criteria:**

**Given** que el sistema tiene documentos indexados (Epic 2, Story 2.4)
**When** implemento el servicio de recuperación (Retrieval)
**Then** existe función `retrieve_relevant_documents(query: str, top_k: int = 3) -> List[Document]`

**And** la función:
1. Toma la consulta del usuario (ej. "¿Cómo solicito vacaciones?")
2. Busca en el índice full-text (SQLite FTS5) documentos que contengan palabras clave
3. Rankea documentos por relevancia (score de FTS5)
4. Retorna top K documentos más relevantes (por defecto K=3)

**And** cada documento retornado incluye:
- `document_id`
- `title`
- `category`
- `content_snippet` (fragmento relevante, máximo 1000 caracteres)
- `relevance_score` (0.0 - 1.0)

**And** si no encuentra documentos relevantes (score < 0.1):
- Retorna lista vacía
- Loggea evento: "No se encontraron documentos relevantes para: {query}"

**And** optimiza la búsqueda:
- Expande consulta con sinónimos (opcional para MVP)
  - Ej. "vacaciones" → también buscar "permiso", "ausencia"
- Normaliza texto: lowercase, eliminar acentos
- Filtra stopwords en español ("el", "la", "de", "en")

**And** existe endpoint de prueba (útil para debugging):
**POST /api/ia/retrieve** (solo admin)
- Body: `{"query": "reembolso urgente"}`
- Response:
  ```json
  {
    "query": "reembolso urgente",
    "documents_found": 3,
    "documents": [
      {
        "document_id": 5,
        "title": "Procedimiento Reembolsos",
        "relevance_score": 0.92,
        "snippet": "...reembolso urgente requiere aprobación..."
      }
    ]
  }
  ```

**Prerequisites:** Epic 2 completada (especialmente Story 2.4 indexación)

**Technical Notes:**
- Reusar servicio de búsqueda de Story 2.4 (`search_service.py`)
- Configurar `top_k` como variable de entorno `RAG_TOP_K_DOCUMENTS=3`
- Considerar búsqueda híbrida: keyword (FTS5) + semantic (embeddings) - semantic es Growth Feature
- Para MVP: solo keyword search es suficiente
- Limitar snippet a contexto relevante (100 caracteres antes/después del match)
- Implementar en `backend/app/services/retrieval_service.py`
- Agregar tests: búsqueda exitosa, sin resultados, múltiples documentos

---

### Story 3.3: Implementación de RAG (Retrieval-Augmented Generation)

Como sistema,
Quiero combinar recuperación de documentos con generación de respuestas por LLM,
Para proporcionar respuestas precisas fundamentadas en conocimiento corporativo verificable.

**Acceptance Criteria:**

**Given** que tengo integración con LLM (Story 3.1) y servicio de retrieval (Story 3.2)
**When** implemento el pipeline RAG completo
**Then** existe función `rag_query(user_query: str, user_id: int) -> dict`:

**Pipeline RAG:**
1. **Retrieval:** Recupera top 3 documentos relevantes usando `retrieve_relevant_documents(user_query)`
2. **Context Construction:** Combina snippets de documentos en contexto:
   ```
   Documento 1 (Procedimiento Reembolsos):
   ...reembolso urgente requiere aprobación de supervisor...

   Documento 2 (Políticas RRHH):
   ...reembolsos se procesan en 5 días hábiles...
   ```
3. **Augmentation:** Construye prompt aumentado con contexto
4. **Generation:** Envía prompt + contexto al LLM usando `generate_response()`
5. **Response Formatting:** Formatea respuesta con referencias a fuentes

**And** retorna objeto:
```python
{
  "answer": "Para solicitar un reembolso urgente, necesitas aprobación de tu supervisor según el Procedimiento de Reembolsos...",
  "sources": [
    {"document_id": 5, "title": "Procedimiento Reembolsos", "relevance_score": 0.92},
    {"document_id": 7, "title": "Políticas RRHH", "relevance_score": 0.78}
  ],
  "response_time_ms": 1850,
  "documents_retrieved": 3
}
```

**And** si no encuentra documentos relevantes:
- NO envía request al LLM (ahorro de costos)
- Retorna mensaje:
  ```python
  {
    "answer": "No encontré información específica sobre tu consulta en la base de conocimiento. ¿Podrías reformular tu pregunta o usar palabras clave diferentes?",
    "sources": [],
    "response_time_ms": 50,
    "documents_retrieved": 0
  }
  ```

**And** incluye disclaimer en respuestas generadas:
- Agrega al final de `answer`: "\n\n*Nota: Esta respuesta fue generada por IA. Verifica con tu supervisor si tienes dudas.*"

**And** loggea métricas:
- Tiempo total del pipeline (retrieval + generation)
- Número de documentos recuperados
- Score promedio de relevancia
- Tokens utilizados por el LLM

**Prerequisites:** Stories 3.1 y 3.2 completadas

**Technical Notes:**
- Implementar en `backend/app/services/rag_service.py`
- Medir tiempos de cada fase del pipeline (profiling)
- Limitar contexto total a ~2000 caracteres (evitar exceder límites de tokens del LLM)
- Si contexto excede límite: priorizar documentos con mayor relevance_score
- Implementar caché de respuestas: consultas idénticas en <5 minutos retornan cached response
- Agregar tests: pipeline completo exitoso, sin documentos relevantes, timeout del LLM

---

### Story 3.4: API de Consulta Conversacional para Usuarios

Como usuario (admin o user),
Quiero consultar el conocimiento corporativo en lenguaje natural mediante una API,
Para obtener respuestas rápidas y precisas fundamentadas en documentos verificables.

**Acceptance Criteria:**

**Given** que estoy autenticado (Story 1.3)
**When** implemento el endpoint de consulta IA
**Then** existe el endpoint:

**POST /api/ia/query**
- Headers: `Authorization: Bearer {token}`
- Body:
  ```json
  {
    "query": "¿Cómo proceso un reembolso urgente?",
    "context_mode": "general"  // opcional: "general" o "specific"
  }
  ```
- Response 200:
  ```json
  {
    "query": "¿Cómo proceso un reembolso urgente?",
    "answer": "Para procesar un reembolso urgente, necesitas...",
    "sources": [
      {
        "document_id": 5,
        "title": "Procedimiento Reembolsos",
        "category": "Procedimientos Operativos",
        "relevance_score": 0.92
      }
    ],
    "response_time_ms": 1850,
    "timestamp": "2025-11-10T10:30:00Z"
  }
  ```

**And** valida la entrada:
- `query` es requerido (mínimo 10 caracteres, máximo 500)
- Si `query` es muy corto: Response 400 "La consulta debe tener al menos 10 caracteres"
- Si `query` es muy largo: Response 400 "La consulta no puede exceder 500 caracteres"

**And** ejecuta el pipeline RAG:
- Llama a `rag_query(user_query, user_id)` de Story 3.3
- Retorna respuesta formateada

**And** registra en base de datos:
- Crea tabla `queries` si no existe:
  - `id`, `user_id`, `query_text`, `answer_text`, `response_time_ms`, `timestamp`, `sources_json`
- Inserta registro de cada consulta (útil para análisis y mejora continua)

**And** registra en audit logs:
- Evento: "AI_QUERY"
- Detalles: `{"user_id": 2, "query": "...", "response_time_ms": 1850, "sources_count": 3}`

**And** maneja errores del LLM:
- Si LLM falla (Story 3.1 lanza exception):
  - Response 503: `{"error": {"code": "AI_SERVICE_UNAVAILABLE", "message": "El servicio de IA no está disponible temporalmente. Intenta nuevamente."}}`
- Si timeout:
  - Response 504: `{"error": {"code": "AI_TIMEOUT", "message": "La consulta tardó demasiado. Intenta con una pregunta más específica."}}`

**And** implementa rate limiting básico:
- Máximo 10 consultas por minuto por usuario
- Si excede: Response 429 "Demasiadas consultas. Espera un momento antes de intentar nuevamente."

**Prerequisites:** Story 3.3 completada

**Technical Notes:**
- Implementar en `backend/app/routes/ia.py`
- Usar decorador `@rate_limit(max_requests=10, window_seconds=60)` personalizado
- Almacenar `sources_json` como JSON serializado en tabla queries
- Considerar almacenar hash de query para detectar duplicados exactos (caché)
- Agregar tests: consulta exitosa, query muy corta, query muy larga, rate limit excedido, LLM no disponible

---

### Story 3.5: Interfaz Conversacional (Estilo Chat) en Frontend

Como usuario,
Quiero una interfaz de chat intuitiva para consultar el conocimiento,
Para interactuar naturalmente con la IA y ver el historial de mis consultas.

**Acceptance Criteria:**

**Given** que estoy autenticado y en el dashboard (Story 1.4)
**When** implemento la interfaz de chat
**Then** existe una página `/chat` accesible desde el menú principal

**And** la interfaz contiene:
- **Área de conversación:** Panel scrolleable que muestra mensajes usuario/IA alternados
- **Input de consulta:**
  - Text area con placeholder: "Escribe tu pregunta aquí... (ej. ¿Cómo solicito vacaciones?)"
  - Contador de caracteres: "45 / 500"
  - Botón "Enviar" (o Enter para enviar)
- **Indicador de estado:**
  - Mientras IA procesa: muestra "IA está pensando..." con animación de puntos
  - Estimación de tiempo: "~2 segundos"

**And** el flujo de interacción:
1. Usuario escribe consulta y presiona "Enviar"
2. Consulta se agrega al área de conversación (burbuja azul a la derecha)
3. Aparece indicador "IA está pensando..."
4. Se envía POST a `/api/ia/query`
5. Respuesta de IA aparece en burbuja gris a la izquierda con:
   - Texto de la respuesta
   - Sección "Fuentes consultadas" expandible con links a documentos
   - Iconos de feedback: 👍 👎
   - Timestamp: "Hace 2 minutos"

**And** muestra fuentes de manera visual:
```
📄 Fuentes consultadas (3):
  • Procedimiento Reembolsos (Relevancia: 92%)
  • Políticas RRHH (Relevancia: 78%)
  • Manual de Procedimientos (Relevancia: 65%)
```
- Click en fuente → abre vista previa del documento o descarga

**And** maneja errores de manera clara:
- Si error 503 (IA no disponible): Muestra mensaje "⚠️ El servicio de IA está temporalmente no disponible. Intenta en unos minutos."
- Si error 504 (timeout): "⏱️ La consulta tardó demasiado. Intenta con una pregunta más específica."
- Si error 429 (rate limit): "🚫 Has realizado muchas consultas. Espera un momento antes de continuar."

**And** el historial de conversación:
- Persiste durante la sesión (almacenado en state del frontend)
- Se limpia al cerrar sesión o refrescar página (opcional para MVP: guardar en localStorage)
- Botón "Limpiar conversación" visible

**And** diseño responsive:
- Funciona en desktop (1920x1080) y tablet (1024x768)
- En mobile (opcional para MVP): interfaz adaptada

**Prerequisites:** Story 3.4 completada

**Technical Notes:**
- Frontend: React 18 + TypeScript - crear componente `ChatInterface.tsx` con shadcn/ui
- Usar Axios para HTTP requests con interceptors (JWT token automático)
- Implementar scroll automático al último mensaje (auto-scroll down)
- Formatear respuestas con markdown básico (negritas, listas, párrafos)
- Usar biblioteca como `marked.js` o `react-markdown` para renderizar
- Agregar animación suave de aparición de mensajes (fade-in)
- CSS: usar framework como Tailwind o custom CSS para burbujas de chat

---

### Story 3.6: Optimización de Rendimiento y Caché de Respuestas

Como sistema,
Quiero optimizar el tiempo de respuesta del motor de IA,
Para cumplir con el requerimiento no funcional de respuestas en <2 segundos.

**Acceptance Criteria:**

**Given** que el pipeline RAG está operativo (Story 3.3)
**When** implemento optimizaciones de rendimiento
**Then** el sistema alcanza las siguientes métricas:

**Métricas Objetivo:**
- **P50 (mediana):** <1.5 segundos
- **P95 (percentil 95):** <2.5 segundos
- **P99 (percentil 99):** <5 segundos

**And** se implementan las siguientes optimizaciones:

**1. Caché de Respuestas:**
- Consultas idénticas (mismo texto) retornan respuesta cacheada
- TTL (Time To Live): 5 minutos
- Implementar con dict en memoria: `{query_hash: (response, timestamp)}`
- Limitar caché a 100 consultas más recientes (LRU - Least Recently Used)

**2. Caché de Retrieval:**
- Búsquedas idénticas retornan documentos cacheados
- TTL: 10 minutos (documentos cambian menos frecuentemente)

**3. Modelo Pre-cargado en Memoria:**
- Mantener Llama 3.1 cargado en memoria (evita latencia de inicialización)
- Ollama mantiene modelo warm por defecto tras primera consulta
- Considerar `ollama run llama3.1:8b-instruct-q4_K_M` al iniciar servidor

**4. Paralelización:**
- Si recupera múltiples documentos: procesar extracción de snippets en paralelo (threading)

**5. Timeouts Configurables:**
- Timeout de búsqueda: 500ms (si excede, retorna parciales)
- Timeout de inferencia local: 10 segundos (luego lanza exception)

**6. Context Pruning:**
- Limitar contexto a máximo 2000 tokens más relevantes
- Reduce tiempo de inferencia (menos tokens a procesar)

**And** existe endpoint de métricas (solo admin):
**GET /api/ia/metrics**
- Response:
  ```json
  {
    "total_queries": 150,
    "avg_response_time_ms": 1650,
    "p50_ms": 1500,
    "p95_ms": 2300,
    "p99_ms": 4200,
    "cache_hit_rate": 0.35,  // 35% de consultas servidas desde caché
    "avg_documents_retrieved": 2.8
  }
  ```

**And** se loggean métricas detalladas:
- Tabla `performance_metrics`:
  - `query_id`, `retrieval_time_ms`, `llm_time_ms`, `total_time_ms`, `cache_hit`, `timestamp`
- Dashboard de admin muestra gráficas de rendimiento (Growth Feature, en MVP solo endpoint JSON)

**And** si rendimiento <2s no es alcanzable:
- Documentar en `docs/limitaciones-tecnicas.md`:
  - Causas: velocidad de inferencia local limitada por CPU, memoria RAM disponible
  - Mediciones reales obtenidas (tokens/segundo en hardware de laboratorio)
  - Propuestas de mejora: GPU dedicada (NVIDIA), modelo más pequeño (3b), cuantización más agresiva (q3)

**Prerequisites:** Story 3.5 completada

**Technical Notes:**
- Implementar caché con `functools.lru_cache` (Python built-in) o `cachetools` (más control)
- Medir tiempos con `time.perf_counter()` (alta precisión)
- Almacenar métricas en tabla para análisis posterior
- Considerar usar Redis para caché distribuido (Growth Feature, no MVP)
- Implementar en `backend/app/services/performance_service.py`
- Agregar tests: cache hit, cache miss, métricas calculadas correctamente

---

## Epic 4: Generación Automática de Contenido Formativo

**Objetivo:** Extender las capacidades de la IA para generar automáticamente material de capacitación personalizado: resúmenes, quizzes de evaluación y learning paths. Este es el diferenciador clave que transforma el sistema de "asistente reactivo" a "generador proactivo de capacitación".

**Valor de Negocio:** No solo responder preguntas, sino CREAR contenido formativo que acelera el aprendizaje organizacional y permite capacitación personalizada a escala.

**Alineación con PRD:** RF4 (Generación de Contenido Formativo), Sección "Innovation & Novel Patterns" (Generación automática de contenido formativo).

---

### Story 4.1: Generación Automática de Resúmenes de Documentos

Como usuario (admin o user),
Quiero generar automáticamente un resumen ejecutivo de cualquier documento del repositorio,
Para comprender rápidamente los puntos clave sin leer el documento completo.

**Acceptance Criteria:**

**Given** que estoy autenticado y tengo acceso a un documento (Epic 2)
**When** implemento la funcionalidad de generación de resúmenes
**Then** existe el endpoint:

**POST /api/ia/generate/summary**
- Headers: `Authorization: Bearer {token}`
- Body:
  ```json
  {
    "document_id": 5,
    "summary_length": "short"  // opciones: "short" (150 palabras), "medium" (300 palabras), "long" (500 palabras)
  }
  ```
- Response 200:
  ```json
  {
    "document_id": 5,
    "document_title": "Manual de Procedimientos RRHH",
    "summary": "Este manual establece los procedimientos para...\n\nPuntos clave:\n- Solicitud de vacaciones requiere 15 días de anticipación\n- Permisos médicos se reportan dentro de 24 horas\n- Evaluaciones de desempeño se realizan semestralmente",
    "summary_length": "short",
    "word_count": 145,
    "generated_at": "2025-11-10T10:30:00Z",
    "generation_time_ms": 3200
  }
  ```

**And** el proceso de generación:
1. Recupera el documento de la base de datos por `document_id`
2. Extrae `content_text` del documento (hasta 10,000 caracteres)
3. Construye prompt para el LLM:
   ```
   Eres un asistente experto en resumir documentos corporativos.

   Genera un resumen ejecutivo del siguiente documento en español.
   Incluye los puntos clave más importantes.
   Longitud objetivo: {summary_length_words} palabras.

   DOCUMENTO:
   {document_content}

   RESUMEN:
   ```
4. Envía al LLM con parámetros:
   - `temperature=0.5` (balance creatividad/determinismo)
   - `max_tokens` según longitud: short=200, medium=400, long=600
5. Retorna resumen generado

**And** maneja casos especiales:
- **Documento no existe:** Response 404 "Documento no encontrado"
- **Documento sin contenido extraído:** Response 400 "El documento no tiene contenido procesado. Intenta más tarde."
- **Documento muy corto (<100 palabras):** Response 400 "El documento es demasiado corto para resumir. Léelo directamente."
- **LLM falla:** Response 503 "Servicio de IA no disponible"

**And** almacena resumen generado:
- Crea tabla `generated_content`:
  - `id`, `document_id`, `user_id`, `content_type` ('summary'/'quiz'/'learning_path'), `content_json`, `created_at`
- Permite reusar resúmenes: si mismo documento + misma longitud → retorna cached (válido 24 horas)

**And** incluye disclaimer:
- Agrega al final del resumen: "\n\n*Resumen generado automáticamente por IA. Revisa el documento completo para detalles precisos.*"

**Prerequisites:** Epic 3 completada (especialmente Story 3.1 integración LLM)

**Technical Notes:**
- Implementar en `backend/app/routes/ia.py`
- Reusar servicio de LLM de Story 3.1 (`ai_service.py`)
- Limitar contenido de entrada al LLM a 10,000 caracteres (evitar exceder límite de tokens)
- Si documento >10,000 chars: usar primeros 10,000 + advertencia en resumen "Nota: Resumen basado en sección inicial del documento"
- Agregar tests: generación exitosa short/medium/long, documento no existe, documento sin contenido, caché

---

### Story 4.2: Generación Automática de Quizzes de Evaluación

Como administrador,
Quiero generar automáticamente quizzes de opción múltiple basados en documentos,
Para evaluar la comprensión de los empleados sobre el conocimiento corporativo.

**Acceptance Criteria:**

**Given** que estoy autenticado como administrador
**When** implemento la funcionalidad de generación de quizzes
**Then** existe el endpoint:

**POST /api/ia/generate/quiz**
- Headers: `Authorization: Bearer {admin_token}`
- Body:
  ```json
  {
    "document_id": 5,
    "num_questions": 5,  // opciones: 5, 10, 15
    "difficulty": "medium"  // opciones: "easy", "medium", "hard"
  }
  ```
- Response 200:
  ```json
  {
    "document_id": 5,
    "document_title": "Manual de Procedimientos RRHH",
    "quiz": {
      "title": "Quiz: Manual de Procedimientos RRHH",
      "num_questions": 5,
      "difficulty": "medium",
      "questions": [
        {
          "question_number": 1,
          "question": "¿Con cuántos días de anticipación se debe solicitar vacaciones?",
          "options": [
            "A) 5 días",
            "B) 10 días",
            "C) 15 días",
            "D) 30 días"
          ],
          "correct_answer": "C",
          "explanation": "Según el manual, las vacaciones requieren 15 días de anticipación para aprobación."
        }
      ]
    },
    "generated_at": "2025-11-10T10:30:00Z",
    "generation_time_ms": 8500
  }
  ```

**And** el proceso de generación:
1. Recupera documento por `document_id`
2. Extrae `content_text`
3. Construye prompt para el LLM:
   ```
   Eres un experto en evaluación educativa.

   Genera un quiz de opción múltiple basado en el siguiente documento.

   Requisitos:
   - {num_questions} preguntas
   - Dificultad: {difficulty}
   - 4 opciones por pregunta (A, B, C, D)
   - Solo 1 opción correcta por pregunta
   - Incluye explicación breve de la respuesta correcta
   - Preguntas claras y específicas sobre el contenido

   DOCUMENTO:
   {document_content}

   Formato de respuesta JSON:
   {
     "questions": [
       {
         "question": "...",
         "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
         "correct_answer": "C",
         "explanation": "..."
       }
     ]
   }
   ```
4. Envía al LLM con prompt estructurado para generar JSON
5. Parsea JSON retornado y valida estructura (usar try/except para manejo robusto)

**And** valida el quiz generado:
- Cada pregunta tiene exactamente 4 opciones
- `correct_answer` está en ["A", "B", "C", "D"]
- Todas las preguntas tienen explicación
- Si validación falla: reintenta generación 1 vez, si falla nuevamente → error 500

**And** maneja restricciones:
- **Solo administradores** pueden generar quizzes (usuarios normales: 403 Forbidden)
- Documento debe tener >500 palabras (si no: 400 "Documento muy corto para generar quiz significativo")
- `num_questions` no puede exceder 1 pregunta por cada 100 palabras del documento

**And** almacena quiz generado:
- Guarda en tabla `generated_content` con `content_type='quiz'`
- `content_json` almacena estructura completa del quiz

**And** existe endpoint para recuperar quizzes generados:
**GET /api/ia/generated/quizzes?document_id=5**
- Lista quizzes previamente generados para un documento

**Prerequisites:** Story 4.1 completada

**Technical Notes:**
- Implementar en `backend/app/routes/ia.py`
- Usar Llama 3.1 con prompt estructurado y formato JSON explícito
- Parsear JSON con manejo robusto de errores (try/except json.JSONDecodeError)
- Tiempo de generación estimado: ~2-3 segundos por pregunta (5 preguntas = ~10-15 segundos)
- Si LLM no retorna JSON válido: intentar extraer con regex como fallback o solicitar regeneración
- Agregar tests: generación exitosa 5/10/15 preguntas, validación de estructura, solo admin
- Considerar agregar en prompt: "Responde ÚNICAMENTE con JSON válido, sin texto adicional"

---

### Story 4.3: Interfaz de Visualización y Respuesta de Quizzes

Como usuario,
Quiero responder interactivamente a quizzes generados y ver mi puntuación,
Para evaluar mi comprensión del conocimiento corporativo.

**Acceptance Criteria:**

**Given** que existe un quiz generado (Story 4.2)
**When** implemento la interfaz de quiz
**Then** existe una página `/quiz/{quiz_id}` accesible para usuarios autenticados

**And** la página muestra:
- **Encabezado:** Título del quiz + documento origen
- **Indicador de progreso:** "Pregunta 3 de 10"
- **Pregunta actual:** Texto de la pregunta claramente visible
- **Opciones:** Radio buttons para las 4 opciones (A, B, C, D)
- **Botones de navegación:**
  - "Siguiente" (si no es última pregunta)
  - "Finalizar Quiz" (si es última pregunta)
  - "Anterior" (permite revisar respuestas previas)

**And** el flujo de respuesta:
1. Usuario selecciona una opción (radio button)
2. Click "Siguiente" → guarda respuesta localmente (frontend state)
3. Carga siguiente pregunta
4. Repite hasta última pregunta
5. Click "Finalizar Quiz" → envía todas las respuestas al backend

**And** existe endpoint para evaluar quiz:
**POST /api/ia/quiz/{quiz_id}/submit**
- Headers: `Authorization: Bearer {token}`
- Body:
  ```json
  {
    "answers": {
      "1": "C",
      "2": "A",
      "3": "B",
      "4": "C",
      "5": "D"
    }
  }
  ```
- Response 200:
  ```json
  {
    "quiz_id": 12,
    "score": 4,
    "total_questions": 5,
    "percentage": 80,
    "passed": true,  // si score >= 70%
    "results": [
      {
        "question_number": 1,
        "user_answer": "C",
        "correct_answer": "C",
        "is_correct": true,
        "explanation": "..."
      },
      {
        "question_number": 2,
        "user_answer": "A",
        "correct_answer": "B",
        "is_correct": false,
        "explanation": "..."
      }
    ]
  }
  ```

**And** la página de resultados muestra:
- **Puntuación:** "4 de 5 correctas (80%)"
- **Badge visual:** "¡Aprobado!" (verde) o "Necesitas mejorar" (amarillo) si <70%
- **Desglose por pregunta:**
  - ✅ Pregunta 1: Correcta
  - ❌ Pregunta 2: Incorrecta (Tu respuesta: A, Correcta: B)
  - Explicación de cada respuesta
- **Botones:**
  - "Reintentar Quiz"
  - "Volver al Documento"
  - "Ver otros Quizzes"

**And** almacena resultados:
- Tabla `quiz_attempts`:
  - `id`, `quiz_id`, `user_id`, `answers_json`, `score`, `total_questions`, `percentage`, `timestamp`
- Permite rastrear progreso de aprendizaje de usuarios

**Prerequisites:** Story 4.2 completada

**Technical Notes:**
- Implementar frontend en React 18 + TypeScript con componentes shadcn/ui
- Usar localStorage para guardar progreso temporal (evitar pérdida si cierra pestaña)
- Implementar timer opcional: "Tiempo estimado: 5 minutos"
- No mostrar respuestas correctas hasta finalizar (prevenir trampa)
- CSS: diseño limpio estilo plataforma educativa (ej. Kahoot, Quizlet)
- Agregar tests: navegación entre preguntas, submit quiz, cálculo de puntuación

---

### Story 4.4: Sugerencia de Learning Paths (Rutas de Aprendizaje)

Como usuario,
Quiero que la IA sugiera una ruta de aprendizaje personalizada sobre un tema,
Para saber qué documentos estudiar y en qué orden para dominar un área de conocimiento.

**Acceptance Criteria:**

**Given** que estoy autenticado
**When** solicito un learning path sobre un tema
**Then** existe el endpoint:

**POST /api/ia/generate/learning-path**
- Headers: `Authorization: Bearer {token}`
- Body:
  ```json
  {
    "topic": "procedimientos de reembolsos",
    "user_level": "beginner"  // opciones: "beginner", "intermediate", "advanced"
  }
  ```
- Response 200:
  ```json
  {
    "topic": "procedimientos de reembolsos",
    "user_level": "beginner",
    "learning_path": {
      "title": "Ruta de Aprendizaje: Procedimientos de Reembolsos",
      "estimated_time_hours": 3,
      "steps": [
        {
          "step_number": 1,
          "title": "Conceptos básicos de reembolsos",
          "document_id": 3,
          "document_title": "Introducción a Políticas RRHH",
          "estimated_time_minutes": 20,
          "why_this_step": "Establece fundamentos antes de procedimientos específicos"
        },
        {
          "step_number": 2,
          "title": "Procedimiento estándar de reembolsos",
          "document_id": 5,
          "document_title": "Procedimiento de Reembolsos",
          "estimated_time_minutes": 45,
          "why_this_step": "Detalla el proceso paso a paso"
        },
        {
          "step_number": 3,
          "title": "Casos especiales y urgentes",
          "document_id": 8,
          "document_title": "Manual de Procedimientos Especiales",
          "estimated_time_minutes": 30,
          "why_this_step": "Cubre excepciones y casos avanzados"
        },
        {
          "step_number": 4,
          "title": "Evaluación de conocimientos",
          "quiz_id": 12,
          "quiz_title": "Quiz: Procedimientos de Reembolsos",
          "estimated_time_minutes": 15,
          "why_this_step": "Valida tu comprensión del tema"
        }
      ]
    },
    "generated_at": "2025-11-10T10:30:00Z"
  }
  ```

**And** el proceso de generación:
1. Busca documentos relevantes usando retrieval de Story 3.2:
   - `retrieve_relevant_documents(topic, top_k=10)`
2. Filtra documentos por relevancia (score >0.3)
3. Construye prompt para el LLM:
   ```
   Eres un experto en diseño instruccional.

   Crea una ruta de aprendizaje personalizada para el siguiente tema.

   TEMA: {topic}
   NIVEL DEL USUARIO: {user_level}

   DOCUMENTOS DISPONIBLES:
   1. {doc1_title} - {doc1_snippet}
   2. {doc2_title} - {doc2_snippet}
   ...

   Genera una secuencia de aprendizaje lógica:
   - Para beginners: empezar con fundamentos
   - Para intermediate: enfocarse en aplicación práctica
   - Para advanced: casos complejos y excepciones

   Para cada paso, indica:
   - Qué documento leer
   - Por qué es importante en esta secuencia
   - Tiempo estimado de estudio

   Formato JSON:
   {...}
   ```
4. Parsea respuesta del LLM
5. Agrega quiz al final (si existe quiz generado para documentos relevantes)

**And** valida el learning path:
- Mínimo 2 pasos, máximo 8 pasos (secuencia manejable)
- Cada paso referencia un documento válido existente
- Orden lógico: fundamentos → aplicación → casos avanzados
- Si no hay suficientes documentos relevantes: Response 400 "No se encontraron documentos suficientes sobre '{topic}'. Intenta con otro tema."

**And** almacena learning path:
- Tabla `generated_content` con `content_type='learning_path'`
- Permite rastrear qué usuarios generaron qué paths (analítica de intereses)

**And** existe interfaz visual del learning path:
**GET /learning-path/{path_id}**
- Página con roadmap visual (timeline vertical o cards horizontales)
- Click en cada paso → navega al documento o quiz
- Checkbox para marcar completados (progreso guardado en localStorage)

**Prerequisites:** Story 4.3 completada

**Technical Notes:**
- Reusar retrieval service de Epic 3
- Usar GPT-4 para mejor planificación secuencial (GPT-3.5 puede funcionar con prompt bien diseñado)
- Estimar tiempos basado en longitud de documentos: ~5 min por 1000 palabras
- Visualización: usar biblioteca como `react-vertical-timeline` o custom CSS
- Agregar tests: generación exitosa, sin documentos relevantes, validación de estructura

---

### Story 4.5: Dashboard de Contenido Generado para Administradores

Como administrador,
Quiero ver un dashboard de todo el contenido generado por IA,
Para monitorear la calidad y uso de resúmenes, quizzes y learning paths.

**Acceptance Criteria:**

**Given** que estoy autenticado como administrador
**When** accedo al dashboard de contenido generado
**Then** existe una página `/admin/generated-content` con las siguientes secciones:

**1. Métricas Generales:**
```
📊 Resumen de Contenido Generado
- Total de resúmenes: 45
- Total de quizzes: 12
- Total de learning paths: 8
- Contenido generado esta semana: 15 items
```

**2. Lista de Contenido Generado:**
Tabla con columnas:
- ID | Tipo (Resumen/Quiz/Path) | Documento Origen | Generado por | Fecha | Acciones

**3. Filtros:**
- Por tipo de contenido (resúmenes, quizzes, learning paths)
- Por rango de fechas
- Por documento origen
- Por usuario que generó

**And** existe endpoint:
**GET /api/admin/generated-content**
- Headers: `Authorization: Bearer {admin_token}`
- Query params: `?type=quiz&limit=20&offset=0`
- Response:
  ```json
  {
    "total": 12,
    "items": [
      {
        "id": 15,
        "type": "quiz",
        "document_id": 5,
        "document_title": "Procedimiento de Reembolsos",
        "created_by": "admin",
        "created_at": "2025-11-10T10:30:00Z",
        "usage_count": 8  // cuántas veces se ha usado/respondido
      }
    ]
  }
  ```

**And** para cada quiz muestra estadísticas de uso:
**GET /api/admin/quiz/{quiz_id}/stats**
- Response:
  ```json
  {
    "quiz_id": 12,
    "total_attempts": 25,
    "avg_score_percentage": 78,
    "pass_rate": 0.84,  // 84% de intentos >=70%
    "most_difficult_question": {
      "question_number": 3,
      "correct_rate": 0.48
    }
  }
  ```

**And** permite acciones administrativas:
- **Ver:** Abre vista previa del contenido
- **Editar:** Permite modificar manualmente el contenido generado (opcional MVP)
- **Eliminar:** Borra el contenido generado (con confirmación)
- **Exportar:** Descarga como PDF o JSON

**And** muestra gráficas de tendencias (opcional MVP, en MVP solo tabla):
- Contenido generado por semana (line chart)
- Tipos de contenido más generados (pie chart)
- Documentos con más contenido generado (bar chart)

**Prerequisites:** Stories 4.1, 4.2, 4.3, 4.4 completadas

**Technical Notes:**
- Implementar en `backend/app/routes/admin.py`
- Solo accesible para rol 'admin' (decorador `@require_role('admin')`)
- Usar joins SQL para obtener estadísticas eficientemente
- Exportar quiz a PDF: usar biblioteca `reportlab` o `weasyprint`
- Dashboard UI: crear custom React admin dashboard con componentes shadcn/ui (Card, Table, Dialog)
- Agregar tests: listado, filtros, estadísticas, solo admin puede acceder

---

## Epic 5: Seguridad, Cumplimiento Normativo y Auditoría

**Objetivo:** Garantizar que el sistema cumpla con todas las regulaciones chilenas (Ley 19.628, Ley 21.180) y estándares internacionales (ISO 27001) mediante controles de seguridad robustos, cifrado, auditoría completa y anonimización de datos personales.

**Valor de Negocio:** Sin cumplimiento normativo, el prototipo no es viable para implementación real. Esta épica asegura la viabilidad legal y la confianza en el manejo de datos sensibles.

**Alineación con PRD:** RS1-RS5 (Requerimientos de Seguridad), RF6-RF8, Sección "Domain-Specific Requirements" (Cumplimiento Normativo).

---

### Story 5.1: Gestión de Usuarios y Roles (RBAC Completo)

Como administrador,
Quiero gestionar usuarios del sistema con roles claramente definidos,
Para controlar el acceso a funcionalidades sensibles según el principio de privilegio mínimo.

**Acceptance Criteria:**

**Given** que estoy autenticado como administrador
**When** implemento la gestión completa de usuarios
**Then** existen los siguientes endpoints:

**POST /api/admin/users** (crear usuario)
- Headers: `Authorization: Bearer {admin_token}`
- Body:
  ```json
  {
    "username": "juan.perez",
    "password": "SecurePass123!",
    "full_name": "Juan Pérez González",
    "email": "juan.perez@banmedica.cl",
    "role": "user"  // "admin" o "user"
  }
  ```
- Response 201:
  ```json
  {
    "user_id": 5,
    "username": "juan.perez",
    "full_name": "Juan Pérez González",
    "email": "juan.perez@banmedica.cl",
    "role": "user",
    "is_active": true,
    "created_at": "2025-11-10T10:30:00Z"
  }
  ```

**GET /api/admin/users** (listar usuarios)
- Response 200:
  ```json
  {
    "total": 12,
    "users": [
      {
        "user_id": 5,
        "username": "juan.perez",
        "full_name": "Juan Pérez González",
        "role": "user",
        "is_active": true,
        "last_login": "2025-11-09T15:30:00Z"
      }
    ]
  }
  ```

**PUT /api/admin/users/{user_id}** (actualizar usuario)
- Permite modificar: `full_name`, `email`, `role`, `is_active`
- NO permite modificar: `username` (es único e inmutable)
- Response 200: usuario actualizado

**PATCH /api/admin/users/{user_id}/deactivate** (desactivar usuario)
- Marca `is_active=False` (soft delete, mantiene trazabilidad)
- Usuario desactivado no puede hacer login
- Response 200: `{"message": "Usuario desactivado exitosamente"}`

**POST /api/users/change-password** (cambiar contraseña - cualquier usuario)
- Headers: `Authorization: Bearer {token}`
- Body:
  ```json
  {
    "current_password": "OldPass123!",
    "new_password": "NewSecurePass456!"
  }
  ```
- Valida contraseña actual antes de cambiar
- Response 200: `{"message": "Contraseña actualizada exitosamente"}`

**And** implementa validación de contraseñas seguras:
- Mínimo 8 caracteres
- Al menos 1 mayúscula, 1 minúscula, 1 número, 1 carácter especial
- No debe ser igual al username
- Si validación falla: Response 400 con mensaje específico del error

**And** modelo `User` extendido contiene:
- `id`, `username` (unique), `password_hash`, `full_name`, `email`, `role`, `is_active`, `created_at`, `last_login`, `failed_login_attempts`, `locked_until`

**And** registra eventos en audit logs:
- "USER_CREATED", "USER_UPDATED", "USER_DEACTIVATED", "PASSWORD_CHANGED"

**Prerequisites:** Epic 1 completada (base de autenticación existe)

**Technical Notes:**
- Validar passwords con librería `password-strength` o regex personalizado
- Hash passwords con bcrypt (work factor = 12)
- NO retornar `password_hash` en ningún endpoint (nunca exponer hashes)
- Email debe ser único (constraint en base de datos)
- Implementar en `backend/app/routes/admin.py` y `backend/app/routes/users.py`
- Agregar tests: crear usuario, validación de password débil, desactivar usuario, cambiar contraseña

---

### Story 5.2: Sistema de Bloqueo de Cuentas por Intentos Fallidos

Como sistema,
Quiero bloquear temporalmente cuentas tras múltiples intentos fallidos de login,
Para prevenir ataques de fuerza bruta y proteger cuentas de usuarios.

**Acceptance Criteria:**

**Given** que un usuario intenta hacer login
**When** implemento el sistema de protección anti-brute force
**Then** el flujo de login (Story 1.3) se extiende con:

**Lógica de intentos fallidos:**
1. Usuario envía credenciales a `/api/auth/login`
2. Si credenciales son **incorrectas**:
   - Incrementa `User.failed_login_attempts` en 1
   - Si `failed_login_attempts >= 5`:
     - Marca `User.locked_until = now() + 15 minutos`
     - Response 403:
       ```json
       {
         "error": {
           "code": "ACCOUNT_LOCKED",
           "message": "Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta nuevamente en 15 minutos.",
           "locked_until": "2025-11-10T10:45:00Z"
         }
       }
       ```
   - Si `failed_login_attempts < 5`:
     - Response 401:
       ```json
       {
         "error": {
           "code": "INVALID_CREDENTIALS",
           "message": "Usuario o contraseña incorrectos",
           "remaining_attempts": 3  // 5 - failed_login_attempts
         }
       }
       ```
3. Si credenciales son **correctas**:
   - Resetea `failed_login_attempts = 0`
   - Actualiza `last_login = now()`
   - Genera token JWT normalmente

**And** si cuenta está bloqueada (`locked_until > now()`):
- Response 403 inmediata sin validar credenciales (prevenir timing attacks)
- Mensaje indica tiempo restante de bloqueo

**And** bloqueo expira automáticamente:
- Si `now() > locked_until`: resetea `locked_until = NULL` y `failed_login_attempts = 0`
- Usuario puede intentar login nuevamente

**And** administrador puede desbloquear cuenta manualmente:
**POST /api/admin/users/{user_id}/unlock**
- Resetea `failed_login_attempts = 0` y `locked_until = NULL`
- Response 200: `{"message": "Cuenta desbloqueada exitosamente"}`

**And** registra eventos en audit logs:
- "LOGIN_FAILED" (cada intento fallido)
- "ACCOUNT_LOCKED" (cuando se bloquea)
- "ACCOUNT_UNLOCKED" (manual por admin o automático)

**And** configuración de bloqueo es personalizable:
- Variables en `.env`:
  ```
  MAX_FAILED_LOGIN_ATTEMPTS=5
  ACCOUNT_LOCKOUT_MINUTES=15
  ```

**Prerequisites:** Story 5.1 completada

**Technical Notes:**
- Implementar middleware de verificación de bloqueo antes de validar credenciales
- Usar transacciones de base de datos para incrementos atómicos (evitar race conditions)
- Loggear IP address en intentos fallidos (detección de ataques distribuidos)
- Opcional: implementar CAPTCHA tras 3 intentos fallidos (Growth Feature)
- Agregar tests: 5 intentos fallidos → bloqueo, desbloqueo automático tras 15 min, desbloqueo manual

---

### Story 5.3: Cifrado de Datos en Reposo y en Tránsito

Como desarrollador de seguridad,
Quiero cifrar datos sensibles en reposo y todas las comunicaciones en tránsito,
Para cumplir con RS4 y proteger la confidencialidad de información corporativa.

**Acceptance Criteria:**

**Given** que el sistema maneja datos sensibles
**When** implemento cifrado completo
**Then** se configuran las siguientes medidas:

**1. Cifrado en Tránsito (HTTPS):**
- Todas las comunicaciones HTTP usan TLS 1.2+ (HTTPS)
- Certificado SSL/TLS configurado:
  - **Laboratorio/desarrollo:** Certificado auto-firmado (generado con OpenSSL)
  - **Producción (futuro):** Certificado válido de CA (Let's Encrypt)
- Configuración FastAPI fuerza HTTPS en producción:
  ```python
  app.config['SESSION_COOKIE_SECURE'] = True  # Cookies solo sobre HTTPS
  app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevenir XSS
  app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevenir CSRF
  ```
- Redireccionamiento automático HTTP → HTTPS (middleware)

**2. Cifrado en Reposo (Base de Datos):**
- Base de datos SQLite cifrada usando extensión SQLCipher:
  ```sql
  PRAGMA key = 'your-encryption-key-from-env';
  ```
- Clave de cifrado almacenada en `.env`:
  ```
  DB_ENCRYPTION_KEY=your-256-bit-encryption-key-here
  ```
- Si migra a PostgreSQL (futuro): usar cifrado de disco completo o pgcrypto

**3. Cifrado de Campos Sensibles (Opcional en MVP, recomendado):**
- Campos que contienen PII (Personally Identifiable Information):
  - `User.email` → cifrado con AES-256
  - `AuditLog.details` → cifrado si contiene datos sensibles
- Usar biblioteca `cryptography` (Python):
  ```python
  from cryptography.fernet import Fernet
  cipher = Fernet(DB_FIELD_ENCRYPTION_KEY)
  encrypted_email = cipher.encrypt(email.encode())
  ```

**And** existe script de inicialización de claves:
**`scripts/generate_encryption_keys.py`**
- Genera claves criptográficas seguras:
  - `SECRET_KEY` (JWT)
  - `DB_ENCRYPTION_KEY` (SQLCipher)
  - `DB_FIELD_ENCRYPTION_KEY` (Fernet)
- Output: claves en formato seguro para copiar a `.env`

**And** documentación de seguridad:
**`docs/seguridad.md`** contiene:
- Cómo generar certificado SSL auto-firmado
- Cómo configurar HTTPS en entorno de desarrollo
- Cómo rotar claves de cifrado
- Política de gestión de secretos

**And** validación de configuración:
- Script de health check valida:
  - HTTPS está habilitado
  - Base de datos está cifrada
  - Claves de cifrado están configuradas (no valores por defecto)
- Si falla: sistema no inicia (fail-secure)

**Prerequisites:** Epic 1 completada

**Technical Notes:**
- **SQLCipher:** Reemplazar `sqlite3` con `pysqlcipher3` en requirements.txt
- **Certificado auto-firmado:** Generar con `openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes`
- **Claves:** Usar `secrets.token_urlsafe(32)` para generar claves seguras
- **IMPORTANTE:** `.env` NUNCA en Git (ya configurado en Story 1.5)
- Documentar cómo manejar claves en producción (ej. AWS Secrets Manager, HashiCorp Vault)
- Agregar tests: HTTPS redirect funciona, base de datos cifrada, cifrado de campos sensibles

---

### Story 5.4: Sistema de Auditoría Completo con Logs Estructurados

Como auditor/administrador,
Quiero que todas las acciones sensibles del sistema queden registradas en logs de auditoría,
Para tener trazabilidad completa y cumplir con RS3 y Ley 19.628.

**Acceptance Criteria:**

**Given** que el sistema tiene la tabla `audit_logs` (creada en Story 1.2)
**When** extiendo el sistema de auditoría
**Then** se registran los siguientes tipos de eventos:

**Eventos de Autenticación:**
- `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `PASSWORD_CHANGED`, `ACCOUNT_LOCKED`, `ACCOUNT_UNLOCKED`

**Eventos de Gestión de Conocimiento:**
- `DOCUMENT_UPLOADED`, `DOCUMENT_DOWNLOADED`, `DOCUMENT_DELETED`, `DOCUMENT_VIEWED`

**Eventos de IA:**
- `AI_QUERY`, `SUMMARY_GENERATED`, `QUIZ_GENERATED`, `LEARNING_PATH_GENERATED`, `QUIZ_SUBMITTED`

**Eventos de Administración:**
- `USER_CREATED`, `USER_UPDATED`, `USER_DEACTIVATED`, `ROLE_CHANGED`

**Eventos de Seguridad:**
- `UNAUTHORIZED_ACCESS_ATTEMPT`, `PERMISSION_DENIED`, `INVALID_TOKEN`, `SUSPICIOUS_ACTIVITY`

**And** cada log contiene campos estructurados:
```python
{
  "id": 1234,
  "timestamp": "2025-11-10T10:30:00.123456Z",
  "event_type": "AI_QUERY",
  "user_id": 5,
  "username": "juan.perez",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "resource": "query_12345",
  "action": "CREATE",
  "status": "success",  // "success", "failure", "error"
  "details": {
    "query": "¿Cómo solicito vacaciones?",
    "response_time_ms": 1850,
    "sources_count": 3
  },
  "severity": "INFO"  // "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
}
```

**And** implementa helper function para logging:
```python
def audit_log(
    event_type: str,
    user_id: int,
    resource: str,
    action: str,
    status: str = "success",
    details: dict = None,
    severity: str = "INFO"
):
    # Captura IP y User-Agent del request actual
    # Inserta en tabla audit_logs
    # Loggea también en archivo de logs (opcional)
```

**And** existe endpoint de consulta de logs (solo admin):
**GET /api/admin/audit-logs**
- Query params:
  - `?event_type=AI_QUERY` (filtrar por tipo de evento)
  - `?user_id=5` (filtrar por usuario)
  - `?start_date=2025-11-01&end_date=2025-11-10` (rango de fechas)
  - `?severity=ERROR` (filtrar por severidad)
  - `?limit=50&offset=0` (paginación)
- Response 200:
  ```json
  {
    "total": 1523,
    "logs": [
      {
        "id": 1234,
        "timestamp": "2025-11-10T10:30:00Z",
        "event_type": "AI_QUERY",
        "username": "juan.perez",
        "resource": "query_12345",
        "status": "success"
      }
    ]
  }
  ```

**And** logs se exportan para análisis externo:
**GET /api/admin/audit-logs/export?format=csv**
- Genera CSV con todos los logs (o filtrados)
- Headers: `Content-Disposition: attachment; filename="audit_logs_20251110.csv"`

**And** política de retención de logs:
- Logs se mantienen por mínimo 6 meses (configurable en `.env`)
- Script de limpieza automática: `scripts/cleanup_old_logs.py`
- Ejecutar mensualmente (cronjob o tarea programada)

**And** alertas de seguridad (opcional MVP):
- Si detecta >10 intentos fallidos de login desde misma IP en 5 minutos → loggea `SUSPICIOUS_ACTIVITY`
- Si usuario intenta acceder a recurso sin permisos → loggea `PERMISSION_DENIED`

**Prerequisites:** Story 5.2 completada

**Technical Notes:**
- Indexar columnas `timestamp`, `event_type`, `user_id` en tabla audit_logs (performance)
- Considerar rotar logs a archivos externos para largo plazo (ej. AWS S3, Elasticsearch)
- Usar Python `logging` module para logs de aplicación + tabla DB para auditoría
- Formato de timestamp: ISO 8601 con milisegundos y timezone UTC
- CSV export: usar biblioteca `csv` estándar de Python
- Agregar tests: audit_log() inserta correctamente, filtros funcionan, export CSV

---

### Story 5.5: Anonimización de Datos Personales (Ley 19.628)

Como desarrollador de cumplimiento,
Quiero anonimizar datos personales en documentos de prueba y datos de auditoría,
Para cumplir con la Ley 19.628 de protección de datos personales y garantizar que el prototipo no contenga información real de personas.

**Acceptance Criteria:**

**Given** que el sistema maneja datos personales
**When** implemento anonimización de datos
**Then** existe un módulo `backend/app/services/anonymization_service.py` con funciones:

**1. Detección de PII (Personally Identifiable Information):**
```python
def detect_pii(text: str) -> List[Dict]:
    """
    Detecta datos personales en texto.
    Retorna lista de PII encontrados: RUT, emails, teléfonos, nombres.
    """
    # Regex para RUT chileno: XX.XXX.XXX-X
    # Regex para email: nombre@dominio.cl
    # Regex para teléfono: +56 9 XXXX XXXX
    # NER (Named Entity Recognition) para nombres propios (opcional con spaCy)
```

**2. Anonimización automática:**
```python
def anonymize_text(text: str, method: str = "mask") -> str:
    """
    Anonimiza PII detectado.
    Métodos:
    - "mask": reemplaza con "***" (ej. "12.345.678-9" → "**.***.**-*")
    - "pseudonymize": reemplaza con identificador ficticio (ej. "Juan Pérez" → "Usuario_A123")
    - "synthetic": genera datos sintéticos realistas (ej. RUT válido pero ficticio)
    """
```

**And** se aplica anonimización en:

**Documentos de prueba:**
- Al cargar documentos (Story 2.2), sistema detecta PII
- Si documento contiene PII:
  - Loggea warning: "Documento contiene datos personales detectados"
  - Ofrece al admin opción de anonimizar automáticamente antes de indexar
  - Endpoint: `POST /api/knowledge/anonymize/{document_id}`

**Datos de auditoría:**
- Antes de almacenar en `audit_logs.details`, anonimiza queries que contengan PII
- Ejemplo:
  - Original: `{"query": "¿Cuándo tengo vacaciones Juan Pérez RUT 12.345.678-9?"}`
  - Anonimizado: `{"query": "¿Cuándo tengo vacaciones [NOMBRE] RUT [RUT]?"}`


**And** existe herramienta de auditoría de PII:
**GET /api/admin/pii-scan**
- Escanea todos los documentos en busca de PII
- Response:
  ```json
  {
    "total_documents": 50,
    "documents_with_pii": 8,
    "pii_types_found": ["RUT", "email", "phone"],
    "documents": [
      {
        "document_id": 5,
        "title": "Manual RRHH",
        "pii_count": 12,
        "pii_types": ["RUT", "email"]
      }
    ]
  }
  ```

**And** validación de cumplimiento:
- Script de validación: `scripts/validate_compliance.py`
- Verifica:
  - ✅ Ningún documento contiene PII real sin anonimizar
  - ✅ Logs de auditoría no exponen datos personales en texto plano
  - ✅ Datos de prueba utilizan información sintética o anonimizada
- Output: reporte de cumplimiento PDF

**Prerequisites:** Epic 2 completada

**Technical Notes:**
- **Detección de RUT:** Regex + validación de dígito verificador chileno
- **Detección de nombres:** Usar spaCy con modelo español `es_core_news_sm` (NER)
- **Alternativa ligera:** Regex + diccionario de nombres comunes chilenos
- **Faker para datos sintéticos:** Biblioteca `Faker` con locale `es_CL`
- **IMPORTANTE:** Esta funcionalidad protege contra filtración accidental de PII en datos de prueba
- **Justificación con modelo local:** Aunque los datos no salen del sistema, es buena práctica para:
  - Preparar datos de prueba limpios para el prototipo
  - Evitar almacenar PII real en logs que podrían exportarse
  - Demostrar cumplimiento normativo en el informe de prefactibilidad
- Documentar proceso de anonimización en `docs/cumplimiento-ley-19628.md`
- Agregar tests: detección de RUT, anonimización de email, scan de documentos

---

### Story 5.6: Control de Acceso Granular a Documentos (Opcional MVP)

Como administrador,
Quiero definir qué usuarios pueden acceder a qué categorías de documentos,
Para implementar control de acceso granular basado en necesidad de conocer (need-to-know).

**Acceptance Criteria:**

**Given** que algunos documentos son sensibles o confidenciales
**When** implemento control de acceso a nivel de categoría
**Then** se extiende el modelo de datos:

**Modelo `DocumentCategory` extendido:**
- `access_level` (String): "public", "internal", "confidential", "restricted"
- `allowed_roles` (JSON): Lista de roles permitidos, ej. `["admin", "manager"]`

**Modelo `UserPermissions` (nuevo):**
- `user_id` (FK → User.id)
- `category_id` (FK → DocumentCategory.id)
- `can_view` (Boolean)
- `can_download` (Boolean)

**And** lógica de autorización:
- Al listar documentos (`GET /api/knowledge/documents`):
  - Filtra documentos según categorías accesibles para el rol/usuario
  - Usuario normal solo ve categorías con `access_level = "public"` o permisos explícitos
  - Admin ve todas las categorías

- Al descargar documento (`GET /api/knowledge/documents/{id}/download`):
  - Verifica que usuario tiene `can_download=True` para esa categoría
  - Si no: Response 403 "No tienes permisos para descargar documentos de esta categoría"

- Al consultar IA (`POST /api/ia/query`):
  - Retrieval solo busca en documentos de categorías accesibles para el usuario
  - Respuestas NO incluyen información de documentos restringidos

**And** administrador gestiona permisos:
**POST /api/admin/permissions/grant**
- Body:
  ```json
  {
    "user_id": 5,
    "category_id": 3,
    "can_view": true,
    "can_download": false
  }
  ```
- Otorga permiso específico a usuario

**GET /api/admin/permissions/user/{user_id}**
- Lista todos los permisos de un usuario

**And** registra accesos a documentos restringidos:
- Logs de auditoría incluyen `access_level` del documento
- Evento: `RESTRICTED_DOCUMENT_ACCESSED`

**And** categorías predefinidas con niveles:
- "Políticas RRHH" → `public` (todos los usuarios)
- "Procedimientos Operativos" → `internal` (usuarios autenticados)
- "Información Financiera" → `confidential` (solo admin)
- "Datos Personales" → `restricted` (requiere permiso explícito)

**Prerequisites:** Story 5.4 completada

**Technical Notes:**
- **Nota:** Esta historia es OPCIONAL para MVP, pero importante para producción
- Si tiempo limitado: implementar solo control a nivel de rol (admin vs user) sin permisos granulares
- Implementar middleware `@require_category_access(category_id)` para endpoints
- Modificar retrieval service para filtrar por categorías accesibles
- Agregar tests: usuario sin permiso no ve documentos, admin ve todos, permisos granulares funcionan

---

