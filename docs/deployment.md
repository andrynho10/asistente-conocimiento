# Guía de Despliegue - Asistente de Conocimiento Corporativo

Esta guía proporciona instrucciones detalladas para el despliegue del sistema en diferentes ambientes.

## Tabla de Contenidos

- [Requisitos del Sistema](#requisitos-del-sistema)
- [Ambiente de Desarrollo Local](#ambiente-de-desarrollo-local)
- [Troubleshooting Común](#troubleshooting-común)
- [Verificación de Instalación](#verificación-de-instalación)
- [Variables de Entorno](#variables-de-entorno)

---

## Requisitos del Sistema

### Software Requerido

#### Backend
- **Python 3.12+** - Lenguaje de programación principal
- **Poetry 1.8+** - Gestor de dependencias y entornos virtuales
- **SQLite 3.45+** (desarrollo) / **PostgreSQL 16+** (producción)
- **Git** - Control de versiones

#### Frontend
- **Node.js 18+** - Runtime de JavaScript
- **npm 9+** - Gestor de paquetes (incluido con Node.js)

#### Opcional (para funcionalidades de IA)
- **Ollama** - Runtime local para modelos LLM
- **Llama 3.1 8B** - Modelo de lenguaje (via Ollama)

### Requisitos de Hardware

**Desarrollo Local (Mínimo):**
- CPU: 2 cores
- RAM: 4 GB
- Disco: 10 GB libres

**Desarrollo Local (Recomendado):**
- CPU: 4+ cores
- RAM: 8+ GB (16 GB si usas Ollama)
- Disco: 20+ GB libres
- SSD para mejor rendimiento de base de datos

**Producción (Recomendado):**
- CPU: 4+ cores
- RAM: 16+ GB (32 GB si usas Ollama)
- Disco: 50+ GB libres (SSD)

---

## Ambiente de Desarrollo Local

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd asistente-conocimiento
```

### 2. Configurar Backend

#### 2.1 Instalar Dependencias

```bash
cd backend
poetry install
```

Esto creará un entorno virtual automáticamente e instalará todas las dependencias.

#### 2.2 Configurar Variables de Entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` y configura las variables críticas:

```bash
# Generar SECRET_KEY seguro
python -c "import secrets; print(secrets.token_hex(32))"
```

Copia el resultado y actualiza tu `.env`:

```env
# Backend/.env
DATABASE_URL=sqlite:///./database/asistente_conocimiento.db
SECRET_KEY=<tu-clave-generada-aqui>
JWT_EXPIRATION_HOURS=24
JWT_ALGORITHM=HS256
FASTAPI_ENV=development
DEBUG=True
LOG_LEVEL=info
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Ollama (opcional para desarrollo)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500
LLM_CONTEXT_SIZE=8192
```

#### 2.3 Inicializar Base de Datos

```bash
# Crear directorio de base de datos
mkdir -p database

# Ejecutar migraciones
poetry run alembic upgrade head
```

#### 2.4 Verificar Configuración

```bash
# Ejecutar tests
poetry run pytest tests/ -v

# Deberías ver: 55 passed
```

#### 2.5 Iniciar Servidor Backend

```bash
poetry run python run.py
```

El backend estará disponible en:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### 3. Configurar Frontend

#### 3.1 Instalar Dependencias

```bash
cd ../frontend
npm install
```

#### 3.2 Configurar Variables de Entorno

```bash
cp .env.example .env
```

Edita `.env`:

```env
# Frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

#### 3.3 Iniciar Servidor Frontend

```bash
npm run dev
```

El frontend estará disponible en: http://localhost:5173

### 4. Verificar Instalación Completa

1. **Abrir navegador:** http://localhost:5173
2. **Iniciar sesión** con credenciales de prueba:
   - Username: `admin`
   - Password: `admin123`
3. **Verificar** que puedes acceder al dashboard

---

## Troubleshooting Común

### 1. "ModuleNotFoundError: No module named 'app'"

**Problema:** Python no puede encontrar el módulo `app`.

**Causa:** No estás usando Poetry o estás en el directorio incorrecto.

**Solución:**
```bash
# Asegúrate de estar en backend/
cd backend

# Usa poetry run para ejecutar comandos
poetry run python run.py

# O activa el shell de Poetry
poetry shell
python run.py
```

---

### 2. "Database connection failed" o "database is locked"

**Problema:** No se puede conectar a la base de datos SQLite.

**Causa:** Base de datos en uso por otro proceso o directorio inexistente.

**Solución:**

**Opción A: Recrear base de datos**
```bash
# Detener todos los procesos que usan la BD
# En Windows: Cerrar otras ventanas de Python
# En Linux/Mac: lsof database/asistente_conocimiento.db

# Eliminar BD y recrear
rm database/asistente_conocimiento.db
poetry run alembic upgrade head
```

**Opción B: Verificar permisos**
```bash
# Linux/Mac: Verificar permisos del directorio
ls -la database/
chmod 755 database/
```

**Opción C: Usar otra ubicación**
```env
# En .env, cambiar ruta de base de datos
DATABASE_URL=sqlite:///./test_db.db
```

---

### 3. "Port already in use" (Puerto 8000 o 5173 en uso)

**Problema:** El puerto ya está siendo usado por otro proceso.

**Solución en Windows:**
```bash
# Ver qué proceso usa el puerto
netstat -ano | findstr :8000

# Matar el proceso (reemplaza <PID> con el número)
taskkill /PID <PID> /F

# O cambiar el puerto
# Backend: editar run.py, cambiar port=8000 a port=8001
# Frontend: npm run dev -- --port 5174
```

**Solución en Linux/Mac:**
```bash
# Ver qué proceso usa el puerto
lsof -i :8000

# Matar el proceso
kill -9 <PID>

# O cambiar el puerto
poetry run uvicorn app.main:app --reload --port 8001
```

---

### 4. "Environment variables not loaded"

**Problema:** Las variables de entorno no se cargan correctamente.

**Causa:** Archivo `.env` no existe o tiene formato incorrecto.

**Solución:**
```bash
# Verificar que .env existe
ls -la .env

# Si no existe, crearlo desde template
cp .env.example .env

# Verificar formato del archivo (sin espacios extras)
cat .env

# Ejemplo correcto:
# SECRET_KEY=valor
# DATABASE_URL=sqlite:///./database/asistente_conocimiento.db
```

---

### 5. "SECRET_KEY validation error"

**Problema:** SECRET_KEY no cumple requisitos de seguridad.

**Causa:** SECRET_KEY es muy corto o usa un valor inseguro por defecto.

**Solución:**
```bash
# Generar clave segura (mínimo 32 caracteres = 64 hex)
python -c "import secrets; print(secrets.token_hex(32))"

# Copiar el resultado en .env
# SECRET_KEY=a1b2c3d4e5f6...
```

**Valores prohibidos (inseguros):**
- `your-secret-key-here...`
- `your-super-secret-jwt-key...`
- `secret`, `test`, `dev`

---

### 6. "Alembic: Can't locate revision"

**Problema:** Estado inconsistente de migraciones de base de datos.

**Causa:** Base de datos y migraciones desincronizadas.

**Solución:**

**Opción A: Marcar como actualizada**
```bash
poetry run alembic stamp head
```

**Opción B: Recrear base de datos**
```bash
rm database/asistente_conocimiento.db
poetry run alembic upgrade head
```

**Opción C: Ver historial de migraciones**
```bash
poetry run alembic history
poetry run alembic current
```

---

### 7. Tests Fallan: "AssertionError" o "fixture not found"

**Problema:** Tests no pasan correctamente.

**Causa:** Base de datos de prueba contaminada o configuración incorrecta.

**Solución:**
```bash
# Eliminar caché de pytest
rm -rf .pytest_cache
rm -rf __pycache__

# Eliminar base de datos de prueba
rm test_database.db

# Ejecutar con verbose para ver errores
poetry run pytest tests/ -v -s

# Ejecutar un test específico
poetry run pytest tests/test_auth.py::test_login_valid_credentials -v
```

---

### 8. "Python version mismatch"

**Problema:** Versión de Python incompatible.

**Causa:** Python instalado es menor a 3.12.

**Solución:**
```bash
# Verificar versión
python --version

# Si es < 3.12, actualizar Python
# Descargar desde: https://www.python.org/downloads/

# Recrear entorno virtual con nueva versión
poetry env remove python
poetry install
```

---

### 9. "npm ERR! Cannot find module" (Frontend)

**Problema:** Dependencias de frontend no instaladas.

**Solución:**
```bash
cd frontend

# Eliminar node_modules y reinstalar
rm -rf node_modules package-lock.json
npm install

# Verificar versión de Node
node --version  # Debe ser 18+
```

---

### 10. "CORS Error" en el Frontend

**Problema:** Navegador bloquea peticiones del frontend al backend.

**Causa:** CORS no configurado correctamente.

**Solución:**
```env
# Backend/.env - Agregar origen del frontend
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Si usas otro puerto:
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
```

Reiniciar el servidor backend después del cambio.

---

### 11. "Ollama connection error" (Opcional)

**Problema:** No se puede conectar al servidor Ollama.

**Causa:** Ollama no está instalado o no está corriendo.

**Solución:**
```bash
# Instalar Ollama (si no está instalado)
# Windows/Mac: https://ollama.ai/download
# Linux: curl https://ollama.ai/install.sh | sh

# Iniciar servidor Ollama
ollama serve

# En otra terminal, descargar modelo
ollama pull llama3.1:8b-instruct-q4_K_M

# Verificar que el modelo está disponible
ollama list
```

---

## Verificación de Instalación

### Checklist de Verificación

Usa este checklist para confirmar que todo está configurado correctamente:

#### Backend

- [ ] Python 3.12+ instalado: `python --version`
- [ ] Poetry instalado: `poetry --version`
- [ ] Dependencias instaladas: `poetry show`
- [ ] Archivo `.env` existe y configurado
- [ ] SECRET_KEY generado (64+ caracteres hex)
- [ ] Base de datos inicializada: `ls database/asistente_conocimiento.db`
- [ ] Migraciones aplicadas: `poetry run alembic current`
- [ ] Tests pasan 100%: `poetry run pytest tests/ -v`
- [ ] Servidor inicia correctamente: `poetry run python run.py`
- [ ] Endpoint de salud responde: `curl http://localhost:8000/api/health`

#### Frontend

- [ ] Node.js 18+ instalado: `node --version`
- [ ] npm instalado: `npm --version`
- [ ] Dependencias instaladas: `npm list --depth=0`
- [ ] Archivo `.env` existe y configurado
- [ ] Servidor inicia correctamente: `npm run dev`
- [ ] Navegador abre en: http://localhost:5173
- [ ] Login funciona con credenciales de prueba

#### Integración

- [ ] Frontend puede hacer login al backend
- [ ] No hay errores CORS en la consola del navegador
- [ ] Dashboard carga correctamente después del login

### Comandos de Verificación Rápida

```bash
# Backend health check
curl http://localhost:8000/api/health

# Debería retornar: {"status":"ok","version":"1.0.0"}

# Backend docs check
curl http://localhost:8000/docs

# Debería retornar HTML de Swagger UI

# Test login endpoint
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Debería retornar token JWT
```

---

## Variables de Entorno

### Backend

| Variable | Requerida | Descripción | Ejemplo | Notas |
|----------|-----------|-------------|---------|-------|
| `DATABASE_URL` | No | URL de conexión a BD | `sqlite:///./database/asistente_conocimiento.db` | SQLite por defecto |
| `SECRET_KEY` | **Sí** | Clave secreta JWT | (generado con `secrets.token_hex(32)`) | Mínimo 32 caracteres |
| `JWT_EXPIRATION_HOURS` | No | Horas de expiración JWT | `24` | Por defecto 24h |
| `JWT_ALGORITHM` | No | Algoritmo JWT | `HS256` | Recomendado HS256 |
| `FASTAPI_ENV` | No | Entorno de ejecución | `development` | development, testing, production |
| `DEBUG` | No | Modo debug | `True` | Solo `True` en desarrollo |
| `LOG_LEVEL` | No | Nivel de logging | `info` | debug, info, warning, error |
| `ALLOWED_ORIGINS` | No | Orígenes CORS | `http://localhost:5173` | Separados por comas |
| `OLLAMA_HOST` | No | URL servidor Ollama | `http://localhost:11434` | Opcional para IA |
| `OLLAMA_MODEL` | No | Modelo LLM | `llama3.1:8b-instruct-q4_K_M` | Opcional para IA |

### Frontend

| Variable | Requerida | Descripción | Ejemplo |
|----------|-----------|-------------|---------|
| `VITE_API_BASE_URL` | **Sí** | URL del backend | `http://localhost:8000` |

### Ejemplos por Ambiente

**Desarrollo:**
```env
FASTAPI_ENV=development
DEBUG=True
DATABASE_URL=sqlite:///./database/asistente_conocimiento.db
SECRET_KEY=<generado>
```

**Testing:**
```env
FASTAPI_ENV=testing
DEBUG=False
DATABASE_URL=sqlite:///./test_database.db
SECRET_KEY=<generado>
```

**Producción:**
```env
FASTAPI_ENV=production
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost:5432/asistente_db
SECRET_KEY=<generado-seguro>
ALLOWED_ORIGINS=https://asistente.empresa.com
```

---

## Próximos Pasos

Una vez completada la instalación y verificación:

1. **Explorar la API** - Visita http://localhost:8000/docs para ver todos los endpoints
2. **Revisar arquitectura** - Lee `docs/architecture.md` para entender el diseño del sistema
3. **Consultar PRD** - Revisa `docs/PRD.md` para ver requisitos completos
4. **Desarrollar nuevas features** - Comienza a implementar según `docs/epics.md`

---

## Soporte

Si encuentras problemas no cubiertos en esta guía:

1. Revisa la sección **Troubleshooting Común** arriba
2. Consulta `backend/README.md` para instrucciones específicas del backend
3. Verifica los logs del servidor para mensajes de error específicos
4. Asegúrate de que todas las variables de entorno requeridas estén configuradas
5. Ejecuta los tests para identificar problemas: `poetry run pytest tests/ -v`

---

**Última actualización:** 2025-11-12
**Versión del documento:** 1.0.0
