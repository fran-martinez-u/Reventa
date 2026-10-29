"""Registro, consulta, edición y anulación de abonos a pedidos."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Pedido, Pago
from backend.schemas.schemas import PagoDatos
from backend.services.auth import usuario_actual, personal, administrador
from backend.services.ventas import (
    buscar_pedido,
    datos_pago,
    revisar_pago,
    actualizar_estado,
)

router = APIRouter(prefix="/api", tags=["Pagos"])


@router.get("/pagos")
def pagos(
    id_pedido: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    user=Depends(usuario_actual),
):
    query = db.query(Pago).join(Pedido)
    if user.rol.nombre == "REVENDEDOR":
        query = query.filter(Pedido.id_revendedor == user.id_usuario)
    if id_pedido:
        query = query.filter(Pago.id_pedido == id_pedido)
    return [datos_pago(p) for p in query.order_by(Pago.id_pago.desc())]


def buscar_pago(db, id, user):
    row = db.get(Pago, id)
    if not row:
        raise HTTPException(404, "Pago no encontrado")
    buscar_pedido(db, row.id_pedido, user)
    return row


@router.get("/pagos/{id}")
def consultar_pago(
    id: int, db: Session = Depends(get_db), user=Depends(usuario_actual)
):
    return datos_pago(buscar_pago(db, id, user))


@router.post("/pagos", status_code=201)
def crear_pago(data: PagoDatos, db: Session = Depends(get_db), user=Depends(personal)):
    pedido = buscar_pedido(db, data.id_pedido, user, bloquear=True)
    revisar_pago(db, pedido, data.monto)
    row = Pago(**data.model_dump(), registrado_por=user.id_usuario)
    db.add(row)
    actualizar_estado(db, pedido)
    db.commit()
    return datos_pago(row)


@router.put("/pagos/{id}")
def editar_pago(
    id: int, data: PagoDatos, db: Session = Depends(get_db), user=Depends(administrador)
):
    row = buscar_pago(db, id, user)
    pedido = buscar_pedido(db, row.id_pedido, user, bloquear=True)
    db.refresh(row)
    if row.estado_pago != "CONFIRMADO" or row.id_pedido != data.id_pedido:
        raise HTTPException(400, "Un pago anulado o su pedido no se pueden cambiar")
    revisar_pago(db, pedido, data.monto, excluir=id)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    actualizar_estado(db, pedido)
    db.commit()
    return datos_pago(row)


@router.delete("/pagos/{id}")
def anular_pago(id: int, db: Session = Depends(get_db), user=Depends(administrador)):
    row = buscar_pago(db, id, user)
    pedido = buscar_pedido(db, row.id_pedido, user, bloquear=True)
    db.refresh(row)
    row.estado_pago = "ANULADO"
    actualizar_estado(db, pedido)
    db.commit()
    return {"mensaje": "Pago anulado"}
