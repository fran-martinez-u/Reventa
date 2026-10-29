-- Búsqueda de productos.
SELECT codigo, nombre, precio_base, stock_actual FROM productos
WHERE nombre ILIKE '%camiseta%' AND estado = 'ACTIVO';

-- Ventas por revendedor, excluyendo pedidos cancelados.
SELECT u.nombre AS revendedor, COUNT(p.id_pedido) AS pedidos, SUM(p.total) AS ventas
FROM usuarios u JOIN pedidos p ON p.id_revendedor = u.id_usuario
WHERE p.estado <> 'CANCELADO'
GROUP BY u.id_usuario, u.nombre ORDER BY u.nombre;

-- Inventario y alertas.
SELECT codigo, nombre, stock_actual, stock_minimo,
       precio_base * stock_actual AS valor_inventario,
       CASE WHEN stock_actual <= stock_minimo THEN 'BAJO' ELSE 'NORMAL' END AS nivel
FROM productos WHERE estado = 'ACTIVO' ORDER BY nombre;

-- Saldo de cada pedido.
SELECT p.id_pedido, p.total,
       COALESCE(SUM(pa.monto) FILTER (WHERE pa.estado_pago='CONFIRMADO'), 0) AS pagado,
       p.total - COALESCE(SUM(pa.monto) FILTER (WHERE pa.estado_pago='CONFIRMADO'),0) AS saldo
FROM pedidos p LEFT JOIN pagos pa ON pa.id_pedido = p.id_pedido
WHERE p.estado <> 'CANCELADO' GROUP BY p.id_pedido;
