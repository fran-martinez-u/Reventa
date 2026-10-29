# Modelo lógico

| Tabla | Clave primaria | Claves foráneas | Información principal |
|---|---|---|---|
| roles | id_rol | — | nombre, descripcion |
| usuarios | id_usuario | id_rol → roles | nombre, correo único, hash de contraseña, activo |
| categorias | id_categoria | — | nombre único, descripción, estado |
| productos | id_producto | id_categoria → categorias | código único, precios, stock, estado |
| pedidos | id_pedido | id_revendedor e id_vendedor → usuarios | fecha, estado, total, observaciones |
| detalle_pedido | id_detalle | id_pedido → pedidos; id_producto → productos | cantidad, precio unitario, subtotal |
| pagos | id_pago | id_pedido → pedidos; registrado_por → usuarios | monto, método, referencia, estado |

Los detalles evitan repetir columnas de productos en pedidos. Los roles y categorías son catálogos separados. Se guarda el precio unitario de la venta para que el historial no cambie al modificar el catálogo.
