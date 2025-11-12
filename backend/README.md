# Asistente de Conocimiento Corporativo - Backend

Backend para el sistema de IA Generativa para gestión del conocimiento y capacitación organizacional.

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.12+** - [Descargar Python](https://www.python.org/downloads/)
- **pip** - Gestor de paquetes de Python (incluido con Python)
- **Poetry** - Gestor de dependencias y entornos virtuales
  ```bash
  pip install poetry
  ```
- **Git** - Control de versiones (opcional pero recomendado)

## Instalación

Sigue estos pasos para configurar el proyecto en tu máquina local:

### 1. Clonar el Repositorio (si aplica)

```bash
git clone <url-repositorio>
cd asistente-conocimiento/backend
```

### 2. Crear Entorno Virtual e Instalar Dependencias

Poetry manejará automáticamente la creación del entorno virtual y la instalación de dependencias:

```bash
poetry install
```

Esto instalará todas las dependencias listadas en `pyproject.toml`, incluyendo:
- FastAPI y Uvicorn (servidor web)
- SQLModel y Alembic (base de datos)
- JWT y Passlib (autenticación)
- pytest (testing)
- python-dotenv y pydantic-settings (configuración)

### 3. Configurar Variables de Entorno

Crea un archivo `.env` basado en el template proporcionado:

```bash
cp .env.example .env
```

**IMPORTANTE:** Edita el archivo `.env` y configura los siguientes valores críticos:

1. **Genera una clave secreta segura:**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Copia el resultado y reemplaza `SECRET_KEY` en tu `.env`

2. **Ajusta otras variables según tu entorno:**
   - `DATABASE_URL` - Ruta de la base de datos SQLite (por defecto está ok para desarrollo)
   - `FASTAPI_ENV` - Mantén como `development` para desarrollo local
   - `DEBUG` - Mantén como `True` para desarrollo local

Ejemplo de `.env` mínimo funcional:
```env
DATABASE_URL=sqlite:///./database/asistente_conocimiento.db
SECRET_KEY=tu-clave-secreta-generada-de-64-caracteres-hexadecimales-aqui
JWT_EXPIRATION_HOURS=24
JWT_ALGORITHM=HS256
FASTAPI_ENV=development
DEBUG=True
LOG_LEVEL=info
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 4. Inicializar la Base de Datos

Crea las tablas necesarias en la base de datos:

```bash
poetry run alembic upgrade head
```

Si encuentras problemas, puedes recrear las migraciones:

```bash
poetry run alembic stamp head
```

### 5. Verificar la Instalación

Ejecuta los tests para verificar que todo está configurado correctamente:

```bash
poetry run pytest tests/ -v
```

Deberías ver todos los tests pasando (✓).

## Ejecución

### Iniciar el Servidor de Desarrollo

Para iniciar el servidor FastAPI en modo desarrollo con auto-reload:

```bash
poetry run python run.py
```

O alternativamente usando uvicorn directamente:

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en:
- **API:** http://localhost:8000
- **Documentación interactiva (Swagger):** http://localhost:8000/docs
- **Documentación alternativa (ReDoc):** http://localhost:8000/redoc

### Credenciales de Prueba

El sistema crea automáticamente un usuario administrador para desarrollo:

- **Username:** `admin`
- **Password:** `admin123`

**⚠️ IMPORTANTE:** Cambia estas credenciales en producción.

## Testing

### Ejecutar Todos los Tests

```bash
poetry run pytest tests/
```

### Ejecutar Tests con Modo Verbose

```bash
poetry run pytest tests/ -v
```

### Ejecutar Tests con Cobertura

```bash
poetry run pytest tests/ --cov=app --cov-report=html
```

Esto generará un reporte de cobertura en `htmlcov/index.html`.

### Ejecutar Tests Específicos

```bash
# Solo tests de autenticación
poetry run pytest tests/test_auth.py -v

# Solo tests de configuración
poetry run pytest tests/test_config.py -v

# Un test específico
poetry run pytest tests/test_auth.py::test_login_valido -v
```

### Estructura de Tests

```
backend/tests/
├── test_auth.py      # Tests de autenticación y endpoints protegidos
├── test_config.py    # Tests de configuración y variables de entorno
└── conftest.py       # Fixtures compartidas (si aplica)
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'app'"

**Causa:** Python no encuentra el módulo `app` porque no está en el PYTHONPATH.

**Solución:**
```bash
# Asegúrate de estar en el directorio backend/
cd backend

# Usa poetry run para ejecutar comandos
poetry run python run.py
```

### Error: "Database connection failed" o "database is locked"

**Causa:** La base de datos SQLite está siendo usada por otro proceso o no existe el directorio.

**Solución:**
```bash
# Crear directorio de base de datos si no existe
mkdir -p database

# Verificar que no hay otros procesos usando la BD
# En Windows, cierra otras sesiones de Python
# En Linux/Mac:
lsof database/asistente_conocimiento.db

# Reiniciar las migraciones
poetry run alembic upgrade head
```

### Error: "Port already in use" (Puerto 8000 en uso)

**Causa:** Otro proceso está usando el puerto 8000.

**Solución en Windows:**
```bash
# Ver qué proceso usa el puerto
netstat -ano | findstr :8000

# Matar el proceso (reemplaza PID con el número de proceso)
taskkill /PID <PID> /F
```

**Solución en Linux/Mac:**
```bash
# Ver qué proceso usa el puerto
lsof -i :8000

# Matar el proceso
kill -9 <PID>

# O usar un puerto diferente
poetry run uvicorn app.main:app --reload --port 8001
```

### Error: "Environment variables not loaded" o "SECRET_KEY validation error"

**Causa:** El archivo `.env` no existe o tiene valores inválidos.

**Solución:**
```bash
# Verificar que .env existe
ls -la .env

# Si no existe, crearlo desde el template
cp .env.example .env

# Generar SECRET_KEY válido (mínimo 32 caracteres)
python -c "import secrets; print(secrets.token_hex(32))"

# Editar .env y agregar el SECRET_KEY generado
```

### Error: "Alembic: Can't locate revision identified by 'xxxx'"

**Causa:** Estado inconsistente de migraciones de base de datos.

**Solución:**
```bash
# Marcar como actualizada sin ejecutar migraciones
poetry run alembic stamp head

# O eliminar la base de datos y recrearla
rm database/asistente_conocimiento.db
poetry run alembic upgrade head
```

### Tests Fallan: "AssertionError" o "fixture not found"

**Causa:** Base de datos de prueba contaminada o configuración incorrecta.

**Solución:**
```bash
# Eliminar base de datos de prueba
rm test_database.db

# Ejecutar tests con output verbose para ver el error exacto
poetry run pytest tests/ -v -s

# Verificar que pytest.ini está configurado correctamente
cat pyproject.toml | grep pytest -A 5
```

### Warning: "Python version mismatch"

**Causa:** La versión de Python activa no coincide con la requerida (3.12+).

**Solución:**
```bash
# Verificar versión de Python
python --version

# Si es menor a 3.12, actualizar Python
# Luego recrear el entorno virtual
poetry env remove python
poetry install
```

## Estructura del Proyecto

```
backend/
├── app/
│   ├── main.py              # Aplicación FastAPI principal
│   ├── core/
│   │   ├── config.py        # Configuración centralizada (python-dotenv + Pydantic)
│   │   ├── database.py      # Configuración de base de datos
│   │   └── security.py      # Utilidades de seguridad (JWT, passwords)
│   ├── auth/
│   │   ├── routes.py        # Endpoints de autenticación
│   │   ├── service.py       # Lógica de negocio de auth
│   │   └── models.py        # Modelos de usuario y tokens
│   └── models/
│       └── user.py          # Modelo de datos de usuario
├── tests/
│   ├── test_auth.py         # Tests de autenticación
│   └── test_config.py       # Tests de configuración
├── database/                # Base de datos SQLite (creada automáticamente)
├── alembic/                 # Migraciones de base de datos
├── run.py                   # Script de inicio del servidor
├── pyproject.toml           # Dependencias y configuración del proyecto
├── .env                     # Variables de entorno (NO incluir en Git)
├── .env.example             # Template de variables de entorno
└── README.md                # Este archivo
```

## Comandos Útiles

```bash
# Activar shell de Poetry (opcional, para no usar "poetry run" cada vez)
poetry shell

# Ver dependencias instaladas
poetry show

# Agregar nueva dependencia
poetry add nombre-paquete

# Agregar dependencia de desarrollo
poetry add --group dev nombre-paquete

# Actualizar dependencias
poetry update

# Salir del shell de Poetry
exit
```

## Próximos Pasos

1. ✅ **Configuración completada** - El backend está listo para desarrollo
2. 📚 **Revisar documentación** - Lee `docs/deployment.md` para más detalles
3. 🔧 **Explorar API** - Visita http://localhost:8000/docs para ver los endpoints
4. 🧪 **Ejecutar tests** - Verifica que todo funciona: `poetry run pytest tests/ -v`
5. 💻 **Empezar a desarrollar** - Comienza a implementar nuevas funcionalidades

## Documentación Adicional

- **Deployment Guide:** `../docs/deployment.md` - Guía detallada de despliegue
- **API Documentation:** http://localhost:8000/docs (cuando el servidor esté corriendo)
- **Architecture:** `../docs/architecture.md` - Diseño y decisiones técnicas
- **PRD:** `../docs/PRD.md` - Requerimientos del producto

## Soporte

Si encuentras problemas no cubiertos en esta guía:

1. Revisa la sección **Troubleshooting** arriba
2. Consulta `../docs/deployment.md` para más detalles
3. Verifica los logs del servidor para mensajes de error específicos
4. Asegúrate de que todas las variables de entorno estén configuradas correctamente

---

**Versión:** 0.1.0
**Última actualización:** 2025-11-12
