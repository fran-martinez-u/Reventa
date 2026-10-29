-- PostgreSQL. Ejecutar solamente en una base nueva y vacía.
-- No se ejecuta automáticamente al iniciar la aplicación.
BEGIN;
CREATE TABLE roles (
  id_rol SERIAL PRIMARY KEY,
  nombre VARCHAR(30) NOT NULL UNIQUE,
  descripcion VARCHAR(150) NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE usuarios (
  id_usuario SERIAL PRIMARY KEY,
  id_rol INTEGER NOT NULL REFERENCES roles(id_rol),
  nombre VARCHAR(100) NOT NULL,
  correo VARCHAR(120) NOT NULL UNIQUE,
  telefono VARCHAR(20),
  password_hash VARCHAR(255) NOT NULL,
  activo SMALLINT NOT NULL DEFAULT 1 CHECK (activo IN (0,1)),
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE categorias (
  id_categoria SERIAL PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL UNIQUE,
  descripcion VARCHAR(200),
  estado VARCHAR(15) NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO','INACTIVO')),
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE productos (
  id_producto SERIAL PRIMARY KEY,
  id_categoria INTEGER NOT NULL REFERENCES categorias(id_categoria),
  codigo VARCHAR(30) NOT NULL UNIQUE,
  nombre VARCHAR(120) NOT NULL,
  descripcion VARCHAR(250),
  precio_base NUMERIC(12,2) NOT NULL CHECK (precio_base > 0),
  precio_reventa_sugerido NUMERIC(12,2) NOT NULL CHECK (precio_reventa_sugerido > 0),
  stock_actual INTEGER NOT NULL DEFAULT 0 CHECK (stock_actual >= 0),
  stock_minimo INTEGER NOT NULL DEFAULT 5 CHECK (stock_minimo >= 0),
  estado VARCHAR(15) NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO','INACTIVO')),
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pedidos (
  id_pedido SERIAL PRIMARY KEY,
  id_revendedor INTEGER NOT NULL REFERENCES usuarios(id_usuario),
  id_vendedor INTEGER REFERENCES usuarios(id_usuario),
  fecha_pedido TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE','CONFIRMADO','CANCELADO')),
  subtotal NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
  descuento_porcentaje NUMERIC(5,2) NOT NULL DEFAULT 0,
  descuento_monto NUMERIC(12,2) NOT NULL DEFAULT 0,
  total NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (total >= 0),
  observaciones VARCHAR(250)
);
CREATE TABLE detalle_pedido (
  id_detalle SERIAL PRIMARY KEY,
  id_pedido INTEGER NOT NULL REFERENCES pedidos(id_pedido) ON DELETE CASCADE,
  id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
  cantidad INTEGER NOT NULL CHECK (cantidad > 0),
  precio_unitario NUMERIC(12,2) NOT NULL CHECK (precio_unitario > 0),
  subtotal NUMERIC(12,2) NOT NULL CHECK (subtotal > 0)
);
CREATE TABLE pagos (
  id_pago SERIAL PRIMARY KEY,
  id_pedido INTEGER NOT NULL REFERENCES pedidos(id_pedido),
  fecha_pago TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  monto NUMERIC(12,2) NOT NULL CHECK (monto > 0),
  metodo_pago VARCHAR(30) NOT NULL CHECK (metodo_pago IN ('EFECTIVO','TRANSFERENCIA','TARJETA')),
  referencia_transaccion VARCHAR(60),
  estado_pago VARCHAR(20) NOT NULL DEFAULT 'CONFIRMADO' CHECK (estado_pago IN ('CONFIRMADO','ANULADO')),
  registrado_por INTEGER NOT NULL REFERENCES usuarios(id_usuario)
);
COMMIT;
