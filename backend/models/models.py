"""Las siete tablas del sistema, con los mismos nombres que PostgreSQL."""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    ForeignKey,
    DateTime,
    SmallInteger,
)
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class Rol(Base):
    __tablename__ = "roles"
    id_rol = Column(Integer, primary_key=True)
    nombre = Column(String(30), unique=True, nullable=False)
    descripcion = Column(String(150), nullable=False)


class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True)
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(120), unique=True, nullable=False)
    telefono = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    activo = Column(SmallInteger, default=1, nullable=False)
    creado_en = Column(DateTime, default=datetime.now, nullable=False)
    rol = relationship("Rol")


class Categoria(Base):
    __tablename__ = "categorias"
    id_categoria = Column(Integer, primary_key=True)
    nombre = Column(String(80), unique=True, nullable=False)
    descripcion = Column(String(200))
    estado = Column(String(15), default="ACTIVO", nullable=False)


class Producto(Base):
    __tablename__ = "productos"
    id_producto = Column(Integer, primary_key=True)
    id_categoria = Column(
        Integer, ForeignKey("categorias.id_categoria"), nullable=False
    )
    codigo = Column(String(30), unique=True, nullable=False)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(String(250))
    precio_base = Column(Numeric(12, 2), nullable=False)
    precio_reventa_sugerido = Column(Numeric(12, 2), nullable=False)
    stock_actual = Column(Integer, default=0, nullable=False)
    stock_minimo = Column(Integer, default=5, nullable=False)
    estado = Column(String(15), default="ACTIVO", nullable=False)
    categoria = relationship("Categoria")


class Pedido(Base):
    __tablename__ = "pedidos"
    id_pedido = Column(Integer, primary_key=True)
    id_revendedor = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_vendedor = Column(Integer, ForeignKey("usuarios.id_usuario"))
    fecha_pedido = Column(DateTime, default=datetime.now, nullable=False)
    estado = Column(String(20), default="PENDIENTE", nullable=False)
    subtotal = Column(Numeric(12, 2), default=0, nullable=False)
    descuento_porcentaje = Column(Numeric(5, 2), default=0, nullable=False)
    descuento_monto = Column(Numeric(12, 2), default=0, nullable=False)
    total = Column(Numeric(12, 2), default=0, nullable=False)
    observaciones = Column(String(250))
    revendedor = relationship("Usuario", foreign_keys=[id_revendedor])
    detalles = relationship("DetallePedido", cascade="all, delete-orphan")


class DetallePedido(Base):
    __tablename__ = "detalle_pedido"
    id_detalle = Column(Integer, primary_key=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido"), nullable=False)
    id_producto = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    producto = relationship("Producto")


class Pago(Base):
    __tablename__ = "pagos"
    id_pago = Column(Integer, primary_key=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido"), nullable=False)
    fecha_pago = Column(DateTime, default=datetime.now, nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    metodo_pago = Column(String(30), nullable=False)
    referencia_transaccion = Column(String(60))
    estado_pago = Column(String(20), default="CONFIRMADO", nullable=False)
    registrado_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
