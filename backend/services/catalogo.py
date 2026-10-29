"""Consulta de registros y datos que se envían al navegador."""

from fastapi import HTTPException


def buscar(db, modelo, id_registro):
    registro = db.get(modelo, id_registro)
    if registro is None:
        raise HTTPException(404, "Registro no encontrado")
    return registro


def datos_categoria(categoria):
    return {
        "id_categoria": categoria.id_categoria,
        "nombre": categoria.nombre,
        "descripcion": categoria.descripcion,
        "estado": categoria.estado,
    }


def datos_producto(producto):
    return {
        "id_producto": producto.id_producto,
        "id_categoria": producto.id_categoria,
        "categoria": producto.categoria.nombre,
        "codigo": producto.codigo,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion,
        "precio_base": producto.precio_base,
        "precio_reventa_sugerido": producto.precio_reventa_sugerido,
        "stock_actual": producto.stock_actual,
        "stock_minimo": producto.stock_minimo,
        "estado": producto.estado,
    }
