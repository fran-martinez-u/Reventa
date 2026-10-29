"""Reglas básicas de pedidos, existencias y pagos."""
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import func
from backend.models.models import Pedido, Producto, DetallePedido, Pago, Usuario


def pedidos_visibles(db, user):
    query = db.query(Pedido)
    if user.rol.nombre == 'REVENDEDOR':
        query = query.filter(Pedido.id_revendedor == user.id_usuario)
    return query


def buscar_pedido(db, id, user, bloquear=False):
    query = pedidos_visibles(db, user).filter(Pedido.id_pedido == id)
    if bloquear:
        query = query.with_for_update()
    row = query.first()
    if not row:
        raise HTTPException(404, 'Pedido no encontrado')
    return row


def pagado(db, id, excluir=None):
    query = db.query(func.coalesce(func.sum(Pago.monto), 0)).filter(
        Pago.id_pedido == id, Pago.estado_pago == 'CONFIRMADO')
    if excluir:
        query = query.filter(Pago.id_pago != excluir)
    return query.scalar()


def datos_pedido(db, row, detalle=False):
    total_pagado = pagado(db, row.id_pedido)
    result = {'id_pedido': row.id_pedido, 'id_revendedor': row.id_revendedor,
              'revendedor': row.revendedor.nombre, 'fecha_pedido': row.fecha_pedido,
              'estado': row.estado, 'total': row.total, 'total_pagado': total_pagado,
              'saldo': row.total - total_pagado, 'observaciones': row.observaciones or ''}
    if detalle:
        result['items'] = [{'id_producto': d.id_producto, 'producto': d.producto.nombre,
                            'cantidad': d.cantidad, 'precio_unitario': d.precio_unitario,
                            'subtotal': d.subtotal} for d in row.detalles]
    return result


def modificar_pedido(db, row, data, user):
    if row.id_pedido and (row.estado != 'PENDIENTE' or pagado(db, row.id_pedido) > 0):
        raise HTTPException(400, 'Solo se puede editar un pedido pendiente sin pagos')
    id_revendedor = user.id_usuario if user.rol.nombre == 'REVENDEDOR' else data.id_revendedor
    revendedor = db.get(Usuario, id_revendedor) if id_revendedor else None
    if not revendedor or not revendedor.activo or revendedor.rol.nombre != 'REVENDEDOR':
        raise HTTPException(400, 'Selecciona un revendedor activo')
    # Se bloquean en orden para que dos ventas no reserven el mismo stock.
    anteriores = {d.id_producto: d.cantidad for d in row.detalles}
    ids = sorted(set(anteriores) | {i.id_producto for i in data.items})
    productos = {p.id_producto: p for p in db.query(Producto).filter(
        Producto.id_producto.in_(ids)).order_by(Producto.id_producto).with_for_update()}
    for id, cantidad in anteriores.items():
        productos[id].stock_actual += cantidad
    row.detalles.clear()
    total = Decimal('0.00')
    for item in data.items:
        producto = productos.get(item.id_producto)
        if not producto or producto.estado != 'ACTIVO' or producto.categoria.estado != 'ACTIVO':
            raise HTTPException(400, 'Selecciona productos activos de una categoría activa')
        if producto.stock_actual < item.cantidad:
            raise HTTPException(400, f'Stock insuficiente: {producto.nombre}')
        producto.stock_actual -= item.cantidad
        subtotal = producto.precio_base * item.cantidad
        row.detalles.append(DetallePedido(id_producto=producto.id_producto, cantidad=item.cantidad,
                                         precio_unitario=producto.precio_base, subtotal=subtotal))
        total += subtotal
    if total > Decimal('9999999999.99'):
        raise HTTPException(400, 'El total supera el importe permitido por pedido')
    row.id_revendedor = id_revendedor
    if user.rol.nombre in ('ADMIN', 'VENDEDOR'):
        row.id_vendedor = user.id_usuario
    row.observaciones = data.observaciones
    row.subtotal = total
    row.descuento_porcentaje = 0
    row.descuento_monto = 0
    row.total = total


def datos_pago(row):
    return {'id_pago': row.id_pago, 'id_pedido': row.id_pedido, 'fecha_pago': row.fecha_pago,
            'monto': row.monto, 'metodo_pago': row.metodo_pago,
            'referencia_transaccion': row.referencia_transaccion or '', 'estado_pago': row.estado_pago}


def revisar_pago(db, pedido, monto, excluir=None):
    if pedido.estado == 'CANCELADO':
        raise HTTPException(400, 'No se puede pagar un pedido cancelado')
    if monto + pagado(db, pedido.id_pedido, excluir) > pedido.total:
        raise HTTPException(400, 'El pago supera el saldo pendiente')


def actualizar_estado(db, pedido):
    db.flush()
    pedido.estado = 'CONFIRMADO' if pagado(db, pedido.id_pedido) >= pedido.total else 'PENDIENTE'
