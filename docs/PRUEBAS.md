# Pruebas

Ejecutar desde la raíz:

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m unittest discover -s tests -v
```

Las pruebas usan TestClient de FastAPI y SQLite temporal. No escriben en Neon. Cubren login, permisos, CRUD, filtros, validaciones, stock, pagos y reportes. Ver los nombres de casos en `tests/test_app.py`.

## Demostración manual con la base real

1. Ingresar como administrador y ver el resumen.
2. Crear, consultar, buscar, editar y desactivar una categoría y un producto de demostración.
3. Crear un vendedor y un revendedor. Editar y desactivar una cuenta de demostración.
4. Entrar como vendedor y comprobar que no puede administrar catálogo ni usuarios.
5. Crear un pedido con varias unidades; comprobar que disminuye el stock.
6. Editar un pedido pendiente sin pagos y comprobar el nuevo total/stock.
7. Registrar un pago parcial, comprobar saldo y probar un importe superior al saldo.
8. Como administrador editar y anular el pago; cancelar el pedido y comprobar que vuelve el stock.
9. Como revendedor verificar que solo ve sus pedidos y pagos; un ID ajeno devuelve 404.
10. Buscar productos y categorías, filtrar pedidos y consultar ambos reportes.
11. Probar campos vacíos, correo inválido, precios negativos, cantidades cero y duplicados.
12. Revisar móvil, cerrar sesión y verificar que no se puede seguir consultando con ese token.

Guardar capturas y resultados propios con fecha en `docs/evidencias/`. Los datos de demostración se crean conscientemente; los DELETE conservan el historial. Las pruebas antiguas de otra versión se guardan en el respaldo y no cuentan como evidencia de esta versión.
