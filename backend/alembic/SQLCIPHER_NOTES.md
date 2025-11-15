# Notas sobre SQLCipher y Alembic (Story 5.3)

## Introducción

Las migraciones Alembic son **completamente transparentes** a SQLCipher. No se requieren cambios en el código de migraciones.

## Cómo Funciona

SQLCipher se configura en el startup de la aplicación mediante `PRAGMA key`:

```python
# backend/app/database.py
from sqlalchemy import event

def _configure_sqlite_encryption(dbapi_conn, connection_record):
    if DB_ENCRYPTION_KEY:
        dbapi_conn.execute(f"PRAGMA key = '{DB_ENCRYPTION_KEY}'")

event.listen(engine, "connect", _configure_sqlite_encryption)
```

Alembic solo ve la conexión **ya desencriptada**, por lo que:
- ✅ Las migraciones funcionan sin cambios
- ✅ Las transacciones se comportan normalmente
- ✅ El cifrado es completamente transparente

## Ejecutar Migraciones con SQLCipher

```bash
# Desarrollo (con DB_ENCRYPTION_KEY en .env)
cd backend
poetry run alembic upgrade head

# El PRAGMA key se ejecuta automáticamente en cada conexión
# No se requieren pasos adicionales
```

## Verificar que la BD está Cifrada

```bash
# Conexión normal (sin clave)
sqlite3 database/asistente_conocimiento.db
> .tables
Error: file is encrypted or is not a database
```

```bash
# Con clave (usando SQLCipher)
# Nota: Requiere sqlcipher3 compilado localmente
sqlcipher database/asistente_conocimiento.db
sqlite> PRAGMA key = 'base64-key-here';
sqlite> .tables
# Funciona correctamente
```

## Backup y Restore de BD Cifrada

### Backup

```bash
# El archivo .db contiene datos cifrados
cp database/asistente_conocimiento.db database/asistente_conocimiento.db.backup

# El backup está encriptado - no se puede leer sin la clave
```

### Restore

```bash
# Restaurar es simple (archivo ya está encriptado)
cp database/asistente_conocimiento.db.backup database/asistente_conocimiento.db

# Ejecutar migraciones si es necesario
alembic upgrade head
```

## Cambiar la Clave de Cifrado

El cambio de clave requiere re-encriptar toda la BD (proceso manual):

1. Generar nueva clave:
   ```bash
   python scripts/generate_encryption_keys.py
   ```

2. Re-encriptar (usando herramienta SQLCipher):
   ```bash
   # Esto requiere SQLCipher compilado con soporte para rekey
   sqlcipher database/asistente_conocimiento.db
   sqlite> PRAGMA key = 'old-key';
   sqlite> PRAGMA rekey = 'new-key';
   sqlite> .quit
   ```

3. Actualizar `.env` con la nueva clave
4. Reiniciar la aplicación

## Migraciones de Prueba

Para verificar que las migraciones funcionan correctamente con SQLCipher:

```bash
# Crear BD de prueba temporal con cifrado
python -c "
import tempfile
import os
from sqlmodel import create_engine, Session, SQLModel
from app.database import _configure_sqlite_encryption
from sqlalchemy import event

with tempfile.TemporaryDirectory() as tmpdir:
    db_path = os.path.join(tmpdir, 'test.db')
    db_url = f'sqlite:///{db_path}'

    # Crear engine con cifrado
    engine = create_engine(db_url, connect_args={'check_same_thread': False})
    event.listen(engine, 'connect', _configure_sqlite_encryption)

    # Crear tablas
    SQLModel.metadata.create_all(engine)

    # Insertar datos
    from app.models import User, UserRole
    user = User(
        username='test',
        email='test@example.com',
        hashed_password='hash',
        role=UserRole.user,
        full_name='Test User'
    )

    with Session(engine) as session:
        session.add(user)
        session.commit()

    print('✅ Migrations work with SQLCipher!')
"
```

## Debugging

Si Alembic tiene problemas con SQLCipher:

1. Verificar que `DB_ENCRYPTION_KEY` está correctamente seteada:
   ```bash
   echo $DB_ENCRYPTION_KEY
   ```

2. Verificar que pysqlcipher3 está instalado:
   ```bash
   poetry show pysqlcipher3
   ```

3. Verificar logs de aplicación:
   ```bash
   grep "database_encryption" logs/*.log
   ```

4. Ejecutar test de cifrado:
   ```bash
   poetry run pytest tests/test_encryption_story_5_3.py::TestSQLCipherConfiguration -v
   ```

## Referencias

- SQLCipher Docs: https://www.zetetic.net/sqlcipher/documentation/
- Alembic Docs: https://alembic.sqlalchemy.org/
- Story 5.3: Cifrado de Datos en Reposo y en Tránsito
