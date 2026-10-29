from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Pedido, Producto, Pago
from backend.schemas.schemas import PedidoDatos, PagoDatos
from backend.services.auth import usuario_actual, personal, administrador
from backend.services.ventas import (
    pedidos_visibles, buscar_pedido, pagado, datos_pedido, modificar_pedido,
    datos_pago, revisar_pago, actualizar_estado,
)

router = APIRouter(prefix='/api', tags=['Pedidos y pagos'])


@router.get('/pedidos')
def pedidos(estado: str = '', db: Session = Depends(get_db), user=Depends(usuario_actual)):
    query = pedidos_visibles(db, user)
    if estado:
        query = query.filter(Pedido.estado == estado)
    return [datos_pedido(db, p) for p in query.order_by(Pedido.id_pedido.desc())]


@router.get('/pedidos/{id}')
def consultar_pedido(id: int, db: Session = Depends(get_db), user=Depends(usuario_actual)):
    return datos_pedido(db, buscar_pedido(db, id, user), detalle=True)


@router.post('/pedidos', status_code=201)
def crear_pedido(data: PedidoDatos, db: Session = Depends(get_db), user=Depends(usuario_actual)):
    row = Pedido(estado='PENDIENTE')
    modificar_pedido(db, row, data, user)
    db.add(row)
    db.commit()
    return datos_pedido(db, row, detalle=True)


@router.put('/pedidos/{id}')
def editar_pedido(id: int, data: PedidoDatos, db: Session = Depends(get_db), user=Depends(usuario_actual)):
    row = buscar_pedido(db, id, user, bloquear=True)
    modificar_pedido(db, row, data, user)
    db.commit()
    return datos_pedido(db, row, detalle=True)


@router.delete('/pedidos/{id}')
def cancelar_pedido(id: int, db: Session = Depends(get_db), user=Depends(usuario_actual)):
    row = buscar_pedido(db, id, user, bloquear=True)
    if row.estado == 'CANCELADO':
        return {'mensaje': 'El pedido ya estaba cancelado'}
    if pagado(db, id) > 0:
        raise HTTPException(400, 'Primero un administrador debe anular los pagos')
    for detail in sorted(row.detalles, key=lambda d: d.id_producto):
        producto = db.query(Producto).filter(Producto.id_producto == detail.id_producto).with_for_update().one()
        producto.stock_actual += detail.cantidad
    row.estado = 'CANCELADO'
    db.commit()
    return {'mensaje': 'Pedido cancelado y existencias devueltas'}


@router.get('/pagos')
def pagos(id_pedido: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), user=Depends(usuario_actual)):
    query = db.query(Pago).join(Pedido)
    if user.rol.nombre == 'REVENDEDOR':
        query = query.filter(Pedido.id_revendedor == user.id_usuario)
    if id_pedido:
        query = query.filter(Pago.id_pedido == id_pedido)
    return [datos_pago(p) for p in query.order_by(Pago.id_pago.desc())]


def buscar_pago(db, id, user):
    row = db.get(Pago, id)
    if not row:
        raise HTTPException(404, 'Pago no encontrado')
    buscar_pedido(db, row.id_pedido, user)
    return row


@router.get('/pagos/{id}')
def consultar_pago(id: int, db: Session = Depends(get_db), user=Depends(usuario_actual)):
    return datos_pago(buscar_pago(db, id, user))


@router.post('/pagos', status_code=201)
def crear_pago(data: PagoDatos, db: Session = Depends(get_db), user=Depends(personal)):
    pedido = buscar_pedido(db, data.id_pedido, user, bloquear=True)
    revisar_pago(db, pedido, data.monto)
    row = Pago(**data.model_dump(), registrado_por=user.id_usuario)
    db.add(row)
    actualizar_estado(db, pedido)
    db.commit()
    return datos_pago(row)


@router.put('/pagos/{id}')
def editar_pago(id: int, data: PagoDatos, db: Session = Depends(get_db), user=Depends(administrador)):
    row = buscar_pago(db, id, user)
    pedido = buscar_pedido(db, row.id_pedido, user, bloquear=True)
    db.refresh(row)
    if row.estado_pago != 'CONFIRMADO' or row.id_pedido != data.id_pedido:
        raise HTTPException(400, 'Un pago anulado o su pedido no se pueden cambiar')
    revisar_pago(db, pedido, data.monto, excluir=id)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    actualizar_estado(db, pedido)
    db.commit()
    return datos_pago(row)


@router.delete('/pagos/{id}')
def anular_pago(id: int, db: Session = Depends(get_db), user=Depends(administrador)):
    row = buscar_pago(db, id, user)
    pedido = buscar_pedido(db, row.id_pedido, user, bloquear=True)
    db.refresh(row)
    row.estado_pago = 'ANULADO'
    actualizar_estado(db, pedido)
    db.commit()
    return {'mensaje': 'Pago anulado'}
