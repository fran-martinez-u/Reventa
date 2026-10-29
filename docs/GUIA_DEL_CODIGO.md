# Cómo está organizado el código

La aplicación usa funciones, formularios HTML, consultas SQLAlchemy y peticiones fetch. No requiere un framework de JavaScript ni un proceso de compilación.

## Backend

| Archivo | Responsabilidad |
|---|---|
| backend/main.py | Cargar las rutas, servir HTML y manejar errores |
| backend/database/connection.py | Leer .env y abrir/cerrar la sesión de base de datos |
| backend/models/models.py | Definir las siete tablas y sus relaciones |
| backend/schemas/schemas.py | Validar los datos recibidos |
| backend/routers/auth.py | Entrar, salir y consultar la sesión |
| backend/routers/usuarios.py | CRUD de usuarios y consultas de roles |
| backend/routers/categorias.py | CRUD de categorías |
| backend/routers/productos.py | CRUD de productos y filtros |
| backend/routers/pedidos.py | CRUD de pedidos |
| backend/routers/pagos.py | CRUD de pagos |
| backend/routers/reportes.py | Indicadores y consultas consolidadas |
| backend/services/auth.py | Contraseñas, sesiones y permisos |
| backend/services/catalogo.py | Buscar un registro y preparar sus datos |
| backend/services/ventas.py | Reglas de stock, pedidos y saldo |

Cada operación tiene una función con su decorador GET, POST, PUT o DELETE. Las rutas comprueban permisos, reciben un esquema validado y consultan la base. Las reglas compartidas de stock y pagos están en services para no repetirlas.

## Frontend

| Archivo | Responsabilidad |
|---|---|
| frontend/js/api.js | Peticiones fetch, token y formato de valores |
| frontend/js/login.js | Enviar el formulario de acceso |
| frontend/js/modulos.js | Nombres, columnas y campos de los cinco módulos |
| frontend/js/vistas.js | Mostrar tablas, filtros, resumen y reportes |
| frontend/js/formularios.js | Preparar controles y cargar datos para editar |
| frontend/js/app.js | Iniciar la página, cambiar de módulo, guardar y eliminar |

Los archivos se cargan con scripts defer en index.html, en el orden indicado. Se utilizan funciones normales compartidas entre esos archivos. No hay módulos npm ni bibliotecas nuevas en la interfaz.

## Ejemplo: editar un producto

1. El botón Editar llama a openEditor en formularios.js.
2. api.js consulta GET /api/productos/{id} y llena el formulario.
3. Guardar llama a saveForm en app.js, que envía PUT /api/productos/{id}.
4. La ruta en productos.py comprueba que el usuario sea administrador.
5. ProductoDatos valida el formulario y SQLAlchemy actualiza el producto.
6. El navegador vuelve a consultar la tabla y muestra el mensaje de éxito.

## Pruebas

tests/test_app.py utiliza unittest y TestClient de FastAPI. Cada prueba crea datos en SQLite temporal, envía peticiones a la API y comprueba resultados. No necesita construir manualmente el protocolo HTTP ni conectarse a Neon.

Instalar las dependencias de pruebas con `python -m pip install -r backend/requirements-dev.txt` y ejecutar `python -m unittest discover -s tests -v`.
