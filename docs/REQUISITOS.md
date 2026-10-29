# Alcance del proyecto

Problema: un negocio necesita organizar su catálogo, registrar ventas por revendedor y controlar existencias y abonos.

Arquitectura: navegador → fetch → API FastAPI → SQLAlchemy → PostgreSQL (Neon). El frontend no accede directamente a la base. La elección de PostgreSQL sigue la autorización del profesor comunicada por el estudiante.

| Requisito | Implementación |
|---|---|
| Autenticación y roles | Acceso por correo; ADMIN, VENDEDOR, REVENDEDOR; permisos comprobados en la API |
| Cinco módulos | Categorías, productos, usuarios, pedidos y pagos |
| Seis tablas o más | Siete: roles, usuarios, categorias, productos, pedidos, detalle_pedido, pagos |
| CRUD principales | GET lista/detalle, POST, PUT, DELETE lógico en los cinco módulos |
| Búsqueda y filtros | Catálogo y usuarios por texto; productos/pedidos por estado; pagos por pedido |
| Formularios validados | Campos obligatorios, tamaños, correo, números positivos, stock, saldo y relaciones |
| Dashboard | Indicadores de ventas, pagos, saldo, pedidos e inventario |
| Reportes | Ventas agrupadas por revendedor y valor del inventario |
| API documentada | Swagger /docs y OpenAPI /openapi.json |
| Errores claros | 400, 401, 403, 404, 409, 422, 503; sin detalles internos de conexión |
| Persistencia | PostgreSQL existente; scripts reproducibles para una base nueva |

Reglas: el precio de venta del pedido es el precio base del producto. No se aplican descuentos automáticos. El precio sugerido es una referencia de reventa. Los campos históricos de descuento de la base se conservan por compatibilidad, con cero en los pedidos nuevos.

Fuera del alcance: pasarela de pagos, facturación electrónica, registro público y recuperación de claves por correo. Los pagos son registros del negocio; no mueven dinero.

Pendiente de los estudiantes: completar autores y aportes, subir los cambios a GitHub, capturar la demostración en la base real y explicar el código. No se atribuyen evidencias ni contribuciones no realizadas.
