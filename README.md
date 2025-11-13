# Asistente de Conocimiento Corporativo

Sistema de IA Generativa para Capacitación Corporativa - Proyecto Académico

## Descripción del Proyecto

El Asistente de Conocimiento Corporativo es un sistema de IA generativa diseñado para facilitar la capacitación y gestión del conocimiento en entornos corporativos. Utiliza modelos de lenguaje de gran escala (LLM) ejecutados localmente para procesar documentación interna y generar contenido formativo personalizado.

**Contexto Académico:** Este proyecto es desarrollado como parte de un trabajo académico de investigación en tecnologías de IA aplicadas a la formación empresarial, con énfasis en privacidad de datos y cumplimiento normativo chileno (Ley 19.628).

### Características Principales

- **Gestión de Documentos:** Carga, indexación y búsqueda de documentación corporativa
- **Consultas en Lenguaje Natural:** Interacción conversacional con el conocimiento corporativo mediante LLM local (Llama 3.1)
- **Generación de Contenido Formativo:** Creación automática de resúmenes, quizzes y rutas de aprendizaje
- **Seguridad y Privacidad:** Ejecución local del modelo, cifrado de datos, auditoría completa
- **Cumplimiento Normativo:** Anonimización de datos personales conforme a legislación chilena

## Tecnologías Utilizadas

### Backend
- Python 3.12
- FastAPI 0.115.0
- SQLModel 0.0.14 (ORM)
- SQLite 3.45+ (desarrollo) / PostgreSQL 16+ (producción)
- Poetry 1.8+ (gestión de dependencias)
- Ollama + Llama 3.1 8B (modelo de lenguaje local)

### Frontend
- Vite 6.0
- React 18.3.0
- TypeScript
- Tailwind CSS + shadcn/ui
- Zustand 5.0.0 (gestión de estado)
- Axios 1.7.0 (cliente HTTP)

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.12** o superior
- **Poetry 1.8+** para gestión de dependencias del backend
- **Node.js 18+** y npm para el frontend
- **Ollama** (opcional, para funcionalidades de IA generativa)

## Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/andrynho10/asistente-conocimiento.git
cd asistente-conocimiento
```

### 2. Configurar Variables de Entorno

#### Backend

```bash
cd backend
cp .env.example .env
```

Edita el archivo `.env` y configura las variables necesarias:
- **SECRET_KEY:** Genera una clave segura con `python -c "import secrets; print(secrets.token_hex(32))"`
- Ajusta otras variables según tu entorno de desarrollo

#### Frontend

```bash
cd ../frontend
cp .env.example .env
```

### 3. Instalar Dependencias del Backend

```bash
cd backend
poetry install
```

Esto creará un entorno virtual e instalará todas las dependencias especificadas en `pyproject.toml`.

### 4. Instalar Dependencias del Frontend

```bash
cd ../frontend
npm install
```

## Ejecución

### Backend (API REST)

Desde la carpeta `backend/`:

```bash
poetry run uvicorn app.main:app --reload
```

El backend estará disponible en: `http://localhost:8000`

Documentación interactiva de la API: `http://localhost:8000/docs`

### Frontend (Interfaz de Usuario)

Desde la carpeta `frontend/`:

```bash
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

## Testing

### Backend

Ejecutar tests con pytest:

```bash
cd backend
poetry run pytest
```

Para ver cobertura de tests:

```bash
poetry run pytest --cov=app --cov-report=html
```

### Frontend

```bash
cd frontend
npm run test
```

## Estructura del Proyecto

```
asistente-conocimiento/
├── backend/
│   ├── app/
│   │   ├── models/       # Modelos de datos (SQLModel)
│   │   ├── routes/       # Endpoints de la API
│   │   ├── services/     # Lógica de negocio
│   │   ├── schemas/      # Esquemas Pydantic
│   │   ├── utils/        # Utilidades
│   │   ├── api/          # Configuración de API
│   │   └── core/         # Configuración central
│   ├── tests/            # Tests del backend
│   ├── alembic/          # Migraciones de base de datos
│   ├── data/             # Datos y documentos
│   ├── pyproject.toml    # Dependencias Poetry
│   └── .env.example      # Template de variables de entorno
├── frontend/
│   ├── src/
│   │   ├── components/   # Componentes React reutilizables
│   │   ├── pages/        # Páginas de la aplicación
│   │   ├── store/        # Estado global (Zustand)
│   │   ├── services/     # Servicios de API
│   │   ├── types/        # Tipos TypeScript
│   │   ├── hooks/        # Custom React hooks
│   │   ├── lib/          # Librerías y utilidades
│   │   └── styles/       # Estilos globales
│   ├── package.json      # Dependencias npm
│   └── .env.example      # Template de variables de entorno
├── database/             # Archivos de base de datos (SQLite en desarrollo)
├── docs/                 # Documentación adicional del proyecto
└── README.md             # Este archivo
```

## Documentación Adicional

Para más información sobre la arquitectura, decisiones técnicas y guías de desarrollo, consulta:

- `docs/architecture.md` - Documentación de arquitectura del sistema
- `docs/epics.md` - Épicas y planificación del proyecto
- `docs/PRD.md` - Documento de requisitos del producto

## Contribución

Este es un proyecto académico. Para contribuir:

1. Crea una rama feature desde `main`
2. Realiza tus cambios siguiendo las convenciones del proyecto
3. Ejecuta los tests para asegurar que todo funciona
4. Crea un Pull Request con descripción detallada de los cambios

## Licencia

Proyecto Académico - Universidad [Nombre] - 2025

## Contacto

Para preguntas o soporte sobre este proyecto académico, contacta a:
- Equipo de Desarrollo: dev@asistente-conocimiento.cl
