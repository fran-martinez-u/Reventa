# Reventa

Proyecto integrador para gestionar un pequeño negocio de reventa. Usa **HTML, CSS, JavaScript, Bootstrap, FastAPI y PostgreSQL (Neon)**. PostgreSQL se conserva según la autorización del profesor comunicada por el estudiante.

## Ejecutar en Windows

Desde la carpeta del proyecto en la terminal de Visual Studio Code:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
```

Completar `DATABASE_URL` en `.env` con la conexión privada. Si `.env` ya existe, conservarlo: no volver a copiar el ejemplo encima. Las credenciales no se suben a GitHub.

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

- Aplicación: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Pruebas: `python -m unittest discover -s tests -v`

La base existente ya contiene datos y cuentas. **No ejecutar los scripts de creación sobre ella.** Para reproducir en una base nueva, ejecutar `database/01_tables.sql` y `database/03_data.sql`, y crear el primer administrador con `python -m backend.create_admin`. Crear los demás usuarios desde la aplicación.

## Funciones

- Inicio y cierre de sesión.
- Cinco módulos con crear, consultar, editar y eliminar de forma lógica: categorías, productos, usuarios, pedidos y pagos.
- Búsqueda de categorías, productos y usuarios; filtros de estado de productos y pedidos, y de número de pedido en pagos.
- Resumen con indicadores desde el backend.
- Reportes de ventas por revendedor e inventario.
- Formularios con validación en navegador y servidor.

## Roles

| Acción | Administrador | Vendedor | Revendedor |
|---|---|---|---|
| Consultar catálogo | Sí | Sí | Sí |
| Crear/editar/desactivar catálogo y usuarios | Sí | No | No |
| Crear/editar/cancelar pedidos pendientes sin pagos | Todos | Todos | Propios |
| Consultar pedidos, pagos y ventas | Todos | Todos | Propios |
| Registrar pagos | Sí | Sí | No |
| Editar/anular pagos | Sí | No | No |

Eliminar categorías, productos o usuarios cambia su estado. Eliminar pedidos los cancela y devuelve stock; eliminar pagos los anula. Así se conservan las relaciones y el historial. Un pedido con pagos requiere anularlos antes de editarlo o cancelarlo.

## Organización

```text
backend/main.py             Inicio y manejo de errores
backend/routers/            Rutas de acceso, catálogo, ventas y reportes
backend/services/           Autenticación y reglas de pedidos/pagos
backend/models/             Siete tablas con SQLAlchemy
backend/schemas/            Validaciones con Pydantic
backend/database/           Conexión por variable de entorno
frontend/                   HTML, Bootstrap, estilos y JavaScript
database/                   Tablas, restricciones, datos y consultas SQL
docs/                       Modelos, requisitos, pruebas y sustentación
tests/                      Pruebas HTTP con base temporal SQLite
```

La sesión dura ocho horas y se guarda en memoria del servidor; al reiniciarlo hay que volver a ingresar. Esta solución sencilla usa un solo proceso del servidor. Las contraseñas nuevas se guardan con PBKDF2; los hashes anteriores se actualizan al iniciar sesión, conservando la contraseña. El sistema no crea ni borra tablas al arrancar.

## Entrega académica

Consultar `docs/REQUISITOS.md`, completar `docs/INTEGRANTES.md`, registrar aportes reales en GitHub y guardar las evidencias de la demostración. Las pruebas con SQLite verifican la aplicación, pero no sustituyen la demostración con PostgreSQL.
