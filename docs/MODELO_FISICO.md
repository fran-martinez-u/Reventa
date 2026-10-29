# Modelo físico

Motor: PostgreSQL. El script completo está en `database/01_tables.sql`.

- Identificadores: SERIAL/INTEGER con PRIMARY KEY.
- Relaciones: FOREIGN KEY hacia las tablas maestras.
- Dinero: NUMERIC(12,2), calculado con Decimal en Python.
- Textos: VARCHAR con límites de cada formulario.
- Fechas: TIMESTAMP con valor inicial CURRENT_TIMESTAMP.
- Valores únicos: nombre del rol, correo, nombre de categoría y código de producto.
- Las restricciones CHECK del script controlan estados, cantidades y precios.

La base existente se conserva sin migraciones automáticas. `database/02_constraints.sql` permite consultar qué restricciones están instaladas realmente. Las validaciones de la API se aplican también a la base existente.
