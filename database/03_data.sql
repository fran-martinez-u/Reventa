-- Datos iniciales para una base NUEVA, después de 01_tables.sql.
BEGIN;
INSERT INTO roles (nombre, descripcion) VALUES
('ADMIN', 'Administra catálogo, usuarios, pedidos y pagos'),
('VENDEDOR', 'Gestiona pedidos y registra pagos'),
('REVENDEDOR', 'Consulta catálogo y gestiona sus propios pedidos');
INSERT INTO categorias (nombre, descripcion) VALUES
('Camisetas', 'Camisetas y prendas básicas'), ('Calzado', 'Calzado casual');
INSERT INTO productos (id_categoria, codigo, nombre, descripcion, precio_base, precio_reventa_sugerido, stock_actual, stock_minimo)
VALUES ((SELECT id_categoria FROM categorias WHERE nombre='Camisetas'), 'CAM-001', 'Camiseta básica', 'Camiseta de algodón', 25000, 40000, 20, 5),
((SELECT id_categoria FROM categorias WHERE nombre='Calzado'), 'CAL-001', 'Tenis casuales', 'Calzado de uso diario', 80000, 120000, 10, 3);
COMMIT;
-- Crear el administrador con: python -m backend.create_admin
-- Después crear vendedor y revendedor desde Usuarios. No hay claves en este SQL.
