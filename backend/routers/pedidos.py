"""CRUD de pedidos, con control de propietario y devolución de existencias."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Pedido, Producto
from backend.schemas.schemas import PedidoDatos
from backend.services.auth import usuario_actual
from backend.services.ventas import (
    pedidos_visibles,
    buscar_pedido,
    pagado,
    datos_pedido,
    modificar_pedido,
)

router = APIRouter(prefix="/api", tags=["Pedidos"])


@router.get("/pedidos")
def pedidos(
    estado: str = "", db: Session = Depends(get_db), user=Depends(usuario_actual)
):
    query = pedidos_visibles(db, user)
    if estado:
        query = query.filter(Pedido.estado == estado)
    return [datos_pedido(db, p) for p in query.order_by(Pedido.id_pedido.desc())]


@router.get("/pedidos/{id}")
def consultar_pedido(
    id: int, db: Session = Depends(get_db), user=Depends(usuario_actual)
):
    return datos_pedido(db, buscar_pedido(db, id, user), detalle=True)


@router.post("/pedidos", status_code=201)
def crear_pedido(
    data: PedidoDatos, db: Session = Depends(get_db), user=Depends(usuario_actual)
):
    row = Pedido(estado="PENDIENTE")
    modificar_pedido(db, row, data, user)
    db.add(row)
    db.commit()
    return datos_pedido(db, row, detalle=True)


@router.put("/pedidos/{id}")
def editar_pedido(
    id: int,
    data: PedidoDatos,
    db: Session = Depends(get_db),
    user=Depends(usuario_actual),
):
    row = buscar_pedido(db, id, user, bloquear=True)
    modificar_pedido(db, row, data, user)
    db.commit()
    return datos_pedido(db, row, detalle=True)


@router.delete("/pedidos/{id}")
def cancelar_pedido(
    id: int, db: Session = Depends(get_db), user=Depends(usuario_actual)
):
    row = buscar_pedido(db, id, user, bloquear=True)
    if row.estado == "CANCELADO":
        return {"mensaje": "El pedido ya estaba cancelado"}
    if pagado(db, id) > 0:
        raise HTTPException(400, "Primero un administrador debe anular los pagos")
    for detail in sorted(row.detalles, key=lambda d: d.id_producto):
        producto = (
            db.query(Producto)
            .filter(Producto.id_producto == detail.id_producto)
            .with_for_update()
            .one()
        )
        producto.stock_actual += detail.cantidad
    row.estado = "CANCELADO"
    db.commit()
    return {"mensaje": "Pedido cancelado y existencias devueltas"}
