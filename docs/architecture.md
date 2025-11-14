# Asistente-Conocimiento - Architecture Document

**Project:** Asistente de Conocimiento - Prototipo de IA Generativa para Gestión del Conocimiento Organizacional
**Author:** Andres Amaya Garces
**Date:** 2025-11-11
**Version:** 1.0
**Academic Context:** Proyecto de Título - Universidad de Las Américas

---

## Executive Summary

Este documento define la arquitectura técnica del prototipo **Asistente-Conocimiento**, un sistema de inteligencia artificial generativa diseñado para revolucionar la gestión del conocimiento y capacitación organizacional. La arquitectura implementa un enfoque de **3 capas** (Presentación, Lógica, Datos) con énfasis en:

- **IA 100% Local**: Ollama + Llama 3.1 8B ejecutándose on-premise (sin dependencias cloud)
- **RAG (Retrieval-Augmented Generation)**: Respuestas fundamentadas en documentos corporativos
- **Cumplimiento Normativo**: Arquitectura diseñada para cumplir Ley 19.628 de protección de datos (Chile)
- **Performance**: Respuestas < 2 segundos mediante arquitectura asíncrona
- **Seguridad**: Autenticación JWT, cifrado en tránsito y reposo, control de acceso basado en roles

### Enfoque Arquitectónico

La arquitectura adopta un diseño **pragmático y académicamente riguroso**, priorizando:

1. **Simplicidad sobre complejidad**: SQLite para prototipo (migración a PostgreSQL documentada para producción)
2. **Reproducibilidad total**: Docker Compose permite setup completo en 1 comando
3. **Escalabilidad planificada**: Arquitectura prepara migración a producción sin reescritura
4. **Documentación exhaustiva**: Cada decisión técnica justificada con rationale académico

### Decisiones Arquitectónicas Clave

Las 12 decisiones críticas tomadas durante este proceso aseguran:
- Stack tecnológico moderno y bien soportado (Python 3.12, FastAPI 0.115, React 18)
- Separación clara de responsabilidades (Controllers → Services → Repositories)
- Patrones de implementación consistentes (naming, error handling, API contracts)
- Seguridad multi-capa (autenticación, autorización, auditoría, cifrado)

---

## Project Initialization

### Quick Start (Desarrollo)

**Prerequisitos:**
- Docker 24.0+ y Docker Compose 2.20+
- Git

**Setup en 3 comandos:**

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/asistente-conocimiento.git
cd asistente-conocimiento

# 2. Configurar variables de entorno
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Levantar servicios
docker-compose up --build
```

**Acceso:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Ollama: http://localhost:11434

### Manual Setup (Sin Docker)

**Backend:**
```bash
cd backend

# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependencias
poetry install

# Activar entorno virtual
poetry shell

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar dev server
npm run dev
```

**Ollama (Local):**
```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull modelo Llama 3.1
ollama pull llama3.1:8b-instruct-q4_K_M

