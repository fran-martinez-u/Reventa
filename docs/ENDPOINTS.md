# API REST

Swagger: `/docs`. OpenAPI: `/openapi.json`.

1. Ejecutar POST `/api/auth/login` con `correo` y `contrasena`.
2. Copiar `access_token` y enviarlo en el encabezado `Authorization: Bearer TOKEN`.
3. En Swagger agregar ese encabezado al campo authorization de cada operación protegida.

| Recurso | Lista y creación | Detalle, edición y eliminación |
|---|---|---|
| Categorías | GET/POST /api/categorias | GET/PUT/DELETE /api/categorias/{id} |
| Productos | GET/POST /api/productos | GET/PUT/DELETE /api/productos/{id} |
| Usuarios | GET/POST /api/auth/usuarios | GET/PUT/DELETE /api/auth/usuarios/{id_usuario} |
| Pedidos | GET/POST /api/pedidos | GET/PUT/DELETE /api/pedidos/{id} |
| Pagos | GET/POST /api/pagos | GET/PUT/DELETE /api/pagos/{id} |

Otros: GET `/api/auth/me`, GET `/api/auth/roles`, GET `/api/auth/revendedores`, POST `/api/auth/logout`, GET `/api/reportes/dashboard`, GET `/api/reportes/ventas-revendedor`, GET `/api/reportes/inventario`.

Filtros: `q` en categorías, productos y usuarios; `estado` en productos y pedidos; `id_categoria` en productos; `id_pedido` en pagos.

POST devuelve 201. GET/PUT/DELETE devuelven 200. Datos incorrectos: 400 o 422. Sin sesión: 401. Sin permiso: 403. Registro inexistente o ajeno: 404. Duplicado/relación no válida: 409. Base no disponible: 503.

Los DELETE conservan el registro: desactivan, cancelan o anulan. Ver las reglas y permisos en README.md.
