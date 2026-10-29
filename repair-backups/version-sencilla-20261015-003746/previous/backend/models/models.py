from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship, synonym
from datetime import datetime
from backend.database.connection import Base

class Rol(Base):
    __tablename__ = "roles"
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(40), unique=True, nullable=False)
    descripcion = Column(String(160))

class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)
    nombre_completo = Column("nombre", String(100), nullable=False)
    correo = Column(String(120), unique=True, nullable=False)
    telefono = Column(String(30))
    ciudad = ""
    username = synonym("correo")
    password_hash = Column(String(200), nullable=False)
    activo = Column(Integer, default=1)
    @property
    def estado(self):
        return "ACTIVO" if self.activo else "INACTIVO"
    @estado.setter
    def estado(self, value):
        self.activo = int(value == "ACTIVO")
    cupo_credito = 0.0
    fecha_creacion = Column("creado_en", DateTime, default=datetime.utcnow)

    rol = relationship("Rol")

class Categoria(Base):
    __tablename__ = "categorias"
    id_categoria = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), unique=True, nullable=False)
    descripcion = Column(String(200))
    estado = Column(String(15), default="ACTIVA")

class Producto(Base):
    __tablename__ = "productos"
    id_producto = Column(Integer, primary_key=True, index=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id_categoria"), nullable=False)
    sku = Column("codigo", String(40), unique=True, nullable=False)
    nombre = Column(String(120), nullable=False)
    talla = ""
    color = ""
    precio_base = Column(Float, nullable=False)
    precio_sugerido = Column("precio_reventa_sugerido", Float, nullable=False)
    stock_actual = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=5)
    estado = Column(String(15), default="ACTIVO")

    categoria = relationship("Categoria")

class Pedido(Base):
    __tablename__ = "pedidos"
    id_pedido = Column(Integer, primary_key=True, index=True)
    @property
    def codigo_pedido(self):
        return f"PED-{self.id_pedido}"
    @codigo_pedido.setter
    def codigo_pedido(self, value):
        pass
    id_revendedor = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    fecha_pedido = Column(DateTime, default=datetime.utcnow)
    tipo_pago = "CONTADO"
    estado_pedido = Column("estado", String(20), default="PENDIENTE")
    subtotal = Column(Float, default=0.0)
    descuento_pct = Column("descuento_porcentaje", Float, default=0.0)
    descuento_valor = Column("descuento_monto", Float, default=0.0)
    total = Column(Float, default=0.0)
    observacion = Column("observaciones", String(250))

    revendedor = relationship("Usuario")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")

class DetallePedido(Base):
    __tablename__ = "detalle_pedido"
    id_detalle = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido"), nullable=False)
    id_producto = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    subtotal_linea = Column("subtotal", Float, nullable=False)

    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto")

class Pago(Base):
    __tablename__ = "pagos"
    id_pago = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido"), nullable=False)
    fecha_pago = Column(DateTime, default=datetime.utcnow)
    monto = Column(Float, nullable=False)
    metodo_pago = Column(String(25), nullable=False)
    referencia = Column("referencia_transaccion", String(60))
    estado_pago = Column(String(15), default="CONFIRMADO")
    registrado_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    observacion = ""

