-- Las PK, FK, UNIQUE, NOT NULL y CHECK están declaradas en 01_tables.sql.
-- Esta consulta permite demostrar las restricciones de la base conectada.
SELECT conrelid::regclass AS tabla, conname AS restriccion,
       pg_get_constraintdef(oid) AS definicion
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
ORDER BY tabla, restriccion;

-- La aplicación también valida cantidades, precios, saldo y permisos.
-- La base Neon existente se conserva: este archivo no altera sus tablas.