# Verificar
ollama list
```

---

## Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| -------- | -------- | ------- | ------------- | --------- |
| **Backend Language** | Python | 3.12 | Todas | Ecosistema IA maduro, soporte Ollama nativo, FastAPI async |
| **Web Framework** | FastAPI | 0.115.0 | Todas | Async nativo (streaming), OpenAPI automático, validación Pydantic |
| **Database (Prototipo)** | SQLite | 3.45+ | E1, E2, E5 | Zero-config, portabilidad, ideal para prototipo académico |
| **Database (Producción)** | PostgreSQL | 16+ | E1, E2, E5 | ACID, pgvector para embeddings, escalabilidad |
| **ORM** | SQLModel | 0.0.14 | E1, E2, E5 | Type safety, integración FastAPI, simplicidad |
| **LLM Local** | Ollama + Llama 3.1 | 0.6.0 / 8B-q4 | E2, E3 | 100% local, Ley 19.628, sin costos token, 10-60 tokens/s |
| **Vector Database** | ChromaDB | 0.5.5 | E2 | Zero-config, persistencia disco, integración LangChain |
| **RAG Framework** | LangChain | 1.0.5 | E2, E3 | Framework RAG estándar, componentes pre-built, Ollama support |
| **Frontend Framework** | Vite + React 18 | 6.0 / 18.3 | E4 | Build rápido, TypeScript, shadcn/ui compatible, SPA ideal |
| **UI Components** | shadcn/ui + Tailwind | latest | E4 | Personalizable, accesible WCAG AA, especificado en UX Design |
| **State Management** | Zustand | 5.0 | E4 | Minimalista, TypeScript nativo, zero boilerplate |
| **Containerization** | Docker Compose | 2.20+ | Todas | Reproducibilidad, multi-container orchestration, demo fácil |

---

## Project Structure

```
asistente-conocimiento/
│
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── config.py                 # Settings (Pydantic BaseSettings)
│   │   ├── database.py               # SQLModel engine + session
│   │   │
│   │   ├── models/                   # SQLModel database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # User, Role enums
│   │   │   ├── document.py           # Document, Category
│   │   │   └── audit.py              # AuditLog
│   │   │
│   │   ├── schemas/                  # Pydantic schemas (API contracts)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # LoginRequest, TokenResponse
│   │   │   ├── document.py           # DocumentCreate, DocumentResponse
│   │   │   └── query.py              # QueryRequest, QueryResponse
│   │   │
│   │   ├── api/                      # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── deps.py               # Dependencies (get_current_user, get_db)
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py           # POST /api/auth/login, /logout
│   │   │       ├── knowledge.py      # CRUD /api/knowledge/documents
│   │   │       ├── ia.py             # POST /api/ia/query, /generate/*
│   │   │       └── audit.py          # GET /api/audit/logs (admin only)
│   │   │
│   │   ├── services/                 # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py       # JWT generation, password hashing
│   │   │   ├── document_service.py   # PDF processing, indexing ChromaDB
│   │   │   └── ia_service.py         # RAG orchestration (LangChain)
│   │   │
│   │   ├── core/                     # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── security.py           # JWT, password utils
│   │   │   ├── exceptions.py         # Custom exceptions
│   │   │   └── rag/                  # RAG components
│   │   │       ├── __init__.py
│   │   │       ├── embeddings.py     # OllamaEmbeddings wrapper
│   │   │       ├── vectorstore.py    # ChromaDB client
│   │   │       └── chains.py         # LangChain RAG chain
│   │   │
│   │   └── utils/                    # Helper functions
│   │       ├── __init__.py
│   │       ├── pdf_extractor.py      # PyPDF text extraction
│   │       └── logger.py             # Structured logging
│   │
│   ├── tests/                        # Pytest tests
│   │   ├── __init__.py
│   │   ├── conftest.py               # Fixtures (test DB, auth client)
│   │   ├── test_auth.py
│   │   ├── test_ia.py
│   │   └── test_documents.py
│   │
│   ├── alembic/                      # Database migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   │
│   ├── data/                         # Persistent data (gitignored)
│   │   ├── chroma_db/                # Vector store
│   │   └── database.db               # SQLite
│   │
│   ├── Dockerfile
│   ├── pyproject.toml                # Poetry dependencies
│   ├── poetry.lock
│   └── .env.example
│
├── frontend/                         # React + Vite Frontend
│   ├── src/
│   │   ├── main.tsx                  # Entry point
│   │   ├── App.tsx                   # Root component with routing
│   │   ├── vite-env.d.ts
│   │   │
│   │   ├── components/               # React components
│   │   │   ├── ui/                   # shadcn/ui base components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── toast.tsx
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── chat/                 # Chat feature (Epic 2)
│   │   │   │   ├── ChatBubble.tsx
│   │   │   │   ├── StreamingText.tsx
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   └── ChatHistory.tsx
│   │   │   │
│   │   │   ├── documents/            # Document management (Epic 1)
│   │   │   │   ├── SourceReferenceCard.tsx
│   │   │   │   ├── DocumentUploadZone.tsx
│   │   │   │   ├── DocumentList.tsx
│   │   │   │   └── DocumentViewer.tsx
│   │   │   │
│   │   │   └── layout/               # Layout components
│   │   │       ├── Navbar.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       └── Layout.tsx
│   │   │
│   │   ├── pages/                    # Route pages
│   │   │   ├── Login.tsx
│   │   │   ├── Chat.tsx              # Usuario regular main view
│   │   │   ├── Admin.tsx             # Admin dashboard
│   │   │   └── NotFound.tsx
│   │   │
│   │   ├── store/                    # Zustand state management
│   │   │   ├── authStore.ts
│   │   │   ├── chatStore.ts
│   │   │   └── documentStore.ts
│   │   │
│   │   ├── services/                 # API client layer
│   │   │   ├── api.ts                # Axios instance + interceptors
│   │   │   ├── authService.ts
│   │   │   ├── iaService.ts
│   │   │   └── documentService.ts
│   │   │
│   │   ├── types/                    # TypeScript interfaces
│   │   │   ├── auth.ts
│   │   │   ├── document.ts
│   │   │   └── chat.ts
│   │   │
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   └── useChat.ts
│   │   │
│   │   ├── lib/                      # Utilities
│   │   │   └── utils.ts
│   │   │
│   │   └── styles/
│   │       └── globals.css           # Tailwind directives
│   │
│   ├── public/
│   ├── index.html
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── components.json               # shadcn/ui config
│   └── .env.example
│
├── docs/                             # Documentación del proyecto
│   ├── PRD.md                        # Product Requirements Document
│   ├── ux-design-specification.md   # UX Design Specification
│   ├── architecture.md               # Este documento
│   ├── bmm-workflow-status.yaml     # Estado de workflows BMAD
│   │
│   ├── academico/                    # Documentación para informe
│   │   ├── metodologia-scrum.md
│   │   ├── informe-prefactibilidad.md
│   │   ├── plan-pruebas.md
│   │   └── diagramas-uml/
│   │       ├── casos-de-uso.puml
│   │       ├── componentes.puml
│   │       ├── secuencia-consulta.puml
│   │       └── modelo-datos.puml
│   │
│   └── technical/                    # Docs técnicas post-implementación
│       ├── README.md
│       ├── setup-guide.md
│       └── api-documentation.md
│
├── .bmad/                            # BMAD methodology metadata
│   └── bmm/
│       ├── config.yaml
│       └── workflows/
│
├── docker-compose.yml                # Multi-container orchestration
├── .gitignore
├── README.md
└── LICENSE
```

---

## Epic to Architecture Mapping

| Epic | Componentes Backend | Componentes Frontend | Tecnologías Clave |
|------|---------------------|----------------------|-------------------|
| **E1: Gestión de Repositorio** | `DocumentService`, `DocumentRepository`, `/api/knowledge/*` | `DocumentUploadZone`, `DocumentList`, `documentStore` | PyPDF, SQLModel, ChromaDB |
| **E2: Motor de IA Generativa** | `IAService`, `RAGChain`, `/api/ia/query` | `ChatBubble`, `StreamingText`, `chatStore` | Ollama, Llama 3.1, LangChain |
| **E3: Generación Contenido Formativo** | `IAService.generate_quiz()`, `/api/ia/generate/*` | Quiz components (futuro) | LangChain chains |
| **E4: Interfaz de Usuario** | N/A (solo frontend) | Todos los componentes UI, Layout, Pages | React, shadcn/ui, Tailwind |
| **E5: Seguridad y Cumplimiento** | `AuthService`, `AuditLog`, middleware auth | `Login`, `authStore`, API interceptors | JWT, bcrypt, Alembic |

---

## Technology Stack Details

### Core Technologies

#### Backend Stack

**Runtime & Framework:**
- **Python 3.12**: Lenguaje principal backend
  - Performance mejorada vs 3.11 (PEP 669, faster comprehensions)
  - Ecosystem IA más maduro (LangChain, HuggingFace, etc.)

- **FastAPI 0.115.0**: Framework web asíncrono
  - Async/await nativo → streaming responses para LLM
  - OpenAPI/Swagger automático → documentación API gratis
  - Pydantic validation → type safety en requests/responses
  - Performance comparable a Node.js/Go

**Database Layer:**
- **SQLite 3.45+** (Prototipo)
  - Zero-config, archivo único `database.db`
  - Portabilidad total (ideal para demo académica)
  - Migración planificada a PostgreSQL para producción

- **SQLModel 0.0.14**: ORM
  - Combina SQLAlchemy + Pydantic
  - Mismos modelos para DB y API (DRY)
  - Type hints integrados

- **Alembic 1.13+**: Migraciones de DB
  - Versionado de esquema
  - Rollback/upgrade controlado

**IA & RAG Stack:**
- **Ollama 0.6.0**: Runtime para LLMs locales
  - Servidor HTTP en puerto 11434
  - API REST simple para inferencia

- **Llama 3.1 8B Instruct (q4_K_M)**: Modelo LLM
  - Cuantizado 4-bit → ~4.7GB en disco
  - Performance: 10-20 tokens/s (CPU), 40-60 tokens/s (GPU)
  - Context window: 8192 tokens

- **LangChain 1.0.5**: Framework RAG
  - `PyPDFLoader`: Carga documentos PDF
  - `RecursiveCharacterTextSplitter`: Chunking inteligente
  - `OllamaEmbeddings`: Generación embeddings
  - `RetrievalQA`: Chain RAG completo

- **ChromaDB 0.5.5**: Vector database
  - Persistencia en `data/chroma_db/`
  - Embeddings 384-dim (all-mpnet-base-v2 via Ollama)
  - Similarity search con metadatos

**Security & Auth:**
- **python-jose 3.3+**: JWT encoding/decoding
- **passlib[bcrypt] 1.7+**: Password hashing
- **python-multipart 0.0.9+**: File uploads

**Utilities:**
- **PyPDF 5.1+**: Extracción texto de PDFs
- **uvicorn[standard] 0.31+**: ASGI server (production-ready)

#### Frontend Stack

**Runtime & Framework:**
- **Node.js 20+ / npm**: JavaScript runtime
- **Vite 6.0**: Build tool & dev server
  - HMR (Hot Module Replacement) instantáneo
  - Builds optimizados con Rollup
  - Plugins ecosystem

- **React 18.3**: UI library
  - Hooks (useState, useEffect, custom hooks)
  - Concurrent rendering
  - Suspense para lazy loading

- **TypeScript 5.6+**: Type safety
  - Interfaces para API contracts
  - Compile-time error detection

**UI & Styling:**
- **shadcn/ui**: Component library
  - Radix UI primitives (accesibles WCAG AA)
  - Tailwind CSS styling
  - Copiable/customizable components

- **Tailwind CSS 3.4+**: Utility-first CSS
  - Design system configurado en `tailwind.config.js`
  - Responsive design (mobile-first)
  - Custom colors (Trust Blue + Academic Slate)

- **Lucide React**: Icon library
  - SVG icons optimizados
  - Tree-shakeable

**State & Data:**
- **Zustand 5.0**: State management
  - Global state (auth, chat, documents)
  - DevTools support
  - Middleware (persist, immer)

- **Axios 1.7+**: HTTP client
  - Interceptors para auth token
  - Error handling centralizado
  - Request/response transformation

**Routing:**
- **React Router 6.26+**: Client-side routing
  - Protected routes (auth required)
  - Lazy loading pages

**Development Tools:**
- **ESLint 9+**: Linting
- **Prettier 3+**: Code formatting
- **Vitest**: Testing (compatible con Vite)

#### DevOps & Infrastructure

**Containerization:**
- **Docker 24.0+**: Containerización
  - Multi-stage builds (optimización tamaño)
  - Health checks integrados

- **Docker Compose 2.20+**: Orchestration
  - 3 servicios: backend, frontend, ollama
  - Networking automático
  - Volume persistence

**Development:**
- **Poetry 1.8+**: Python dependency management
  - Lock file determinista (`poetry.lock`)
  - Virtual env automático
  - Build & publish integrados

- **Git**: Version control
  - Conventional commits
  - Feature branches

### Integration Points

#### 1. Frontend ↔ Backend (REST API)

**Protocol:** HTTP/HTTPS
**Format:** JSON
**Authentication:** JWT in Authorization header

**Flujo:**
```
Frontend (React)
  → Axios HTTP Request + JWT token
    → FastAPI endpoint (/api/*)
      → Service layer (business logic)
        → Database (SQLModel) / RAG (LangChain)
      ← Response (Pydantic schema)
    ← JSON response
  ← State update (Zustand)
```

**Ejemplo:**
```typescript
// Frontend: src/services/iaService.ts
async function queryIA(query: string): Promise<QueryResponse> {
  const response = await api.post('/api/ia/query', { query });
  return response.data;
}
```

```python
# Backend: app/api/routes/ia.py
@router.post("/query", response_model=QueryResponse)
async def query_ia(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    ia_service: IAService = Depends()
):
    return await ia_service.process_query(request.query, current_user)
```

#### 2. Backend ↔ Ollama (Local LLM)

**Protocol:** HTTP
**Host:** `http://ollama:11434` (Docker) o `http://localhost:11434` (local)
**SDK:** `ollama` Python package

**Flujo:**
```
Backend (IAService)
  → OllamaLLM.invoke(prompt)
    → HTTP POST to Ollama API
      → Llama 3.1 inference
    ← Streamed tokens
  ← Complete response
```

**Ejemplo:**
```python
from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="llama3.1:8b-instruct-q4_K_M",
    base_url="http://ollama:11434"
)

response = llm.invoke("¿Cómo proceso un reembolso?")
```

#### 3. Backend ↔ ChromaDB (Vector Store)

**Protocol:** Python SDK (local file-based)
**Storage:** `backend/data/chroma_db/`

**Flujo:**
```
Backend (DocumentService)
  → Load PDF → Extract text
    → Split into chunks (500 chars, 50 overlap)
      → Generate embeddings (OllamaEmbeddings)
        → Store in ChromaDB
          → Persist to disk

Backend (IAService - Query)
  → User query
    → Generate query embedding
      → ChromaDB similarity search (top 5)
        → Retrieve relevant chunks
          → Pass to LLM as context
            → Generate answer
```

**Ejemplo:**
```python
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="llama3.1:8b-instruct-q4_K_M")

vectorstore = Chroma(
    persist_directory="./data/chroma_db",
    embedding_function=embeddings
)

# Indexar documento
vectorstore.add_texts(chunks, metadatas=[{"source": "manual.pdf"}])

# Buscar
docs = vectorstore.similarity_search("reembolso", k=5)
```

#### 4. Docker Compose Orchestration

**docker-compose.yml:**
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - DATABASE_URL=sqlite:///./data/database.db
    volumes:
      - ./backend/data:/app/data
    depends_on:
      - ollama

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

---

## Implementation Patterns

### Naming Conventions

#### Backend (Python)

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Archivos | `snake_case.py` | `document_service.py` |
| Clases | `PascalCase` | `class DocumentService` |
| Funciones | `snake_case` | `def process_document()` |
| Variables | `snake_case` | `user_id = 123` |
| Constantes | `UPPER_SNAKE_CASE` | `MAX_FILE_SIZE` |
| Models | `PascalCase` (singular) | `class Document(SQLModel)` |
| Schemas | `PascalCase` + sufijo | `class DocumentCreate(BaseModel)` |
| Endpoints | `kebab-case` (plural) | `/api/knowledge/documents` |
| Env vars | `UPPER_SNAKE_CASE` | `DATABASE_URL` |

#### Frontend (TypeScript)

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Componentes | `PascalCase.tsx` | `ChatBubble.tsx` |
| Utilities | `camelCase.ts` | `apiClient.ts` |
| Functions | `camelCase` | `function formatDate()` |
| Variables | `camelCase` | `const userId = 123` |
| Constantes | `UPPER_SNAKE_CASE` | `const API_TIMEOUT` |
| Interfaces | `PascalCase` | `interface UserProps` |
| Hooks | `use + PascalCase` | `function useAuth()` |
| Stores | `use + PascalCase + Store` | `useAuthStore` |

### Code Organization

**Backend - Layer Separation:**
- **API Layer** (`app/api/routes/`): Solo validación y orquestación
- **Service Layer** (`app/services/`): Lógica de negocio
- **Repository Layer** (`app/repositories/` - opcional): Acceso a datos
- **Models** (`app/models/`): Definición de DB
- **Schemas** (`app/schemas/`): Contratos API

**Frontend - Feature-Based:**
```
components/
  chat/          # Todo lo relacionado con chat
  documents/     # Todo lo relacionado con documentos
  layout/        # Componentes de layout
```

### API Patterns

**REST Naming:**
```
GET    /api/knowledge/documents           # Listar
POST   /api/knowledge/documents           # Crear
GET    /api/knowledge/documents/{id}      # Obtener
PUT    /api/knowledge/documents/{id}      # Actualizar
DELETE /api/knowledge/documents/{id}      # Eliminar
```

**Request/Response Format:**
```json
// Request (camelCase)
{
  "title": "Manual de Procedimientos",
  "category": "manual"
}

// Response Success (camelCase)
{
  "id": 123,
  "title": "Manual de Procedimientos",
  "uploadDate": "2025-11-10T15:30:00Z"
}

// Response Error (structured)
{
  "error": {
    "code": "INVALID_FILE_FORMAT",
    "message": "El archivo debe ser PDF o TXT",
    "details": {
      "field": "file",
      "receivedFormat": "docx"
    }
  }
}
```

### Error Handling

**Backend - Custom Exceptions:**
```python
# app/core/exceptions.py
class AppException(Exception):
    def __init__(self, message: str, code: str, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}

class DocumentNotFoundError(AppException):
    def __init__(self, document_id: int):
        super().__init__(
            message=f"Documento {document_id} no encontrado",
            code="DOCUMENT_NOT_FOUND",
            details={"documentId": document_id}
        )

# app/main.py - Global handler
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=400,
        content={"error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }}
    )
```

**Frontend - Axios Interceptors:**
```typescript
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError = error.response?.data?.error;
    throw {
      code: apiError?.code || 'UNKNOWN_ERROR',
      message: apiError?.message || 'Error inesperado',
      status: error.response?.status || 0
    };
  }
);
```

### Logging Strategy

**Structured JSON Logging:**
```python
logger.info(json.dumps({
    "timestamp": datetime.utcnow().isoformat(),
    "level": "INFO",
    "message": "Query processed",
    "userId": user.id,
    "queryTimeMs": elapsed
}))
```

---

## Data Architecture

### Database Schema (SQLite/PostgreSQL)

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL,  -- 'admin' o 'user'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Documents Table
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'processing',  -- 'processing', 'indexed', 'error'
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,  -- 'login', 'query', 'upload', 'delete'
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details TEXT,  -- JSON string
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### SQLModel Models

```python
# app/models/user.py
from sqlmodel import SQLModel, Field
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, max_length=50)
    email: str = Field(unique=True, max_length=100)
    hashed_password: str = Field(max_length=255)
    full_name: str | None = Field(max_length=100)
    role: UserRole = Field(default=UserRole.USER)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Vector Store Structure (ChromaDB)

**Collection:** `knowledge_base`

**Document Structure:**
```python
{
    "id": "doc_123_chunk_1",
    "embedding": [0.123, -0.456, ...],  # 384-dim vector
    "text": "Para procesar un reembolso especial...",
    "metadata": {
        "document_id": 123,
        "source": "Manual de Procedimientos",
        "category": "manual",
        "chunk_index": 1,
        "upload_date": "2025-11-10"
    }
}
```

### Entity-Relationship Diagram

```
┌──────────────┐       ┌────────────────┐       ┌─────────────┐
│    Users     │1    N │   Documents    │1    N │ AuditLogs   │
├──────────────┤───────├────────────────┤───────├─────────────┤
│ id (PK)      │       │ id (PK)        │       │ id (PK)     │
│ username     │       │ title          │       │ user_id (FK)│
│ email        │       │ category       │       │ action      │
│ hashed_pwd   │       │ file_path      │       │ resource_*  │
│ role         │       │ user_id (FK)   │       │ timestamp   │
│ is_active    │       │ upload_date    │       └─────────────┘
└──────────────┘       │ status         │
                       └────────────────┘
```

---

## API Contracts

### Authentication Endpoints

#### POST /api/auth/login
**Request:**
```json
{
  "username": "admin",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tokenType": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "fullName": "Administrador Sistema"
  }
}
```

**Error (401 Unauthorized):**
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Usuario o contraseña incorrectos"
  }
}
```

#### POST /api/auth/logout
**Headers:** `Authorization: Bearer {token}`

**Response (200 OK):**
```json
{
  "message": "Logout exitoso"
}
```

### Knowledge Management Endpoints

#### POST /api/knowledge/documents
**Headers:** `Authorization: Bearer {token}`
**Content-Type:** `multipart/form-data`

**Request:**
```
file: [Binary PDF]
title: "Manual de Procedimientos"
category: "manual"
description: "Manual completo de procedimientos organizacionales"
```

**Response (201 Created):**
```json
{
  "id": 123,
  "title": "Manual de Procedimientos",
  "category": "manual",
  "filePath": "uploads/manual_procedimientos_20251110.pdf",
  "fileSize": 2048576,
  "uploadDate": "2025-11-10T15:30:00Z",
  "userId": 1,
  "status": "processing"
}
```

#### GET /api/knowledge/documents
**Headers:** `Authorization: Bearer {token}`
**Query Params:** `?category=manual&limit=10&offset=0`

**Response (200 OK):**
```json
{
  "documents": [
    {
      "id": 123,
      "title": "Manual de Procedimientos",
      "category": "manual",
      "uploadDate": "2025-11-10T15:30:00Z",
      "status": "indexed"
    }
  ],
  "total": 45,
  "limit": 10,
  "offset": 0
}
```

### IA Endpoints

#### POST /api/ia/query
**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "query": "¿Cómo proceso un reembolso especial?",
  "contextMode": "general"
}
```

**Response (200 OK):**
```json
{
  "answer": "Para procesar un reembolso especial, debes seguir estos pasos:\n1. Verificar elegibilidad del afiliado...",
  "sources": [
    {
      "documentId": 123,
      "title": "Manual de Procedimientos",
      "excerpt": "Para reembolsos especiales, verificar primero...",
      "relevanceScore": 0.92
    }
  ],
  "responseTimeMs": 1847,
  "confidenceScore": 0.88
}
```

#### POST /api/ia/generate/quiz
**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "documentId": 123,
  "numQuestions": 5,
  "difficulty": "medium"
}
```

**Response (200 OK):**
```json
{
  "quiz": [
    {
      "question": "¿Cuál es el primer paso para procesar un reembolso especial?",
      "options": [
        "Verificar elegibilidad",
        "Generar formulario",
        "Contactar al afiliado",
        "Validar monto"
      ],
      "correctAnswer": "Verificar elegibilidad",
      "explanation": "Según el manual, la verificación de elegibilidad es el paso inicial..."
    }
  ],
  "generatedAt": "2025-11-10T15:35:00Z"
}
```

#### POST /api/ia/generate/learning-path
**Headers:** `Authorization: Bearer {token}`
**Rate Limit:** 5 requests per user per day

**Request:**
```json
{
  "topic": "procedimientos de reembolsos",
  "user_level": "beginner"
}
```

**Response (200 OK):**
```json
{
  "learning_path_id": 456,
  "title": "Ruta de Aprendizaje: Procedimientos de Reembolsos (Principiante)",
  "steps": [
    {
      "step_number": 1,
      "title": "Entender los conceptos básicos de reembolsos",
      "document_id": 123,
      "why_this_step": "Es importante conocer qué son los reembolsos y sus categorías",
      "estimated_time_minutes": 15
    },
    {
      "step_number": 2,
      "title": "Aprender el procedimiento paso a paso",
      "document_id": 124,
      "why_this_step": "Necesitas saber exactamente cómo solicitar un reembolso",
      "estimated_time_minutes": 20
    }
  ],
  "total_steps": 2,
  "estimated_time_hours": 0.58,
  "user_level": "beginner",
  "generated_at": "2025-11-14T12:30:00Z"
}
```

**Error (400 Bad Request - Insufficient Documents):**
```json
{
  "detail": "No se encontraron documentos suficientes sobre 'tema_inexistente'. Intenta con otro tema."
}
```

**Error (400 Bad Request - Validation):**
```json
{
  "detail": "El tema debe tener al menos 5 caracteres"
}
```

**Error (429 Too Many Requests):**
```json
{
  "detail": "Has alcanzado el límite de 5 generaciones por día. Intenta mañana."
}
```

#### GET /api/ia/learning-path/{path_id}
**Headers:** `Authorization: Bearer {token}`

**Response (200 OK):**
```json
{
  "id": 456,
  "user_id": 1,
  "topic": "procedimientos de reembolsos",
  "user_level": "beginner",
  "title": "Ruta de Aprendizaje: Procedimientos de Reembolsos (Principiante)",
  "steps": [
    {
      "step_number": 1,
      "title": "Entender los conceptos básicos de reembolsos",
      "document_id": 123,
      "why_this_step": "Es importante conocer qué son los reembolsos y sus categorías",
      "estimated_time_minutes": 15
    },
    {
      "step_number": 2,
      "title": "Aprender el procedimiento paso a paso",
      "document_id": 124,
      "why_this_step": "Necesitas saber exactamente cómo solicitar un reembolso",
      "estimated_time_minutes": 20
    }
  ],
  "estimated_time_hours": 0.58,
  "content_json": "{...}",
  "created_at": "2025-11-14T12:30:00Z"
}
```

**Error (404 Not Found):**
```json
{
  "detail": "La ruta de aprendizaje no existe"
}
```

**Error (403 Forbidden):**
```json
{
  "detail": "No tienes acceso a esta ruta de aprendizaje"
}
```

### Audit Endpoints

#### GET /api/audit/logs
**Headers:** `Authorization: Bearer {token}` (Admin only)
**Query Params:** `?userId=1&action=query&startDate=2025-11-01&limit=50`

**Response (200 OK):**
```json
{
  "logs": [
    {
      "id": 5432,
      "userId": 1,
      "action": "query",
      "resourceType": "ia",
      "details": {
        "query": "¿Cómo proceso un reembolso?",
        "responseTimeMs": 1847
      },
      "ipAddress": "192.168.1.100",
      "timestamp": "2025-11-10T15:30:45Z"
    }
  ],
  "total": 1234
}
```

---

## Security Architecture

### Authentication & Authorization

**Método:** JWT (JSON Web Tokens)

**Flujo de Autenticación:**
```
1. User → POST /api/auth/login (username, password)
2. Backend → Validar credenciales (bcrypt compare)
3. Backend → Generar JWT (firma con SECRET_KEY)
4. Backend → Return token + user info
5. Frontend → Almacenar token en sessionStorage
6. Frontend → Incluir token en header de todas las requests subsecuentes
```

**JWT Payload:**
```json
{
  "sub": "1",              // User ID
  "role": "admin",         // Admin o User
  "exp": 1731340800,       // Expiration (24 horas)
  "iat": 1731254400,       // Issued at
  "type": "access"
}
```

**Autorización por Roles:**
```python
# app/api/deps.py
def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# app/api/routes/audit.py
@router.get("/logs")
async def get_audit_logs(admin: User = Depends(get_current_admin)):
    # Solo admins pueden acceder
    ...
```

### Password Security

**Hashing:** bcrypt con salt automático
**Rounds:** 12 (balance seguridad/performance)

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hashear password
hashed = pwd_context.hash("securepassword123")

# Verificar
is_valid = pwd_context.verify("securepassword123", hashed)
```

### Data Encryption

**En Tránsito:**
- HTTPS/TLS 1.3 (producción)
- HTTP (desarrollo local - Docker interno)

**En Reposo:**
- SQLite con extensión SEE (opcional, no implementado en prototipo)
- Producción: PostgreSQL con cifrado a nivel de filesystem (LUKS/dm-crypt)

### Input Validation

**Todas las entradas validadas con Pydantic:**
```python
from pydantic import BaseModel, Field, validator

class DocumentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    category: str = Field(pattern="^(manual|procedimiento|normativa|formulario)$")

    @validator('title')
    def sanitize_title(cls, v):
        # Prevenir inyección SQL/XSS
        return v.strip()
```

### CORS Configuration

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Audit Logging

**Requisito RS3:** Registro de todas las acciones críticas

**Eventos Auditados:**
- Login/logout
- Consultas a IA (query, responseTimeMs)
- Carga/eliminación de documentos
- Cambios de configuración (admin)
- Accesos denegados (401, 403)

**Implementación:**
```python
# app/services/audit_service.py
async def log_action(
    user_id: int,
    action: str,
    resource_type: str = None,
    resource_id: int = None,
    details: dict = None,
    ip_address: str = None
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address
    )
    session.add(log)
    await session.commit()
```

### Admin Dashboard Endpoints (Story 4.5)

**Nuevos endpoints para dashboard de administrador - Gestión centralizada de contenido generado**

**Endpoints:**

1. **GET /api/admin/generated-content**
   - Descripción: Lista todo el contenido generado con filtros y paginación
   - Auth: Requiere Bearer token + rol admin
   - Parámetros query:
     - `type`: Filtro por tipo (summary|quiz|learning_path)
     - `document_id`: Filtro por documento
     - `user_id`: Filtro por usuario generador
     - `date_from`: Fecha inicial (ISO 8601)
     - `date_to`: Fecha final (ISO 8601)
     - `search`: Búsqueda de texto libre
     - `limit`: Items por página (default 20)
     - `offset`: Paginación offset
     - `sort_by`: Campo para ordenamiento (id, created_at, content_type)
     - `sort_order`: asc|desc
   - Response: `{total: int, items: [{id, content_type, document_id, user_id, created_at, is_validated, validated_by, validated_at}], limit, offset}`

2. **PUT /api/admin/generated-content/{content_id}/validate**
   - Descripción: Marcar contenido como validado/revisado
   - Auth: Requiere rol admin
   - Body: `{is_validated: bool}`
   - Response: `{id, is_validated, validated_by, validated_at}`
   - Auditoría: Registra acción con validated_by, timestamp

3. **DELETE /api/admin/generated-content/{content_id}**
   - Descripción: Soft delete de contenido (marca como eliminado, no borra)
   - Auth: Requiere rol admin
   - Response: 204 No Content
   - Auditoría: Registra acción de eliminación

4. **GET /api/admin/quiz/{quiz_id}/stats**
   - Descripción: Estadísticas de evaluación de un quiz
   - Auth: Requiere rol admin
   - Response: `{quiz_id, total_attempts, avg_score_percentage, pass_rate, most_difficult_question: {number, correct_rate}}`

5. **GET /api/admin/learning-path/{path_id}/stats**
   - Descripción: Estadísticas de una ruta de aprendizaje
   - Auth: Requiere rol admin
   - Response: `{path_id, total_views, completed_count, completion_rate, most_skipped_step}`

6. **GET /api/admin/generated-content/export**
   - Descripción: Exportar contenido como CSV o PDF
   - Auth: Requiere rol admin
   - Parámetros: `format` (csv|pdf)
   - Response: Archivo descargable con Content-Disposition: attachment

**Implementación:**
- Archivo: `backend/app/routes/admin.py`
- Servicio: `backend/app/services/admin_service.py`
- Modelos BD: ExtendGeneratedContent con campos is_validated, validated_by, validated_at, deleted_at
- Tablas adicionales: quiz_attempts, learning_path_progress para estadísticas

### Compliance (Ley 19.628 - Chile)

**Medidas Implementadas:**

1. **Anonimización de Datos de Prueba (RS5)**
   - Datos sintéticos generados para demostración
   - Ningún dato personal real en prototipo

2. **Control de Acceso (RS1, RS2)**
   - Autenticación obligatoria
   - Roles Admin/User con permisos diferenciados

3. **Auditoría Completa (RS3)**
   - Trazabilidad de accesos y consultas
   - Logs con timestamp, user_id, acción

4. **Cifrado (RS4)**
   - HTTPS en producción
   - Tokens JWT firmados

5. **Minimización de Datos**
   - Solo se almacena información necesaria
   - No se comparten datos con terceros (IA 100% local)

---

## Performance Considerations

### Target Metrics (RNF2)

**Requisito:** Respuestas de IA < 2 segundos

**Estrategia Multi-capa:**

1. **Backend Async (FastAPI)**
   - Async/await en todos los endpoints I/O bound
   - Streaming responses (chunks de 50 caracteres)
   - Uvicorn con workers múltiples

2. **RAG Optimization**
   - Chunks pequeños (500 caracteres, 50 overlap)
   - Top-K limitado (5 documentos más relevantes)
   - Embeddings cacheados cuando es posible

3. **Ollama Performance**
   - Modelo cuantizado q4_K_M (balance calidad/velocidad)
   - GPU acceleration (opcional, 3x speedup)
   - Context window limitado (2048 tokens max prompt)

4. **ChromaDB Indexing**
   - HNSW index para similarity search
   - Persistencia en SSD (no HDD)

5. **Frontend Optimization**
   - Code splitting (React.lazy)
   - Lazy loading imágenes
   - Debounce en input (300ms)

**Mediciones Esperadas:**
```
Query Processing Breakdown:
1. Embedding generación: 200-400ms
2. Vector similarity search: 50-150ms
3. LLM inference: 1000-1500ms (20-30 tokens/s * 30-50 tokens)
4. Network overhead: 50-100ms
-----------------------------------
Total: 1.3-2.15 segundos ✅
```

**Plan B si > 2s:**
- Reducir context window (menos chunks)
- Usar modelo más pequeño (Llama 3.1:3b)
- Pre-generar respuestas para FAQs comunes

### Caching Strategy

**Backend:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_embedding(text: str):
    return embeddings.embed_query(text)
```

**Frontend:**
- React Query (futuro): Cache de respuestas API
- Service Worker (futuro): Offline support

### Database Optimization

**Indexes:**
```sql
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
```

**Connection Pooling (SQLite):**
```python
# SQLite no necesita pooling, pero para PostgreSQL:
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20
)
```

---

## Deployment Architecture

### Development Environment (Docker Compose)

```
┌─────────────────────────────────────────────────────┐
│                  Docker Host                        │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   frontend   │  │   backend    │  │  ollama  │ │
│  │  (Vite:5173) │  │ (Uvicorn:8000│  │ (:11434) │ │
│  │              │  │              │  │          │ │
│  │  React App   │──│  FastAPI     │──│  Llama   │ │
│  │              │  │              │  │  3.1 8B  │ │
│  └──────────────┘  └──────┬───────┘  └──────────┘ │
│                           │                         │
│                    ┌──────▼───────┐                │
│                    │  SQLite DB   │                │
│                    │  ChromaDB    │                │
│                    │  (volumes)   │                │
│                    └──────────────┘                │
└─────────────────────────────────────────────────────┘
         ▲                    ▲
         │                    │
    localhost:5173       localhost:8000
```

### Production Deployment (Documented for Report)

**Recomendación para Producción Futura:**

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Server                        │
│                                                              │
│  ┌───────────────┐                                          │
│  │   NGINX       │  (Reverse Proxy + SSL)                   │
│  │  :80 / :443   │                                          │
│  └───────┬───────┘                                          │
│          │                                                   │
│  ┌───────▼───────┐   ┌─────────────┐   ┌──────────────┐   │
│  │  Frontend     │   │  Backend    │   │  PostgreSQL  │   │
│  │  (Static)     │   │  (Gunicorn) │   │  + pgvector  │   │
│  │               │   │  + Workers  │   │              │   │
│  └───────────────┘   └──────┬──────┘   └──────────────┘   │
│                             │                               │
│                      ┌──────▼──────┐   ┌──────────────┐   │
│                      │   Ollama    │   │   Qdrant     │   │
│                      │  (GPU opt)  │   │  (Vectors)   │   │
│                      └─────────────┘   └──────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Monitoring: Prometheus + Grafana                   │   │
│  │  Logs: ELK Stack (Elasticsearch, Logstash, Kibana) │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Cambios para Producción:**
- SQLite → PostgreSQL 16 + pgvector
- ChromaDB → Qdrant (escalabilidad)
- Uvicorn → Gunicorn con múltiples workers
- HTTPS con Let's Encrypt
- Backup automático de DB
- Monitoring y alertas

---

## Development Environment

### Prerequisites

**Software Requerido:**

- **Docker 24.0+** y **Docker Compose 2.20+**
  - [Instalación](https://docs.docker.com/get-docker/)

- **Git 2.40+**
  - [Instalación](https://git-scm.com/downloads)

**Software Opcional (para desarrollo sin Docker):**

- **Python 3.12+**
  - [Instalación](https://www.python.org/downloads/)

- **Poetry 1.8+**
  - `curl -sSL https://install.python-poetry.org | python3 -`

- **Node.js 20+ / npm 10+**
  - [Instalación](https://nodejs.org/)

- **Ollama**
  - `curl -fsSL https://ollama.com/install.sh | sh`

**Hardware Recomendado:**

- **Mínimo:**
  - CPU: 4 cores
  - RAM: 16GB
  - Disco: 20GB libres (SSD recomendado)

- **Recomendado (GPU para Ollama):**
  - GPU: NVIDIA con 6GB+ VRAM (GTX 1660 o superior)
  - CUDA 11.8+
  - RAM: 32GB

### Setup Commands

#### Docker Compose (Recomendado)

```bash
# 1. Clonar repositorio
git clone https://github.com/andres-amaya/asistente-conocimiento.git
cd asistente-conocimiento

# 2. Copiar archivos de configuración
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Editar .env (opcional - valores default funcionan)
# nano backend/.env

# 4. Levantar servicios
docker-compose up --build

# 5. Pull modelo Llama (en contenedor ollama)
docker exec -it asistente-conocimiento-ollama-1 ollama pull llama3.1:8b-instruct-q4_K_M

# 6. Ejecutar migraciones de DB (primera vez)
docker exec -it asistente-conocimiento-backend-1 alembic upgrade head

# 7. Crear usuario admin (primera vez)
docker exec -it asistente-conocimiento-backend-1 python scripts/create_admin.py
```

**Acceso:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

#### Setup Manual (Sin Docker)

**Backend:**
```bash
cd backend

# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependencias
poetry install

# Activar entorno virtual
poetry shell

# Configurar .env
cp .env.example .env
nano .env  # Editar OLLAMA_HOST si es necesario

# Ejecutar migraciones
alembic upgrade head

# Crear usuario admin
python scripts/create_admin.py

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend

# Instalar dependencias
npm install

# Configurar .env
cp .env.example .env
nano .env  # Verificar VITE_API_URL

# Iniciar dev server
npm run dev
```

**Ollama (Local):**
```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Iniciar servicio
ollama serve

# En otra terminal, pull modelo
ollama pull llama3.1:8b-instruct-q4_K_M

# Verificar
ollama list
```

### Testing

**Backend (pytest):**
```bash
cd backend
poetry run pytest

# Con coverage
poetry run pytest --cov=app --cov-report=html
```

**Frontend (Vitest):**
```bash
cd frontend
npm run test

# Con UI
npm run test:ui
```

---

## Architecture Decision Records (ADRs)

### ADR-001: Python 3.12 como Lenguaje Backend

**Status:** Aceptado
**Date:** 2025-11-11
**Decision Makers:** Andres Amaya, Winston (Architect Agent)

**Context:**
El proyecto requiere un backend robusto para integrar IA generativa local (Ollama + Llama 3.1) con capacidades de procesamiento de documentos y API REST.

**Decision:**
Se selecciona **Python 3.12** como lenguaje principal del backend.

**Rationale:**
1. **Ecosistema IA:** Python domina el espacio de IA/ML (LangChain, HuggingFace, Ollama SDK oficial)
2. **Performance:** Python 3.12 ofrece mejoras de 10-15% vs 3.11 (PEP 669, faster comprehensions)
3. **Type Safety:** Type hints + Pydantic permiten validación robusta
4. **Comunidad:** Amplia documentación y soporte para RAG/LLM

**Alternatives Considered:**
- **Python 3.11:** Más estable, pero performance inferior
- **TypeScript (Node.js):** Mismo lenguaje que frontend, pero ecosistema IA menos maduro

**Consequences:**
- ✅ Integración trivial con Ollama, LangChain, ChromaDB
- ✅ Librerías ML/NLP abundantes
- ❌ Tipado opcional requiere disciplina con type hints

---

### ADR-002: FastAPI como Framework Web

**Status:** Aceptado
**Date:** 2025-11-11

**Context:**
Necesidad de API REST asíncrona para cumplir requisito RNF2 (respuestas < 2s) con streaming de respuestas LLM.

**Decision:**
Usar **FastAPI 0.115** como framework web.

**Rationale:**
1. **Async Nativo:** Soporta streaming responses para LLMs (crítico para UX)
2. **OpenAPI Automático:** Genera documentación Swagger/ReDoc gratis (ideal para informe académico)
3. **Validación Pydantic:** Type safety en requests/responses
4. **Performance:** Comparable a Node.js/Go (ASGI + async)

**Alternatives Considered:**
- **Flask:** Sync por defecto, sin validación automática
- **Django:** Overhead innecesario para API REST, async limitado

**Consequences:**
- ✅ Streaming responses trivial (async generators)
- ✅ API autodocumentada con ejemplos
- ❌ Menos "batteries included" que Django (requiere más setup)

---

### ADR-003: SQLite para Prototipo, PostgreSQL para Producción

**Status:** Aceptado
**Date:** 2025-11-11

**Context:**
Proyecto académico requiere demostración funcional rápida, pero debe documentar arquitectura escalable para producción.

**Decision:**
- **Prototipo:** SQLite 3.45+
- **Producción (documentada):** PostgreSQL 16 + pgvector

**Rationale:**
1. **Prototipo:**
   - Zero-config (archivo único `database.db`)
   - Portabilidad total (demo en cualquier máquina)
   - Suficiente para datos de prueba (<10k documentos)

2. **Producción:**
   - ACID completo, concurrencia robusta
   - pgvector permite embeddings en Postgres (elimina ChromaDB)
   - Escalabilidad horizontal

**Alternatives Considered:**
- **Solo PostgreSQL:** Overhead de configuración para prototipo
- **Solo SQLite:** No escalable a producción

**Consequences:**
- ✅ Demo funcional en < 1 hora de setup
- ✅ Migración a Postgres trivial (SQLAlchemy abstrae DB)
- ✅ Informe documenta path de producción realista
- ❌ Doble testing necesario (SQLite + Postgres)

---

### ADR-004: Ollama + Llama 3.1 8B Local

**Status:** Aceptado
**Date:** 2025-11-11

**Context:**
Requisito RS5 y Ley 19.628 requieren datos 100% on-premise. Alternativas cloud (OpenAI, Anthropic) violan privacidad.

**Decision:**
**Ollama 0.6.0** como runtime + **Llama 3.1 8B Instruct (q4_K_M)** como modelo LLM.

**Rationale:**
1. **Cumplimiento Legal:** Datos nunca abandonan infraestructura local (Ley 19.628)
2. **Sin Costos Recurrentes:** No API keys, no límites de tokens
3. **Performance Adecuado:** 10-20 tokens/s (CPU), 40-60 tokens/s (GPU) → cumple RNF2
4. **Modelo Open Source:** Llama 3.1 bajo licencia Meta (uso académico permitido)

**Alternatives Considered:**
- **OpenAI API:** Viola Ley 19.628, costos por token
- **Modelos más pequeños (3B):** Calidad de respuestas inferior
- **Modelos más grandes (70B):** Hardware prohibitivo

**Consequences:**
- ✅ Privacidad 100% garantizada
- ✅ Replicable sin API keys
- ❌ Requiere hardware decente (16GB RAM mínimo)
- ❌ Performance inferior a GPT-4 (aceptable para prototipo)

---

### ADR-005: ChromaDB como Vector Store (Prototipo)

**Status:** Aceptado
**Date:** 2025-11-11

**Context:**
RAG requiere almacenamiento de embeddings para similarity search. Opciones van desde bibliotecas simples (FAISS) a bases de datos completas (Qdrant).

**Decision:**
**ChromaDB 0.5.5** para prototipo, con migración documentada a **Qdrant** o **pgvector** para producción.

**Rationale:**
1. **Simplicidad:** Setup en 2 líneas de código, persistencia automática
2. **Portabilidad:** Base vectorial = carpeta `chroma_db/` (fácil backup/demo)
3. **LangChain Integration:** Soporte nativo, ejemplos abundantes

**Alternatives Considered:**
- **FAISS:** Máximo performance, pero no es base de datos (solo biblioteca)
- **Qdrant:** Producción-ready, pero overkill para prototipo (requiere servidor Docker extra)
- **Pinecone:** Cloud-only, viola Ley 19.628

**Consequences:**
- ✅ Setup prototipo en minutos
- ✅ Suficiente para < 50k documentos
- ❌ No escala a millones de vectores
- ➡️ Migración a Qdrant/pgvector documentada para producción

---

### ADR-006: Vite + React 18 + TypeScript (Frontend)

**Status:** Aceptado
**Date:** 2025-11-11

**Context:**
UX Design especifica React + shadcn/ui. Necesidad de build tool moderno para cumplir RNF2 (< 2s).

**Decision:**
**Vite 6.0** + **React 18.3** + **TypeScript 5.6**.

**Rationale:**
1. **Vite:** Build ultra-rápido (HMR instantáneo), ideal para desarrollo
2. **React 18:** Concurrent rendering, Suspense para lazy loading
3. **TypeScript:** Type safety end-to-end (backend Pydantic → frontend TS)

**Alternatives Considered:**
- **Next.js:** SSR innecesario para SPA, overhead mayor
- **Create React App:** Deprecado en 2025

**Consequences:**
- ✅ Dev server instantáneo (< 1s reload)
- ✅ Type safety completo (interfaces compartidas)
- ❌ No SSR/SEO optimization (irrelevante para app interna)

---

### ADR-007: Docker Compose para Desarrollo y Demo

**Status:** Aceptado
**Date:** 2025-11-11

**Context:**
Proyecto académico debe ser reproducible para evaluación. Setup manual (Python, Node, Ollama) es propenso a errores.

**Decision:**
**Docker Compose 2.20+** como entorno de desarrollo y demostración.

**Rationale:**
1. **Reproducibilidad:** `docker-compose up` funciona en cualquier OS con Docker
2. **Aislamiento:** Dependencias encapsuladas (no contamina sistema)
3. **Demo Académica:** Profesores pueden ejecutar prototipo sin configurar Python/Node

**Alternatives Considered:**
- **Instalación manual:** No reproducible, "works on my machine"
- **Kubernetes:** Overkill absoluto para prototipo

**Consequences:**
- ✅ Setup completo en 1 comando
- ✅ Entorno idéntico dev/demo
- ❌ Requiere Docker instalado (~5GB descarga inicial)

---

## Conclusión

Esta arquitectura implementa un sistema de **3 capas** (Presentación, Lógica, Datos) con énfasis en:

- **Privacidad y Cumplimiento:** IA 100% local (Ollama + Llama 3.1), cumplimiento Ley 19.628
- **Performance:** Arquitectura asíncrona (FastAPI), streaming responses, caching estratégico
- **Escalabilidad:** Path claro SQLite → PostgreSQL, ChromaDB → Qdrant documentado
- **Reproducibilidad:** Docker Compose permite setup completo en minutos
- **Seguridad Multi-capa:** JWT, bcrypt, CORS, audit logging, input validation

**Próximos Pasos (Implementación):**
1. Ejecutar `sprint-planning` para generar plan de implementación
2. Usar `dev-story` workflow para implementar cada épica
3. Validar arquitectura con pruebas funcionales y de seguridad
4. Generar informe de prefactibilidad basado en esta arquitectura

---

_Generated by BMAD Decision Architecture Workflow v1.3_
_Date: 2025-11-11_
_For: Andres Amaya Garces_
_Academic Context: Proyecto de Título - Universidad de Las Américas_
