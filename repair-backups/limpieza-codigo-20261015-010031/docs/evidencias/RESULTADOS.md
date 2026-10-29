# Verificación del 15 de octubre de 2026

- 11 pruebas automatizadas aprobadas con `python -m unittest discover -s tests -v`.
- Cobertura: acceso/cierre de sesión, protección de rutas, CRUD de los cinco módulos, búsquedas, filtros, cantidades y precios inválidos, duplicados, permisos por rol y propietario, stock, cancelaciones, saldo, pagos y reportes.
- Base de pruebas: SQLite temporal; no se escribieron pedidos ni pagos de prueba en Neon.
- Sintaxis JavaScript: api.js, login.js y app.js comprobados con Node.
- Comprobación real en navegador: inicio con una cuenta existente, indicadores del resumen, listado y búsqueda de productos, apertura del formulario con datos del producto.
- Reporte real de ventas por revendedor consultado. Vista móvil de 390 × 844 revisada: controles y tabla de ventas visibles; menú con desplazamiento horizontal.
- La conexión real continúa en PostgreSQL (Neon). No se ejecutaron scripts de creación ni se reemplazaron tablas.

Los integrantes deben completar la demostración manual de `docs/PRUEBAS.md` y guardar sus propias capturas para la entrega. Estas pruebas no acreditan aportes de integrantes ni una publicación en GitHub.
