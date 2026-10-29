from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Producto, Pedido, Pago, Usuario
from backend.services.auth import usuario_actual
from backend.services.ventas import pedidos_visibles

router = APIRouter(prefix='/api/reportes', tags=['Resumen y reportes'])


@router.get('/dashboard')
def dashboard(db: Session = Depends(get_db), user=Depends(usuario_actual)):
    pedidos = pedidos_visibles(db, user).filter(Pedido.estado != 'CANCELADO')
    ventas = pedidos.with_entities(func.coalesce(func.sum(Pedido.total), 0)).scalar()
    pagos = db.query(func.coalesce(func.sum(Pago.monto), 0)).join(Pedido).filter(Pago.estado_pago == 'CONFIRMADO')
    if user.rol.nombre == 'REVENDEDOR':
        pagos = pagos.filter(Pedido.id_revendedor == user.id_usuario)
    recaudado = pagos.scalar()
    return {'productos_activos': db.query(Producto).filter(Producto.estado == 'ACTIVO').count(),
            'stock_bajo': db.query(Producto).filter(Producto.estado == 'ACTIVO', Producto.stock_actual <= Producto.stock_minimo).count(),
            'pedidos_pendientes': pedidos.filter(Pedido.estado == 'PENDIENTE').count(),
            'ventas': ventas, 'recaudado': recaudado, 'saldo': ventas - recaudado}


@router.get('/ventas-revendedor')
def ventas_revendedor(db: Session = Depends(get_db), user=Depends(usuario_actual)):
    query = db.query(Usuario.nombre, func.count(Pedido.id_pedido), func.sum(Pedido.total)).join(
        Pedido, Pedido.id_revendedor == Usuario.id_usuario).filter(Pedido.estado != 'CANCELADO')
    if user.rol.nombre == 'REVENDEDOR':
        query = query.filter(Usuario.id_usuario == user.id_usuario)
    return [{'revendedor': nombre, 'pedidos': cantidad, 'ventas': total}
            for nombre, cantidad, total in query.group_by(Usuario.id_usuario, Usuario.nombre).order_by(Usuario.nombre)]


@router.get('/inventario')
def inventario(db: Session = Depends(get_db), user=Depends(usuario_actual)):
    return [{'codigo': p.codigo, 'producto': p.nombre, 'stock': p.stock_actual,
             'minimo': p.stock_minimo, 'valor_inventario': p.precio_base * p.stock_actual,
             'nivel': 'BAJO' if p.stock_actual <= p.stock_minimo else 'NORMAL'}
            for p in db.query(Producto).filter(Producto.estado == 'ACTIVO').order_by(Producto.nombre)]
